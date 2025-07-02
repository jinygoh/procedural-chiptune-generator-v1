import numpy as np
import scipy.signal

# --- Auto-Mixing Parameters ---

# Relative volume levels for each track (0.0 to 1.0 or higher, will be normalized later)
# These are gain factors.
TRACK_LEVELS = {
    "Melody": 0.9,
    "Harmony Line": 0.7,
    "Counter-Melody": 0.65,
    "Bassline": 1.0,
    "Pads": 0.5,
    "Drums_Kick": 1.0,
    "Drums_Snare": 0.9,
    "Drums_Hat": 0.6,
    "Drums_OpenHat": 0.65,
    "Default": 0.7
}

# Panning for tracks (-1.0 for full Left, 0.0 for Center, 1.0 for full Right)
TRACK_PANNING = {
    "Melody": -0.3,
    "Harmony Line": 0.3,
    "Counter-Melody": -0.6,
    "Bassline": 0.0,
    "Pads": 0.0,
    "Drums_Kick": 0.0,
    "Drums_Snare": 0.05,
    "Drums_Hat": 0.0,
    "Drums_OpenHat": 0.0,
    "Default": 0.0
}


def apply_panning(audio_mono, pan_value):
    if not isinstance(audio_mono, np.ndarray) or audio_mono.ndim != 1:
        return np.zeros((len(audio_mono) if hasattr(audio_mono, '__len__') else 0, 2), dtype=np.float32)

    # Constant power panning (approximated)
    # angle = (pan_value * 0.5 + 0.5) * (np.pi / 2) # Map pan value from [-1, 1] to angle [0, pi/2]
    # gain_l = np.cos(angle)
    # gain_r = np.sin(angle)

    # Simpler linear panning (easier to reason about, less "constant power")
    gain_l = min(1.0, 1.0 - pan_value if pan_value > 0 else 1.0)
    gain_r = min(1.0, 1.0 + pan_value if pan_value < 0 else 1.0)

    stereo_signal = np.zeros((len(audio_mono), 2), dtype=np.float32)
    stereo_signal[:, 0] = audio_mono * gain_l
    stereo_signal[:, 1] = audio_mono * gain_r

    return stereo_signal

# --- Auto-EQ (Placeholders / Basic Filters) ---

def apply_eq_track(audio_data_mono, track_name, sample_rate):
    """
    Applies basic EQ to a mono track before panning.
    """
    if not isinstance(audio_data_mono, np.ndarray) or audio_data_mono.ndim != 1 or audio_data_mono.size == 0:
        return audio_data_mono # Return unchanged if not suitable mono data

    if track_name not in ["Bassline", "Drums_Kick", "Pads"]: # Pads might have low freq content
        try:
            # 4th order Butterworth high-pass filter
            # Cutoff frequency (e.g., 80-100Hz for general high-passing non-bass elements)
            cutoff_hz = 90
            nyquist = 0.5 * sample_rate
            if cutoff_hz >= nyquist: # Avoid error if cutoff is too high for sample rate
                return audio_data_mono

            sos = scipy.signal.butter(N=4, Wn=cutoff_hz, btype='highpass', fs=sample_rate, output='sos')
            filtered_audio = scipy.signal.sosfilt(sos, audio_data_mono)
            return filtered_audio
        except Exception as e:
            print(f"Warning: Could not apply HPF to {track_name}: {e}")
            return audio_data_mono

    # Placeholder for other EQs, like scooping for pads
    # if track_name == "Pads":
    #     try:
    #         # Example: Gentle scoop around 500Hz
    #         # sos_scoop = scipy.signal.butter(N=2, Wn=[400, 600], btype='bandstop', fs=sample_rate, output='sos')
    #         # audio_data_mono = scipy.signal.sosfilt(sos_scoop, audio_data_mono)
    #         pass # Not implementing scoop yet
    #     except Exception as e:
    #         print(f"Warning: Could not apply scoop EQ to {track_name}: {e}")
    #         return audio_data_mono

    return audio_data_mono


# --- Auto-Mastering ---

