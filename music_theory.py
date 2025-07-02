# music_theory.py

# MIDI note numbers for C0 octave
NOTE_TO_MIDI_BASE = {
    'C': 0, 'C#': 1, 'DB': 1,
    'D': 2, 'D#': 3, 'EB': 3,
    'E': 4, 'FB': 4,
    'F': 5, 'F#': 6, 'GB': 6,
    'G': 7, 'G#': 8, 'AB': 8,
    'A': 9, 'A#': 10, 'BB': 10,
    'B': 11, 'CB': 11,
}

def note_to_midi(note_name: str, octave: int) -> int:
    """
    Converts a musical note name (e.g., "C", "C#", "Db") and octave
    to its corresponding MIDI note number.
    C4 is MIDI note 60.
    """
    note_name_upper = note_name.upper()
    if note_name_upper not in NOTE_TO_MIDI_BASE:
        raise ValueError(f"Invalid note name: {note_name}")

    # MIDI octave numbering: C4 is middle C (MIDI note 60).
    # MIDI note number = base_note_value + (octave + 1) * 12
    # However, it's common in some systems for C4 to be octave 4.
    # If C0 is 0, then C4 is 4*12 = 48.
    # If C4 is 60, then C0 must be 12. (60 - 4*12 = 12)
    # Let's assume the standard where C4 = 60.
    # Our NOTE_TO_MIDI_BASE is for octave 0 if C0 = 0.
    # So, MIDI value = base_value + octave * 12.
    # For C4 to be 60, if octave is 4, then 60 = C_base + 4*12 => C_base = 12.
    # This means C in octave 0 is 12, C in octave 1 is 24, etc.
    # C-1 = 0
    # C0 = 12
    # C1 = 24
    # C2 = 36
    # C3 = 48
    # C4 = 60

    midi_val = NOTE_TO_MIDI_BASE[note_name_upper] + (octave + 1) * 12
    if not (0 <= midi_val <= 127):
        # Attempt to adjust octave if it's a common off-by-one interpretation for C4=60
        # Some systems treat octave 4 as the 'middle' octave for C4=60
        # Our calculation (octave + 1)*12 means:
        # note_to_midi("C", 4) = C_base[0] + (4+1)*12 = 0 + 60 = 60. This is correct for C4=60.
        # note_to_midi("C", 0) = C_base[0] + (0+1)*12 = 12. This is C0.
        # note_to_midi("C", -1) = C_base[0] + (-1+1)*12 = 0. This is C-1.
        # The formula seems fine for the C4=60 standard.
        # The error should be raised if the resulting midi_val is out of 0-127 range.
        raise ValueError(f"Resulting MIDI value {midi_val} for {note_name}{octave} is out of range [0, 127].")
    return midi_val

# Test (can be removed later)
if __name__ == '__main__':
    print("Testing note_to_midi:")
    print(f"C4: {note_to_midi('C', 4)}")      # Expected: 60
    print(f"C#4: {note_to_midi('C#', 4)}")    # Expected: 61
    print(f"Db4: {note_to_midi('Db', 4)}")    # Expected: 61
    print(f"A4: {note_to_midi('A', 4)}")      # Expected: 69
    print(f"C0: {note_to_midi('C', 0)}")      # Expected: 12
    print(f"B8: {note_to_midi('B', 8)}")      # Expected: 119
    # Test extremes
    print(f"C-1: {note_to_midi('C', -1)}")    # Expected: 0
    # print(f"G9: {note_to_midi('G', 9)}") # Expected: 127, (G_base=7 + (9+1)*12 = 7 + 120 = 127)
    try:
        print(f"C-2: {note_to_midi('C', -2)}") # Error
    except ValueError as e:
        print(e)
    try:
        print(f"G#9: {note_to_midi('G#', 9)}") # Error (G#_base=8 + 120 = 128)
    except ValueError as e:
        print(e)
    try:
        print(f"X4: {note_to_midi('X', 4)}")    # Error
    except ValueError as e:
        print(e)

MIDI_TO_NOTE_NAME_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# MIDI_TO_NOTE_NAME_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'] # For alternative naming

