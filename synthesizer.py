import numpy as np
import random
import time
import audio_processing # For levels, panning, EQ, mastering

# --- Global Synthesizer Parameters ---
SAMPLE_RATE = 44100
DEFAULT_AMPLITUDE = 0.5 # Base amplitude before track-specific leveling

# --- Waveform Generators (Identical to previous version) ---
def midi_to_frequency(midi_note):
    if not (0 <= midi_note <= 127): return 0
    return 440.0 * (2.0**((midi_note - 69) / 12.0))

def pulse_wave(frequency, duration, duty_cycle=0.5, sample_rate=SAMPLE_RATE):
    if frequency == 0: return np.zeros(int(duration * sample_rate))
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    period = 1.0 / frequency
    wave = np.where( (t % period) < (period * duty_cycle), 1.0, -1.0)
    return wave.astype(np.float32)

def sawtooth_wave(frequency, duration, sample_rate=SAMPLE_RATE):
    if frequency == 0: return np.zeros(int(duration * sample_rate))
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    wave = 2.0 * (t * frequency - np.floor(0.5 + t * frequency))
    return wave.astype(np.float32)

def triangle_wave(frequency, duration, sample_rate=SAMPLE_RATE):
    if frequency == 0: return np.zeros(int(duration * sample_rate))
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    wave = 2.0 * np.abs(2.0 * (t * frequency - np.floor(t * frequency + 0.5))) - 1.0
    return wave.astype(np.float32)

def noise_wave(duration, noise_type="white", sample_rate=SAMPLE_RATE):
    num_samples = int(duration * sample_rate)
    if noise_type == "white" or noise_type =="pink": # Pink noise simplified to white for now
        wave = np.random.uniform(-1.0, 1.0, num_samples)
    else:
        wave = np.zeros(num_samples)
    return wave.astype(np.float32)

# --- ADSR Envelope (Identical to previous version) ---
def adsr_envelope(duration_samples, attack_time, decay_time, sustain_level, release_time, sample_rate=SAMPLE_RATE):
    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_samples = int(release_time * sample_rate)
    sustain_samples = duration_samples - attack_samples - decay_samples
    envelope = np.zeros(duration_samples + release_samples, dtype=np.float32)

    current_level_at_note_end = sustain_level # Default if note is long enough for full sustain phase
    if attack_samples > 0:
        end_attack = min(attack_samples, duration_samples)
        envelope[:end_attack] = np.linspace(0, 1, end_attack) if end_attack > 0 else []
        if duration_samples <= attack_samples: current_level_at_note_end = envelope[duration_samples-1] if duration_samples > 0 else 0

    if decay_samples > 0 and duration_samples > attack_samples:
        start_decay = attack_samples
        end_decay = min(duration_samples, start_decay + decay_samples)
        decay_actual_samples = end_decay - start_decay
        if decay_actual_samples > 0:
            envelope[start_decay:end_decay] = np.linspace(1, sustain_level, decay_actual_samples)
        if duration_samples <= (attack_samples + decay_samples) : current_level_at_note_end = envelope[duration_samples-1] if duration_samples > 0 else sustain_level

    if sustain_samples > 0:
        start_sustain = attack_samples + decay_samples
        end_sustain = start_sustain + sustain_samples
        envelope[start_sustain:end_sustain] = sustain_level
        current_level_at_note_end = sustain_level # Redundant if note is long enough

    if release_samples > 0:
        start_release = duration_samples
        end_release = duration_samples + release_samples
        # Level at release start depends on where the note_off occurred
        level_at_release_start = current_level_at_note_end
        envelope[start_release:end_release] = np.linspace(level_at_release_start, 0, release_samples)

    return envelope[:duration_samples + release_samples]


# --- Instrument Definitions (Mostly identical, filter_type might be used by EQ now) ---
INSTRUMENT_PARAMS = {
    "Melody":       {"waveform": "pulse", "duty_cycle": 0.5, "adsr": (0.01, 0.1, 0.7, 0.2), "octave_shift": 0},
    "Harmony Line": {"waveform": "sawtooth", "adsr": (0.02, 0.15, 0.6, 0.25), "octave_shift": 0},
    "Counter-Melody": {"waveform": "triangle", "adsr": (0.05, 0.2, 0.5, 0.3), "octave_shift": 0},
    "Bassline":     {"waveform": "pulse", "duty_cycle": 0.5, "adsr": (0.01, 0.05, 0.8, 0.15), "octave_shift": -1},
    "Pads":         {"waveform": "sawtooth", "adsr": (0.5, 0.5, 0.3, 1.0), "octave_shift": 0}, # HPF might apply from EQ
    "Drums_Kick":   {"waveform": "noise", "noise_type": "white", "adsr": (0.001, 0.1, 0, 0.05)}, # EQ will handle filtering
    "Drums_Snare":  {"waveform": "noise", "noise_type": "white", "adsr": (0.001, 0.15, 0, 0.1)},
    "Drums_Hat":    {"waveform": "noise", "noise_type": "white", "adsr": (0.001, 0.05, 0, 0.02)},
    "Drums_OpenHat":{"waveform": "noise", "noise_type": "white", "adsr": (0.001, 0.2, 0, 0.1)},
}