def apply_mastering_chain(stereo_audio_mix):
    processed_mix = stereo_audio_mix.copy()
    if processed_mix.size == 0: return processed_mix

    # 1. Basic Peak Normalization / Limiting
    # Normalize to a target peak level (e.g., -0.5 dBFS) to provide headroom and consistent output.
    target_peak_amplitude = 0.94 # Corresponds to approx -0.5 dBFS (20*log10(0.94))

    current_max_abs_val = np.max(np.abs(processed_mix))

    if current_max_abs_val == 0: # Silence
        return processed_mix

    if current_max_abs_val > target_peak_amplitude:
        gain_to_apply = target_peak_amplitude / current_max_abs_val
        processed_mix *= gain_to_apply
    # If it's quieter than target_peak_amplitude, this simple version doesn't boost it.
    # A true "mastering" chain might include upward compression or makeup gain.

    # 2. Optional: Very simple soft clipping as a safety net (if needed after normalization)
    # threshold = 0.98
    # processed_mix = threshold * np.tanh(processed_mix / threshold) if threshold > 0 else processed_mix

    return processed_mix


if __name__ == "__main__":
    print("Audio Processing Module Test")
    sr = 44100
    mono_sine = np.sin(np.linspace(0, 440 * 2 * np.pi * 1, sr, endpoint=False))

    # Test Panning
    pan_left = apply_panning(mono_sine, -0.5)
    print(f"Pan Left: L_max={np.max(pan_left[:,0]):.2f}, R_max={np.max(pan_left[:,1]):.2f}")

    # Test EQ (HPF)
    hpf_sine = apply_eq_track(mono_sine.copy(), "Melody", sr)
    # A simple check: sum of abs values should ideally decrease if HPF removes content,
    # or at least not increase significantly.
    print(f"Sum of abs mono_sine: {np.sum(np.abs(mono_sine)):.2f}")
    print(f"Sum of abs hpf_sine: {np.sum(np.abs(hpf_sine)):.2f}")
    assert np.sum(np.abs(hpf_sine)) <= np.sum(np.abs(mono_sine)) * 1.01, "HPF increased signal power unexpectedly"


    # Test Mastering
    stereo_loud = np.array([mono_sine * 1.5, mono_sine * 1.2]).T
    mastered_loud = apply_mastering_chain(stereo_loud)
    print(f"Mastered Loud: L_max={np.max(mastered_loud[:,0]):.2f}, R_max={np.max(mastered_loud[:,1]):.2f}")
    assert np.max(np.abs(mastered_loud)) < 0.95, "Mastering did not limit peak effectively"

    stereo_quiet = np.array([mono_sine * 0.2, mono_sine * 0.15]).T
    mastered_quiet = apply_mastering_chain(stereo_quiet)
    print(f"Mastered Quiet: L_max={np.max(mastered_quiet[:,0]):.2f}, R_max={np.max(mastered_quiet[:,1]):.2f}")
    # Quiet signal should remain quiet with this simple peak normalization
    assert np.allclose(np.max(np.abs(stereo_quiet)), np.max(np.abs(mastered_quiet))), "Quiet signal changed unexpectedly"
    print("Audio processing tests passed (basic checks).")
# ```
# The file `audio_processing.py` now includes:
# *   `TRACK_LEVELS` and `TRACK_PANNING` dictionaries.
# *   `apply_panning(audio_mono, pan_value)`: Converts a mono signal to stereo and applies panning. I've used a slightly more standard linear panning logic.
# *   `apply_eq_track(audio_data_mono, track_name, sample_rate)`: Applies a 4th-order Butterworth high-pass filter (cutoff 90Hz) to non-bass/kick/pad tracks using `scipy.signal`. Error handling for invalid cutoff is included. Other EQs are still conceptual.
# *   `apply_mastering_chain(stereo_audio_mix)`: Implements peak normalization to a target amplitude (approx -0.5 dBFS). This acts as a simple limiter by ensuring the output doesn't exceed this level. True compression or more advanced limiting is not yet included.
# *   Basic tests in the `if __name__ == "__main__":` block.

# Next, I need to modify `synthesizer.py` to:
# 1.  Use `TRACK_LEVELS` when rendering individual MIDI events.
# 2.  Apply the track-specific EQ using `apply_eq_track`.
# 3.  Convert the mono track audio to stereo using `apply_panning`.
# 4.  Sum these stereo tracks into a final stereo mix.
# 5.  Pass this final stereo mix through `apply_mastering_chain`.
# This means `render_song_to_audio` will now produce a stereo NumPy array. `main.py`'s `sd.OutputStream` will also need to be updated for 2 channels.