def midi_to_note_name(midi_note: int, prefer_sharps: bool = True) -> str:
    """
    Converts a MIDI note number to its musical note name and octave.
    e.g., 60 -> "C4", 61 -> "C#4" (if prefer_sharps is True)
    """
    if not (0 <= midi_note <= 127):
        raise ValueError(f"MIDI note {midi_note} is out of range [0, 127].")

    octave = (midi_note // 12) - 1
    note_index = midi_note % 12

    if prefer_sharps:
        note_name = MIDI_TO_NOTE_NAME_SHARP[note_index]
    else:
        # Could implement flat preference here if needed, using MIDI_TO_NOTE_NAME_FLAT
        # For now, defaulting to sharps or the primary name.
        note_name = MIDI_TO_NOTE_NAME_SHARP[note_index] # Placeholder, can be improved

    return f"{note_name}{octave}"

if __name__ == '__main__':
    print("\nTesting midi_to_note_name:")
    print(f"60: {midi_to_note_name(60)}")     # Expected: C4
    print(f"61: {midi_to_note_name(61)}")     # Expected: C#4
    print(f"69: {midi_to_note_name(69)}")     # Expected: A4
    print(f"12: {midi_to_note_name(12)}")     # Expected: C0
    print(f"0: {midi_to_note_name(0)}")       # Expected: C-1
    print(f"119: {midi_to_note_name(119)}")   # Expected: B8
    print(f"127: {midi_to_note_name(127)}")   # Expected: G9
    try:
        midi_to_note_name(128)
    except ValueError as e:
        print(e)

# Scale definitions (intervals in semitones from the root)
SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],  # W-W-H-W-W-W-H
    "minor": [0, 2, 3, 5, 7, 8, 10],  # Natural minor: W-H-W-W-H-W-W
    # Can add more scales like harmonic minor, melodic minor, pentatonic, etc. later
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor_asc": [0, 2, 3, 5, 7, 9, 11], # Melodic minor (ascending)
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 4, 6, 8, 10], # Rarely used harmonically
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10], # Minor pentatonic + flat 5th
}

def get_scale_notes(key_root_midi: int, key_type: str, num_octaves: int = 2) -> list[int]:
    """
    Generates a list of MIDI note numbers for a given scale and key.
    `key_type` can be "major", "minor", etc. as defined in SCALE_INTERVALS.
    `num_octaves` specifies how many octaves of the scale to generate, starting from the octave of key_root_midi.
    """
    key_type_lower = key_type.lower()
    if key_type_lower not in SCALE_INTERVALS:
        # Fallback to major or minor if a specific type isn't found
        if "major" in key_type_lower: key_type_lower = "major"
        elif "minor" in key_type_lower: key_type_lower = "minor"
        else: # Default to major if still not recognized
            print(f"Warning: Scale type '{key_type}' not recognized. Defaulting to major scale.")
            key_type_lower = "major"

    intervals = SCALE_INTERVALS[key_type_lower]
    scale_notes = []

    for i in range(num_octaves):
        for interval in intervals:
            note = key_root_midi + interval + (i * 12)
            if 0 <= note <= 127:
                scale_notes.append(note)
    
    # Add one more root note at the top for completeness over num_octaves
    top_root = key_root_midi + (num_octaves * 12)
    if 0 <= top_root <= 127:
        scale_notes.append(top_root)
        
    return sorted(list(set(scale_notes))) # Remove duplicates and sort

if __name__ == '__main__':
    print("\nTesting get_scale_notes:")
    c4_midi = note_to_midi('C', 4) # 60
    print(f"C Major scale (2 octaves from C4): {[midi_to_note_name(n) for n in get_scale_notes(c4_midi, 'major', 2)]}")
    # Expected: ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']

    a3_midi = note_to_midi('A', 3) # 45+12 = 57 (A_base=9 + (3+1)*12 = 9+48=57)
    print(f"A Natural Minor scale (1 octave from A3): {[midi_to_note_name(n) for n in get_scale_notes(a3_midi, 'minor', 1)]}")
    # Expected: ['A3', 'B3', 'C4', 'D4', 'E4', 'F4', 'G4', 'A4']

    fs5_midi = note_to_midi('F#', 5) # F#_base=6 + (5+1)*12 = 6 + 72 = 78
    print(f"F# Major Pentatonic (1 octave from F#5): {[midi_to_note_name(n) for n in get_scale_notes(fs5_midi, 'major_pentatonic', 1)]}")
    # Expected: ['F#5', 'G#5', 'A#5', 'C#6', 'D#6', 'F#6']
    
    # Test with a key type that might fall back
    print(f"C Happy scale (should default to major): {[midi_to_note_name(n) for n in get_scale_notes(c4_midi, 'Happy', 1)]}")