def render_midi_event_mono(event, instrument_name_full, bpm, sample_rate=SAMPLE_RATE):
    """
    Renders a single MIDIEvent to a MONO audio waveform, applying track level and EQ.
    instrument_name_full can be "Melody", "Drums_Kick", etc.
    Returns a tuple: (start_sample_index, mono_audio_data_array)
    """
    if event.type != 'note':
        return None, None

    params = INSTRUMENT_PARAMS.get(instrument_name_full)
    if not params: # Fallback for generic track name if specific drum name not found
        params = INSTRUMENT_PARAMS.get(instrument_name_full.split("_")[0] if "_" in instrument_name_full else "Default", INSTRUMENT_PARAMS["Melody"])


    note_duration_seconds = (event.duration / bpm) * 60.0
    attack_s, decay_s, sustain_l, release_s = params["adsr"]
    total_sounding_duration_seconds = note_duration_seconds + release_s
    total_samples = int(total_sounding_duration_seconds * sample_rate)
    if total_samples == 0: return int((event.time_start / bpm) * 60.0 * sample_rate), np.array([], dtype=np.float32)

    held_duration_samples = int(note_duration_seconds * sample_rate)
    wave_data = np.zeros(total_samples, dtype=np.float32)

    # Generate base waveform
    if "noise" in params["waveform"]:
        base_wave = noise_wave(total_sounding_duration_seconds, params.get("noise_type", "white"), sample_rate)
    else:
        frequency = midi_to_frequency(event.note + (params.get("octave_shift", 0) * 12))
        if frequency == 0: return int((event.time_start / bpm) * 60.0 * sample_rate), np.zeros(0, dtype=np.float32)
        waveform_type = params["waveform"]
        if waveform_type == "pulse": base_wave = pulse_wave(frequency, total_sounding_duration_seconds, params.get("duty_cycle", 0.5), sample_rate)
        elif waveform_type == "sawtooth": base_wave = sawtooth_wave(frequency, total_sounding_duration_seconds, sample_rate)
        elif waveform_type == "triangle": base_wave = triangle_wave(frequency, total_sounding_duration_seconds, sample_rate)
        else: base_wave = np.zeros(total_samples)

    env = adsr_envelope(held_duration_samples, attack_s, decay_s, sustain_l, release_s, sample_rate)
    if len(env) > len(base_wave): env = env[:len(base_wave)]
    wave_data[:len(env)] = base_wave[:len(env)] * env

    # Apply velocity
    normalized_velocity = (event.velocity / 127.0)
    wave_data *= (normalized_velocity**1.5)
    wave_data *= DEFAULT_AMPLITUDE

    # Apply track-specific gain (leveling)
    track_level = audio_processing.TRACK_LEVELS.get(instrument_name_full, audio_processing.TRACK_LEVELS["Default"])
    wave_data *= track_level

    # Apply track-specific EQ
    # EQ is applied to the mono signal before panning
    wave_data = audio_processing.apply_eq_track(wave_data, instrument_name_full, sample_rate)

    start_sample_offset = int((event.time_start / bpm) * 60.0 * sample_rate)
    return start_sample_offset, wave_data.astype(np.float32)


