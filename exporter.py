import numpy as np
import mido
from scipy.io import wavfile
from pydub import AudioSegment
import math

# --- MIDI Export ---
DEFAULT_TICKS_PER_BEAT = 480
DEFAULT_MIDI_VELOCITY = 90 # Default velocity for notes if not specified otherwise by event

def save_midi_file(song_data, filepath, ticks_per_beat=DEFAULT_TICKS_PER_BEAT):
    """
    Saves the generated song data as a MIDI file.
    Each track in song_data.tracks becomes a MIDI track.
    """
    if not song_data:
        raise ValueError("No song data to export.")

    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)

    for track_name, events in song_data.tracks.items():
        midi_track = mido.MidiTrack()
        mid.tracks.append(midi_track)
        midi_track.append(mido.MetaMessage('track_name', name=track_name, time=0))

        # Sort events by start time just in case, though they should be somewhat sorted.
        # The critical part is calculating delta times correctly.
        sorted_events = sorted(events, key=lambda e: e.time_start)

        last_event_abs_ticks = 0

        for event in sorted_events:
            if event.type == 'note':
                abs_start_ticks = int(round(event.time_start * ticks_per_beat * (song_data.bpm / 60.0)))
                abs_end_ticks = int(round((event.time_start + event.duration) * ticks_per_beat * (song_data.bpm / 60.0)))

                # Note On message
                delta_on = abs_start_ticks - last_event_abs_ticks
                midi_track.append(mido.Message('note_on',
                                               note=event.note,
                                               velocity=event.velocity,
                                               time=max(0, delta_on),  # Delta time must be non-negative
                                               channel=event.channel))
                last_event_abs_ticks = abs_start_ticks

                # Note Off message - Mido handles sorting these if they are added to a list
                # then processed, but easier to interleave if strict timing is needed.
                # For simplicity here, we'll add note_off relative to the note_on's absolute time.
                # This means we need a way to sort messages by absolute time before finalizing deltas,
                # or ensure note_offs are also timed with deltas.
                #
                # Simpler: Calculate delta for note_off based on previous event (which was its note_on)
                # No, this is wrong. Delta is always from the *previous message on this track*.
                # A common way is to store (abs_time, message) tuples, sort them, then calculate deltas.

                # Let's try the tuple storage method for robustness:
                # This event processing logic needs to be outside the loop to collect all ons/offs first.
                pass # Will be handled by a more robust approach below.

        # Robust MIDI event timing:
        # 1. Create a list of (absolute_tick, message_type, note, velocity, channel)
        timed_midi_messages = []
        for event in sorted_events: # Iterate again, this time for the robust list
            if event.type == 'note':
                abs_start_ticks = int(round(event.time_start * ticks_per_beat * (song_data.bpm / 60.0)))
                abs_end_ticks = int(round((event.time_start + event.duration) * ticks_per_beat * (song_data.bpm / 60.0)))

                timed_midi_messages.append(
                    (abs_start_ticks, 'note_on', event.note, event.velocity, event.channel)
                )
                # Ensure note_off is not before note_on, and duration is at least 1 tick if very short
                duration_ticks = abs_end_ticks - abs_start_ticks
                if duration_ticks <=0 : duration_ticks = 1 # Minimum 1 tick duration for a note_off

                timed_midi_messages.append(
                    (abs_start_ticks + duration_ticks, 'note_off', event.note, 0, event.channel) # Velocity 0 for note_off
                )

        # 2. Sort this list by absolute_tick, then by message type (note_off before note_on at same time)
        def sort_key(msg_tuple):
            abs_time, msg_type = msg_tuple[0], msg_tuple[1]
            # Process note_off before note_on if they occur at the exact same tick
            # (e.g. end of one note, start of another)
            type_priority = 0 if msg_type == 'note_off' else 1
            return (abs_time, type_priority)

        timed_midi_messages.sort(key=sort_key)

        # 3. Iterate through sorted list, create Mido messages, and calculate delta times
        last_abs_ticks_for_track = 0
        for msg_info in timed_midi_messages:
            abs_ticks, msg_type, note, velocity, channel = msg_info
            delta_ticks = abs_ticks - last_abs_ticks_for_track

            midi_track.append(mido.Message(msg_type,
                                           note=note,
                                           velocity=velocity,
                                           time=max(0, delta_ticks), # Ensure non-negative delta
                                           channel=channel))
            last_abs_ticks_for_track = abs_ticks

        # Add End of Track meta message
        # It should have a delta time from the last event. If no events, time=0.
        # For now, Mido might handle this, or we can add it with time=0 if last one was also 0.
        # midi_track.append(mido.MetaMessage('end_of_track', time=...))
        # Mido adds this automatically on save if not present.

    mid.save(filepath)
    print(f"MIDI file saved to {filepath}")


# --- WAV Export ---
def save_wav_file(audio_data_stereo, filepath, sample_rate):
    """
    Saves the stereo audio data as a WAV file.
    Assumes audio_data_stereo is a NumPy array with shape (N, 2) and float32 dtype.
    """
    if not isinstance(audio_data_stereo, np.ndarray) or audio_data_stereo.ndim != 2 or audio_data_stereo.shape[1] != 2:
        raise ValueError("Audio data must be a stereo NumPy array (N, 2).")
    if audio_data_stereo.dtype != np.float32:
        # Attempt to convert if not float32, though this might indicate an issue upstream
        try:
            audio_data_stereo = audio_data_stereo.astype(np.float32)
            print("Warning: WAV data was not float32, converted.")
        except:
            raise ValueError("Audio data for WAV export must be convertible to float32.")

    # Ensure data is within [-1.0, 1.0] if it's float.
    # scipy.io.wavfile.write handles scaling for int16, but for float32 it expects [-1,1]
    # Our mastering chain should already ensure this, but a clamp is safe.
    audio_data_stereo = np.clip(audio_data_stereo, -1.0, 1.0)

    wavfile.write(filepath, sample_rate, audio_data_stereo)
    print(f"WAV file saved to {filepath}")