# Chord definitions (intervals from the chord's root note)
CHORD_TYPE_INTERVALS = {
    "major_triad": [0, 4, 7],        # Root, Major Third, Perfect Fifth
    "minor_triad": [0, 3, 7],        # Root, Minor Third, Perfect Fifth
    "diminished_triad": [0, 3, 6],   # Root, Minor Third, Diminished Fifth
    "augmented_triad": [0, 4, 8],    # Root, Major Third, Augmented Fifth
    "major_seventh": [0, 4, 7, 11],  # Major Triad + Major Seventh
    "minor_seventh": [0, 3, 7, 10],  # Minor Triad + Minor Seventh
    "dominant_seventh": [0, 4, 7, 10],# Major Triad + Minor Seventh
    "diminished_seventh": [0, 3, 6, 9],# Diminished Triad + Diminished Seventh (interval is 6 semitones above minor third)
    "half_diminished_seventh": [0, 3, 6, 10], # Diminished Triad + Minor Seventh
    "sus2": [0, 2, 7], # Root, Major Second, Perfect Fifth
    "sus4": [0, 5, 7], # Root, Perfect Fourth, Perfect Fifth
}

# Diatonic chords for major and minor keys (degree, type)
# Roman numerals: I, II, III, IV, V, VI, VII
# For major: I (maj), ii (min), iii (min), IV (maj), V (maj), vi (min), vii° (dim)
# For natural minor: i (min), ii° (dim), III (maj), iv (min), v (min), VI (maj), VII (maj)
# Using dominant V for minor (harmonic minor): i (min), ii° (dim), III+ (aug), iv (min), V (maj), VI (maj), vii° (dim)

DIATONIC_CHORDS_MAJOR = {
    1: "major_triad", 2: "minor_triad", 3: "minor_triad", 4: "major_triad",
    5: "major_triad", 6: "minor_triad", 7: "diminished_triad"
}
DIATONIC_CHORDS_MINOR = { # Using harmonic minor for V chord
    1: "minor_triad", 2: "diminished_triad", 3: "augmented_triad", 4: "minor_triad",
    5: "major_triad", 6: "major_triad", 7: "diminished_triad"
}
# Simpler natural minor variant if preferred for some moods:
# DIATONIC_CHORDS_MINOR_NATURAL = {
#     1: "minor_triad", 2: "diminished_triad", 3: "major_triad", 4: "minor_triad",
#     5: "minor_triad", 6: "major_triad", 7: "major_triad"
# }


def get_chord_notes(chord_root_midi: int, chord_type: str) -> list[int]:
    """
    Generates the MIDI notes for a given chord.
    `chord_type` refers to keys in CHORD_TYPE_INTERVALS.
    """
    chord_type_lower = chord_type.lower()
    if chord_type_lower not in CHORD_TYPE_INTERVALS:
        # Attempt a simple fallback
        if "maj" in chord_type_lower and "7" not in chord_type_lower and "seventh" not in chord_type_lower : chord_type_lower = "major_triad"
        elif "min" in chord_type_lower and "7" not in chord_type_lower and "seventh" not in chord_type_lower: chord_type_lower = "minor_triad"
        elif "dom" in chord_type_lower or ("maj" in chord_type_lower and ("7" in chord_type_lower or "seventh" in chord_type_lower)): chord_type_lower = "dominant_seventh"
        elif "min" in chord_type_lower and ("7" in chord_type_lower or "seventh" in chord_type_lower): chord_type_lower = "minor_seventh"
        else:
            print(f"Warning: Chord type '{chord_type}' not recognized. Defaulting to major triad.")
            chord_type_lower = "major_triad"

    intervals = CHORD_TYPE_INTERVALS[chord_type_lower]
    chord_notes = []
    for interval in intervals:
        note = chord_root_midi + interval
        if 0 <= note <= 127: # Ensure notes are within MIDI range
            chord_notes.append(note)
    return chord_notes