def render_song_to_stereo_mix(song_data, sample_rate=SAMPLE_RATE):
    """
    Renders a full Song object to a final STEREO audio mix,
    including leveling, EQ, panning, and mastering.
    """
    if not song_data: return np.array([[0,0]], dtype=np.float32) # Return stereo silence
    all_events = song_data.get_all_events()
    if not all_events: return np.array([[0,0]], dtype=np.float32)

    max_event_time_beats = 0
    for track_name_main, track_events in song_data.tracks.items():
        for event in track_events:
            # Determine full instrument name (e.g. Drums_Kick) for ADSR lookup
            instr_name_for_adsr = track_name_main
            if track_name_main == "Drums":
                if event.note == 60: instr_name_for_adsr = "Drums_Kick"
                elif event.note == 61: instr_name_for_adsr = "Drums_Snare"
                elif event.note == 62: instr_name_for_adsr = "Drums_Hat"
                elif event.note == 63: instr_name_for_adsr = "Drums_OpenHat"

            params = INSTRUMENT_PARAMS.get(instr_name_for_adsr)
            if params:
                release_time_beats = (params["adsr"][3] * song_data.bpm) / 60.0
                event_end_time_beats = event.time_start + event.duration + release_time_beats
                if event_end_time_beats > max_event_time_beats:
                    max_event_time_beats = event_end_time_beats

    total_song_duration_seconds = (max_event_time_beats / song_data.bpm) * 60.0 if song_data.bpm > 0 else 0
    total_song_samples = int(total_song_duration_seconds * sample_rate) + sample_rate # Add buffer

    master_stereo_buffer = np.zeros((total_song_samples, 2), dtype=np.float32) # Stereo buffer

    for track_name, track_events in song_data.tracks.items():
        for event in track_events:
            # Determine full instrument name for processing (e.g. Drums_Kick vs just Drums)
            instrument_name_full = track_name
            if track_name == "Drums":
                if event.note == 60: instrument_name_full = "Drums_Kick"
                elif event.note == 61: instrument_name_full = "Drums_Snare"
                elif event.note == 62: instrument_name_full = "Drums_Hat"
                elif event.note == 63: instrument_name_full = "Drums_OpenHat"
                else: continue # Skip unknown drum notes

            start_sample, mono_audio_chunk = render_midi_event_mono(event, instrument_name_full, song_data.bpm, sample_rate)

            if mono_audio_chunk is not None and mono_audio_chunk.size > 0:
                # Apply panning to the mono chunk to make it stereo
                pan_value = audio_processing.TRACK_PANNING.get(instrument_name_full, audio_processing.TRACK_PANNING["Default"])
                stereo_audio_chunk = audio_processing.apply_panning(mono_audio_chunk, pan_value)

                end_sample = start_sample + len(stereo_audio_chunk)
                if end_sample <= total_song_samples:
                    master_stereo_buffer[start_sample:end_sample] += stereo_audio_chunk
                else:
                    available_len = total_song_samples - start_sample
                    if available_len > 0:
                         master_stereo_buffer[start_sample:, :] += stereo_audio_chunk[:available_len, :]

    # Apply mastering chain to the final stereo mix
    final_mastered_mix = audio_processing.apply_mastering_chain(master_stereo_buffer)

    return final_mastered_mix


# --- Example Usage (for testing this module) ---
if __name__ == "__main__":
    # This now requires audio_processing.py to be in the same directory or accessible
    # and song_generator.py for a full test
    print("Synthesizer Module Test (with Auto-Mixing Integration)")

    class DummyMIDIEvent: # For basic testing without full song_generator
        def __init__(self, type, note, velocity, time_start, duration, channel=0):
            self.type, self.note, self.velocity, self.time_start, self.duration, self.channel = \
                type, note, velocity, time_start, duration, channel

    event_c4_melody = DummyMIDIEvent('note', 60, 100, 0, 2, 0) # C4, 2 beats
    bpm_test = 120

    # Test mono rendering (includes level and EQ)
    start_idx_mono, audio_data_mono = render_midi_event_mono(event_c4_melody, "Melody", bpm_test, SAMPLE_RATE)
    if audio_data_mono is not None:
        print(f"Rendered MONO 'Melody' C4 note: Start sample {start_idx_mono}, {len(audio_data_mono)} samples. Max amp: {np.max(np.abs(audio_data_mono)):.4f}")
    else:
        print("Failed to render mono melody note.")

    # Full song render test (if song_generator is available)
    try:
        import song_generator
        print("\nAttempting to generate a test song for full STEREO render...")
        test_song = song_generator.generate_full_song(mood="Happy", key_root_name="C", key_octave=4, bpm=120)
        if test_song:
            print("Test song generated. Rendering to stereo audio with mixing/mastering...")
            start_render_time = time.time()
            full_stereo_mix = render_song_to_stereo_mix(test_song, SAMPLE_RATE)
            end_render_time = time.time()
            print(f"Full song rendered in {end_render_time - start_render_time:.2f} seconds.")
            print(f"Stereo mix samples: {full_stereo_mix.shape}, Duration: {full_stereo_mix.shape[0]/SAMPLE_RATE:.2f}s")
            print(f"Max amplitude in stereo mix: L={np.max(np.abs(full_stereo_mix[:,0])):.4f}, R={np.max(np.abs(full_stereo_mix[:,1])):.4f}")

            # Optional: save to wav for listening (requires scipy.io.wavfile or wave module)
            try:
                from scipy.io.wavfile import write as write_wav
                # Ensure data is in int16 for typical WAV if player doesn't support float32
                # scaled_audio = np.int16(full_stereo_mix * 32767) # For int16
                # write_wav("test_song_stereo_render.wav", SAMPLE_RATE, scaled_audio)
                write_wav("test_song_stereo_render_float32.wav", SAMPLE_RATE, full_stereo_mix.astype(np.float32)) # Save as float32
                print("Test stereo song saved to test_song_stereo_render_float32.wav")
            except ImportError:
                print("Scipy not installed, cannot save WAV for testing here.")
            except Exception as e:
                print(f"Error saving WAV: {e}")
        else:
            print("Could not generate test song.")
    except ImportError:
        print("song_generator.py not found or error importing. Skipping full render test.")
    except Exception as e:
        print(f"An error occurred during full song render test: {e}")

```

And update `main.py`'s `sd.OutputStream` to expect 2 channels.