# --- MP3 Export ---
def save_mp3_file(audio_data_stereo, filepath, sample_rate, bitrate="192k"):
    """
    Saves the stereo audio data as an MP3 file using pydub.
    audio_data_stereo: NumPy array (N, 2), float32, range [-1.0, 1.0]
    Requires ffmpeg or libav to be installed and in PATH for pydub.
    """
    if not isinstance(audio_data_stereo, np.ndarray) or audio_data_stereo.ndim != 2 or audio_data_stereo.shape[1] != 2:
        raise ValueError("Audio data must be a stereo NumPy array (N, 2).")
    if audio_data_stereo.dtype != np.float32:
         audio_data_stereo = audio_data_stereo.astype(np.float32) # Ensure float32

    # Convert float32 NumPy array (range -1.0 to 1.0) to int16 (range -32768 to 32767)
    # Pydub's AudioSegment.from_mono_audiosegments or from_file expects data that can be
    # converted to raw audio bytes. For PCM, this is often int16.
    # Max value for int16
    int16_max = np.iinfo(np.int16).max
    audio_data_int16 = (audio_data_stereo * int16_max).astype(np.int16)

    # Create an AudioSegment.
    # Ensure channels=2 for stereo. sample_width=2 for 16-bit.
    try:
        audio_segment = AudioSegment(
            data=audio_data_int16.tobytes(),
            sample_width=audio_data_int16.dtype.itemsize, # Should be 2 for int16
            frame_rate=sample_rate,
            channels=2 # Stereo
        )
    except Exception as e:
        raise RuntimeError(f"Error creating AudioSegment for MP3 export: {e}. Check pydub installation and data format.")

    try:
        audio_segment.export(filepath, format="mp3", bitrate=bitrate)
        print(f"MP3 file saved to {filepath} with bitrate {bitrate}.")
    except Exception as e: # pydub often raises generic Exception or specific like CouldntEncodeError
        error_message = f"Failed to export MP3: {e}. " \
                        "This often means FFmpeg or LAME is not installed or not found in your system's PATH. " \
                        "Please ensure FFmpeg (recommended) or LAME is installed correctly."
        print(error_message) # Also print to console for backend logging
        raise RuntimeError(error_message)


if __name__ == '__main__':
    # Basic tests (conceptual, as they need a Song object and audio data)
    print("Exporter Module Basic Tests")

    # Mock Song Data for MIDI export test
    class MockMIDIEvent:
        def __init__(self, type, note, velocity, time_start, duration, channel=0):
            self.type, self.note, self.velocity, self.time_start, self.duration, self.channel = \
                type, note, velocity, time_start, duration, channel

    class MockSongData:
        def __init__(self):
            self.bpm = 120
            self.tracks = {
                "Melody": [
                    MockMIDIEvent('note', 60, 90, 0.0, 1.0, 0), # C4, 1 beat
                    MockMIDIEvent('note', 62, 90, 1.0, 0.5, 0), # D4, 0.5 beat
                    MockMIDIEvent('note', 64, 90, 2.0, 1.5, 0)  # E4, 1.5 beats
                ],
                "Bass": [
                    MockMIDIEvent('note', 36, 100, 0.0, 2.0, 1), # C2, 2 beats
                    MockMIDIEvent('note', 43, 100, 2.0, 2.0, 1)  # G2, 2 beats
                ]
            }

    mock_song = MockSongData()
    try:
        save_midi_file(mock_song, "test_export.mid")
        print("Test MIDI export successful (file created: test_export.mid). Please verify its content.")
    except Exception as e:
        print(f"Test MIDI export failed: {e}")

    # Mock Audio Data for WAV/MP3 export test
    sample_rate_test = 44100
    duration_test = 2.0 # seconds
    frequency_test_l = 440 # A4
    frequency_test_r = 660 # E5 (approx)

    t = np.linspace(0, duration_test, int(sample_rate_test * duration_test), endpoint=False)
    audio_l = 0.5 * np.sin(2 * np.pi * frequency_test_l * t)
    audio_r = 0.3 * np.sin(2 * np.pi * frequency_test_r * t)
    mock_stereo_audio = np.vstack((audio_l, audio_r)).T.astype(np.float32)

    try:
        save_wav_file(mock_stereo_audio, "test_export.wav", sample_rate_test)
        print("Test WAV export successful (file created: test_export.wav).")
    except Exception as e:
        print(f"Test WAV export failed: {e}")

    try:
        # This test for MP3 will likely fail if ffmpeg is not in the test environment's PATH
        save_mp3_file(mock_stereo_audio, "test_export.mp3", sample_rate_test)
        print("Test MP3 export successful (file created: test_export.mp3).")
    except Exception as e:
        print(f"Test MP3 export failed: {e}")
        print(" (This is expected if FFmpeg/LAME is not installed in the test environment.)")

    print("Exporter tests finished.")