def generate_chord_progression(key_root_midi: int, key_type: str, num_chords: int) -> list[dict]:
    """
    Generates a chord progression for a given key and number of chords.
    Returns a list of dictionaries, where each dict is:
    {'root_midi': int, 'chord_type': str, 'notes': list[int]}
    """
    key_type_lower = key_type.lower()
    is_major_key = "major" in key_type_lower or \
                   (key_type_lower not in ["minor", "dorian", "phrygian", "locrian"] and "minor" not in key_type_lower)


    scale_notes_for_key = get_scale_notes(key_root_midi, "major" if is_major_key else "harmonic_minor", 1) # Get one octave for roots

    diatonic_map = DIATONIC_CHORDS_MAJOR if is_major_key else DIATONIC_CHORDS_MINOR

    progression = []

    # Simple I-IV-V-I style progressions, cycling or extending
    # Degrees are 1-indexed for music theory, but scale_notes_for_key is 0-indexed
    # I is scale_notes_for_key[0], IV is scale_notes_for_key[3], V is scale_notes_for_key[4]
    
    # Common progressions:
    # Major: I-IV-V-I, I-V-vi-IV, ii-V-I, I-vi-IV-V
    # Minor: i-iv-v-i (natural v), i-iv-V-i (harmonic V), i-VI-III-VII, i-iidim-V-i

    if num_chords == 0:
        return []
    if not scale_notes_for_key or len(scale_notes_for_key) < 7: # Need enough notes for diatonic chords
        # Fallback: just use root chord if scale is too small/weird
        chord_type = "major_triad" if is_major_key else "minor_triad"
        root_note = key_root_midi
        notes = get_chord_notes(root_note, chord_type)
        for _ in range(num_chords):
            progression.append({"root_midi": root_note, "chord_type": chord_type, "notes": notes, "degree": 1, "name": f"I ({chord_type})"})
        return progression

    # Define some simple patterns
    patterns = {
        "major": [
            [1, 4, 5, 1],  # I-IV-V-I
            [1, 5, 6, 4],  # I-V-vi-IV
            [2, 5, 1],     # ii-V-I
            [1, 6, 4, 5],  # I-vi-IV-V
        ],
        "minor": [ # Using V from harmonic minor
            [1, 4, 5, 1],  # i-iv-V-i
            [1, 6, 3, 7],  # i-VI-III-VII (VII from natural minor scale for III and VII typically)
            [1, 2, 5, 1],  # i-ii*-V-i (*ii is diminished)
        ]
    }

    current_pattern = patterns["major"] if is_major_key else patterns["minor"]
    # Pick a random pattern to start with, or cycle through them
    chosen_pattern_indices = current_pattern[num_chords % len(current_pattern)] # Cycle through patterns based on num_chords

    # Ensure scale_notes_for_key has enough notes for the chosen pattern degrees
    max_degree = 0
    for degree in chosen_pattern_indices: max_degree = max(max_degree,degree)
    
    # Adjust scale if needed (e.g. for minor key's III, VI, VII which might need natural minor context)
    # For simplicity here, we'll use the harmonic minor derived scale roots for minor keys for all degrees.
    # A more advanced system could switch scales for certain chords.

    if len(scale_notes_for_key) < max_degree: # Should not happen with diatonic 7-note scales
        print(f"Warning: Scale for {midi_to_note_name(key_root_midi)} {key_type} has too few notes ({len(scale_notes_for_key)}) for pattern degree {max_degree}. Falling back to tonic.")
        chord_type = "major_triad" if is_major_key else "minor_triad"
        root_note = key_root_midi
        notes = get_chord_notes(root_note, chord_type)
        prog_name_prefix = "I" if is_major_key else "i"
        for _ in range(num_chords):
            progression.append({"root_midi": root_note, "chord_type": chord_type, "notes": notes, "degree": 1, "name": f"{prog_name_prefix} ({chord_type})"})
        return progression


    for i in range(num_chords):
        degree = chosen_pattern_indices[i % len(chosen_pattern_indices)]
        
        # Get root of the chord (degree-1 because scale_notes is 0-indexed)
        # Ensure we don't go out of bounds if scale_notes_for_key is unexpectedly short
        if degree -1 >= len(scale_notes_for_key):
            print(f"Warning: Degree {degree} out of bounds for scale. Using tonic.")
            chord_root_note_midi = key_root_midi
            chord_type = diatonic_map[1]
        else:
            chord_root_note_midi = scale_notes_for_key[degree - 1]
            chord_type = diatonic_map[degree]

        chord_notes = get_chord_notes(chord_root_note_midi, chord_type)
        
        # For display/info purposes, get a name
        roman_numerals_major = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        roman_numerals_minor = ["i", "ii°", "III+", "iv", "V", "VI", "vii°"] # Based on harmonic minor
        
        numeral = ""
        if degree -1 < len(roman_numerals_major): # Defensive check
            if is_major_key:
                numeral = roman_numerals_major[degree-1]
            else:
                numeral = roman_numerals_minor[degree-1]


        progression.append({
            "root_midi": chord_root_note_midi,
            "chord_type": chord_type,
            "notes": chord_notes,
            "degree": degree,
            "name": f"{numeral} ({midi_to_note_name(chord_root_note_midi).replace(str((chord_root_note_midi // 12) - 1),'')} {chord_type})"
        })

    return progression


if __name__ == '__main__':
    print("\nTesting get_chord_notes:")
    c4_midi = note_to_midi('C', 4)
    print(f"C Major Triad from C4: {[midi_to_note_name(n) for n in get_chord_notes(c4_midi, 'major_triad')]}") # C4 E4 G4
    a3_midi = note_to_midi('A', 3)
    print(f"A Minor Seventh from A3: {[midi_to_note_name(n) for n in get_chord_notes(a3_midi, 'minor_seventh')]}") # A3 C4 E4 G4
    g4_midi = note_to_midi('G', 4)
    print(f"G Dominant Seventh from G4: {[midi_to_note_name(n) for n in get_chord_notes(g4_midi, 'dominant_seventh')]}") # G4 B4 D5 F5

    print("\nTesting generate_chord_progression:")
    c_major_prog_4 = generate_chord_progression(c4_midi, "major", 4)
    print(f"C Major progression (4 chords):")
    for chord in c_major_prog_4:
        print(f"  Root: {midi_to_note_name(chord['root_midi'])}, Type: {chord['chord_type']}, Notes: {[midi_to_note_name(n) for n in chord['notes']]}, Name: {chord['name']}")

    a_minor_prog_4 = generate_chord_progression(a3_midi, "minor", 4)
    print(f"A Minor progression (4 chords):")
    for chord in a_minor_prog_4:
        print(f"  Root: {midi_to_note_name(chord['root_midi'])}, Type: {chord['chord_type']}, Notes: {[midi_to_note_name(n) for n in chord['notes']]}, Name: {chord['name']}")

    d_major_prog_3 = generate_chord_progression(note_to_midi('D', 4), "major", 3)
    print(f"D Major progression (3 chords):")
    for chord in d_major_prog_3:
        print(f"  Root: {midi_to_note_name(chord['root_midi'])}, Type: {chord['chord_type']}, Notes: {[midi_to_note_name(n) for n in chord['notes']]}, Name: {chord['name']}")
        
    # Test with a key_type that should resolve (e.g. "Happy" from song_generator)
    c_happy_prog_4 = generate_chord_progression(c4_midi, "Happy", 4) # Should default to C Major
    print(f"C 'Happy' progression (4 chords):")
    for chord in c_happy_prog_4:
        print(f"  Root: {midi_to_note_name(chord['root_midi'])}, Type: {chord['chord_type']}, Notes: {[midi_to_note_name(n) for n in chord['notes']]}, Name: {chord['name']}")


print("music_theory.py updated with chord functions and progression generator")
