import random
import music_theory

# --- Global Song Parameters (can be adjusted by UI later) ---
DEFAULT_BPM = 120
DEFAULT_KEY_ROOT_MIDI = music_theory.note_to_midi("C", 4) # C4
DEFAULT_KEY_TYPE = "major" # "major" or "minor"

# Song Structure Definition (fixed as per requirements)
SONG_STRUCTURE_TEMPLATE = ["Chorus", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus"]

BAR_LENGTH_BEATS = 4
CHORDS_PER_BAR = 1
SECTION_LENGTH_BARS = {
    "Verse": 4,
    "Chorus": 4,
    "Bridge": 4,
}

class MIDIEvent:
    def __init__(self, type, note, velocity, time_start, duration, channel=0):
        self.type = type
        self.note = note
        self.velocity = velocity
        self.time_start = time_start
        self.duration = duration
        self.channel = channel

    def __repr__(self):
        return f"MIDIEvent(type={self.type}, note={self.note}, vel={self.velocity}, start={self.time_start:.2f}, dur={self.duration:.2f}, ch={self.channel})"

def generate_pads(chord_progression_details, section_start_time, section_duration_beats, channel, key_root_midi, key_type):
    pad_events = []
    num_chords = len(chord_progression_details)
    if num_chords == 0:
        return []

    duration_per_chord = section_duration_beats / num_chords
    current_time = section_start_time

    for chord_info in chord_progression_details:
        for note_midi in chord_info["notes"]:
            adjusted_note = note_midi
            while adjusted_note > music_theory.note_to_midi("C", 5):
                adjusted_note -= 12
            while adjusted_note < music_theory.note_to_midi("C", 3):
                 adjusted_note +=12

            if 0 <= adjusted_note <= 127:
                 pad_events.append(MIDIEvent(
                    type='note', note=adjusted_note, velocity=random.randint(60, 80),
                    time_start=current_time, duration=duration_per_chord * 0.95, channel=channel
                ))
        current_time += duration_per_chord
    return pad_events

def generate_bassline(chord_progression_details, section_start_time, section_duration_beats, channel, key_root_midi, key_type, mood):
    bass_events = []
    num_chords = len(chord_progression_details)
    if num_chords == 0: return []
    beats_per_chord = section_duration_beats / num_chords
    current_time = section_start_time

    for chord_info in chord_progression_details:
        bass_note_midi = chord_info["root_midi"]
        if bass_note_midi >= music_theory.note_to_midi("C", 3): bass_note_midi -= 12
        if bass_note_midi >= music_theory.note_to_midi("C", 2): bass_note_midi -=12
        bass_note_midi = max(0, min(127, bass_note_midi))

        if beats_per_chord >= BAR_LENGTH_BEATS:
            bass_events.append(MIDIEvent('note', bass_note_midi, random.randint(90,110), current_time, beats_per_chord * 0.45, channel))
            bass_events.append(MIDIEvent('note', bass_note_midi, random.randint(85,100), current_time + beats_per_chord * 0.5, beats_per_chord * 0.45, channel))
        else:
            bass_events.append(MIDIEvent('note', bass_note_midi, random.randint(90,110), current_time, beats_per_chord * 0.9, channel))
        current_time += beats_per_chord
    return bass_events

def generate_melody_line(chord_progression_details, section_start_time, section_duration_beats, channel, key_root_midi, key_type, mood, layer_name="Melody"):
    melody_events = []
    scale_notes = music_theory.get_scale_notes(key_root_midi, key_type)
    melodic_range_notes = [n for n in scale_notes if music_theory.note_to_midi("C", 4) <= n <= music_theory.note_to_midi("C", 6)]
    if not melodic_range_notes: melodic_range_notes = scale_notes
    num_chords = len(chord_progression_details)
    if num_chords == 0 or not melodic_range_notes: return []
    beats_per_chord = section_duration_beats / num_chords
    current_event_time = section_start_time
    last_note = None

    for i, chord_info in enumerate(chord_progression_details):
        chord_tones = chord_info["notes"]
        possible_notes = sorted(list(set(chord_tones + melodic_range_notes)))
        possible_notes = [n for n in possible_notes if music_theory.note_to_midi("C", 4) <= n <= music_theory.note_to_midi("C", 6)]
        if not possible_notes: possible_notes = melodic_range_notes

        notes_in_this_chord_segment = random.choice([2,3,4] if mood == "Happy" else [1,2] if mood == "Sad" else [2,3])
        duration_per_note = beats_per_chord / notes_in_this_chord_segment if notes_in_this_chord_segment > 0 else beats_per_chord

        for _ in range(notes_in_this_chord_segment):
            selected_note = None
            if random.random() < 0.7 or last_note is None:
                candidate_notes = [n for n in chord_tones if n in possible_notes]
                if not candidate_notes: candidate_notes = possible_notes
                selected_note = random.choice(candidate_notes) if candidate_notes else None
            else:
                step_candidates = [n for n in possible_notes if abs(n - last_note) <= 2 and n != last_note] # type: ignore
                if step_candidates and random.random() < 0.6:
                    selected_note = random.choice(step_candidates)
                else:
                    selected_note = random.choice(possible_notes) if possible_notes else None

            if selected_note is not None:
                min_note, max_note = music_theory.note_to_midi("C",4), music_theory.note_to_midi("C",6)
                if layer_name == "Harmony Line": min_note, max_note = music_theory.note_to_midi("G",3), music_theory.note_to_midi("G",5)
                elif layer_name == "Counter-Melody": min_note, max_note = music_theory.note_to_midi("C",3), music_theory.note_to_midi("C",5)
                while selected_note < min_note and selected_note + 12 <= max_note : selected_note += 12
                while selected_note > max_note and selected_note - 12 >= min_note : selected_note -= 12
                selected_note = max(min_note, min(max_note, selected_note))
                melody_events.append(MIDIEvent('note',selected_note,random.randint(80,115),current_event_time,duration_per_note*0.85,channel))
                last_note = selected_note
            current_event_time += duration_per_note
    return melody_events

def generate_harmony_line(main_melody_events, chord_progression_details, section_start_time, section_duration_beats, channel, key_root_midi, key_type, mood):
    harmony_events = []
    scale_notes = music_theory.get_scale_notes(key_root_midi, key_type)
    harmony_range_notes = [n for n in scale_notes if music_theory.note_to_midi("G", 3) <= n <= music_theory.note_to_midi("G", 5)]
    if not harmony_range_notes: harmony_range_notes = scale_notes

    for melody_event in main_melody_events:
        melody_note = melody_event.note
        harmony_note_candidate = None
        current_chord = None
        num_chords = len(chord_progression_details)
        beats_per_chord = section_duration_beats / num_chords if num_chords > 0 else section_duration_beats

        chord_idx = 0
        if beats_per_chord > 0 :
            chord_idx = int((melody_event.time_start - section_start_time) / beats_per_chord)

        if 0 <= chord_idx < num_chords: current_chord = chord_progression_details[chord_idx]

        if current_chord:
            possible_harmony_notes = [n for n in current_chord["notes"] if n != melody_note and n in harmony_range_notes]
            if not possible_harmony_notes: possible_harmony_notes = [n for n in harmony_range_notes if n != melody_note]
            if possible_harmony_notes:
                lower_candidates = [n for n in possible_harmony_notes if n < melody_note]
                harmony_note_candidate = random.choice(lower_candidates) if lower_candidates else random.choice(possible_harmony_notes)

        if harmony_note_candidate is None: # Fallback
            fallback_candidates = [n for n in harmony_range_notes if n < melody_note]
            if fallback_candidates: harmony_note_candidate = random.choice(fallback_candidates)

        if harmony_note_candidate is not None:
            harmony_events.append(MIDIEvent('note',harmony_note_candidate,melody_event.velocity-random.randint(10,20),melody_event.time_start,melody_event.duration,channel))
    return harmony_events

def generate_counter_melody(main_melody_events, chord_progression_details, section_start_time, section_duration_beats, channel, key_root_midi, key_type, mood):
    return generate_melody_line(chord_progression_details,section_start_time,section_duration_beats,channel,key_root_midi,key_type,mood,layer_name="Counter-Melody")

def generate_drums(section_start_time, section_duration_beats, channel, mood):
    drum_events = []
    KICK_NOTE, SNARE_NOTE, HAT_NOTE, OPEN_HAT_NOTE = 60, 61, 62, 63 # Example MIDI notes
    num_bars = int(section_duration_beats / BAR_LENGTH_BEATS) if BAR_LENGTH_BEATS > 0 else 0
    for bar in range(num_bars):
        bar_start_time = section_start_time + (bar * BAR_LENGTH_BEATS)
        # Kick
        drum_events.append(MIDIEvent('note', KICK_NOTE, random.randint(100,120), bar_start_time + 0, 0.1, channel))
        if mood == "Happy" or mood == "Chill":
            if random.random() < 0.7: drum_events.append(MIDIEvent('note', KICK_NOTE, random.randint(95,115), bar_start_time + 2, 0.1, channel))
            if mood == "Happy" and random.random() < 0.4: drum_events.append(MIDIEvent('note', KICK_NOTE, random.randint(90,110), bar_start_time + 1.5, 0.1, channel))
        elif mood == "Sad": # Simpler kick
            if random.random() < 0.5 : drum_events.append(MIDIEvent('note', KICK_NOTE, random.randint(95,115), bar_start_time + 2, 0.1, channel))
        # Snare
        drum_events.append(MIDIEvent('note', SNARE_NOTE, random.randint(90,110), bar_start_time + 1, 0.1, channel))
        drum_events.append(MIDIEvent('note', SNARE_NOTE, random.randint(90,110), bar_start_time + 3, 0.1, channel))
        if mood == "Chill" and random.random() < 0.3: drum_events.append(MIDIEvent('note', SNARE_NOTE, random.randint(60,80), bar_start_time + 2.5, 0.05, channel))

        # Hi-Hats
        hat_patterns = {
            "Happy": [i*0.25 for i in range(16)], # 16th notes
            "Sad": [0,1,2,3], # Quarter notes
            "Chill": [0,1,1.5,2.5,3] # Syncopated
        }
        selected_hat_pattern = hat_patterns.get(mood, [0,0.5,1,1.5,2,2.5,3,3.5]) # Default to 8th notes

        hat_vel_ranges = {"Happy": (75,95), "Sad": (60,80), "Chill": (70,90)}
        hat_vel = random.randint(*hat_vel_ranges.get(mood, (70,90)))

        open_hat_chances = {"Happy": 0.15, "Sad": 0.05, "Chill": 0.2}
        open_hat_chance = open_hat_chances.get(mood, 0.1)

        for beat_offset in selected_hat_pattern:
            hat_time = bar_start_time + beat_offset
            is_open_hat_trigger = random.random() < open_hat_chance and \
                                (beat_offset % 1 == 0.5 or (selected_hat_pattern and beat_offset == max(selected_hat_pattern)))
            note_to_use = OPEN_HAT_NOTE if is_open_hat_trigger else HAT_NOTE
            duration = 0.2 if is_open_hat_trigger else 0.08

            # Avoid clash with snare
            if not (abs(beat_offset - 1) < 0.1 or abs(beat_offset - 3) < 0.1):
                 drum_events.append(MIDIEvent('note', note_to_use, hat_vel - random.randint(0,10), hat_time, duration, channel))
    return drum_events

class Song:
    def __init__(self):
        self.tracks = {"Melody":[],"Harmony Line":[],"Counter-Melody":[],"Bassline":[],"Pads":[],"Drums":[]}
        self.bpm = DEFAULT_BPM
        self.key_root_midi = DEFAULT_KEY_ROOT_MIDI
        self.key_type = DEFAULT_KEY_TYPE
        self.mood = "Happy"
        self.structure = SONG_STRUCTURE_TEMPLATE # Default structure
        self.section_details = [] # Will store {'name': str, 'start_beat': float, 'duration_beats': float, 'chord_progression': list}

    def get_all_events(self):
        all_events = [event for track_events in self.tracks.values() for event in track_events]
        all_events.sort(key=lambda x: (x.time_start, x.note, x.duration)) # Sort by time, then note, then duration
        return all_events

    def get_events_by_track(self): return self.tracks

# MIDI channels (0-indexed)
CHANNEL_MAP = {"Melody":0,"Harmony Line":1,"Counter-Melody":2,"Bassline":3,"Pads":4,"Drums":9 }

def generate_full_song(mood="Happy", key_root_name="C", key_octave=4, bpm=120):
    song = Song()
    song.mood = mood
    song.bpm = bpm
    try: song.key_root_midi = music_theory.note_to_midi(key_root_name, key_octave)
    except ValueError: song.key_root_midi = music_theory.note_to_midi("C", 4) # Default C4

    song.key_type = "major" if mood == "Happy" else "minor" if mood == "Sad" else random.choice(["major", "minor"])

    current_song_time_beats = 0.0
    song.section_details = [] # Clear any previous details

    for section_name in song.structure: # Use song.structure which might have been set
        section_length_bars = SECTION_LENGTH_BARS.get(section_name, 4) # Default to 4 bars
        section_duration_beats = section_length_bars * BAR_LENGTH_BEATS
        num_chords_in_section = section_length_bars * CHORDS_PER_BAR if BAR_LENGTH_BEATS > 0 else section_length_bars

        chord_prog_for_section = music_theory.generate_chord_progression(
            song.key_root_midi, song.key_type, num_chords_in_section
        )

        current_section_detail = {
            "name": section_name,
            "start_beat": current_song_time_beats,
            "duration_beats": section_duration_beats,
            "chord_progression": chord_prog_for_section,
            "key_root_midi": song.key_root_midi, # Section inherits song key by default
            "key_type": song.key_type
        }
        song.section_details.append(current_section_detail)

        # Generate events for this section
        section_events_by_track = generate_events_for_section(current_section_detail, chord_prog_for_section, song.mood, CHANNEL_MAP)
        for track_name, events in section_events_by_track.items():
            song.tracks[track_name].extend(events)

        current_song_time_beats += section_duration_beats

    return song

def generate_events_for_section(section_detail, chord_prog_for_section, mood, channel_map):
    """
    Helper function to generate all layer events for a single section.
    `section_detail` should contain `start_beat`, `duration_beats`, `key_root_midi`, `key_type`.
    Returns a dictionary: {"TrackName": [event1, event2], ...}
    """
    section_events = {track_name: [] for track_name in Song().tracks.keys()}

    s_time = section_detail['start_beat']
    s_dur = section_detail['duration_beats']
    s_key_root = section_detail['key_root_midi']
    s_key_type = section_detail['key_type']

    # Pads
    section_events["Pads"].extend(generate_pads(
        chord_prog_for_section, s_time, s_dur, channel_map["Pads"], s_key_root, s_key_type
    ))
    # Bassline
    section_events["Bassline"].extend(generate_bassline(
        chord_prog_for_section, s_time, s_dur, channel_map["Bassline"], s_key_root, s_key_type, mood
    ))
    # Melody (Primary)
    mel_events = generate_melody_line(
        chord_prog_for_section, s_time, s_dur, channel_map["Melody"], s_key_root, s_key_type, mood, layer_name="Melody"
    )
    section_events["Melody"].extend(mel_events)
    # Harmony Line
    section_events["Harmony Line"].extend(generate_harmony_line(
        mel_events, chord_prog_for_section, s_time, s_dur, channel_map["Harmony Line"], s_key_root, s_key_type, mood
    ))
    # Counter-Melody
    section_events["Counter-Melody"].extend(generate_counter_melody(
        mel_events, chord_prog_for_section, s_time, s_dur, channel_map["Counter-Melody"], s_key_root, s_key_type, mood
    ))
    # Drums
    section_events["Drums"].extend(generate_drums(
        s_time, s_dur, channel_map["Drums"], mood
    ))
    return section_events

def regenerate_specific_section(song_object, section_index, channel_map):
    """
    Regenerates the musical content for a specific section within the song_object.
    The section's duration, key, and overall mood are preserved.
    The chord progression for that section IS regenerated.
    Modifies song_object.tracks and song_object.section_details directly. Returns modified song_object.
    """
    if not (0 <= section_index < len(song_object.section_details)):
        print(f"Error: Invalid section_index {section_index} for regeneration.")
        return song_object

    section_detail = song_object.section_details[section_index]
    s_key_root = section_detail['key_root_midi']
    s_key_type = section_detail['key_type']
    s_start_beat = section_detail['start_beat']
    s_duration_beats = section_detail['duration_beats']

    # Regenerate chord progression for this section
    num_chords = int(s_duration_beats / BAR_LENGTH_BEATS) * CHORDS_PER_BAR if BAR_LENGTH_BEATS > 0 else int(s_duration_beats * CHORDS_PER_BAR)

    new_chord_prog = music_theory.generate_chord_progression(
        s_key_root, s_key_type, num_chords
    )
    song_object.section_details[section_index]['chord_progression'] = new_chord_prog # Update the stored progression

    # Generate new events for this section using the updated section_detail (with new chord prog)
    new_section_events_by_track = generate_events_for_section(
        song_object.section_details[section_index], # Pass the modified detail
        new_chord_prog, # Explicitly pass the new progression
        song_object.mood,
        channel_map
    )

    # Remove old events from all tracks that fall within this section's time window
    for track_name in song_object.tracks.keys():
        song_object.tracks[track_name] = [
            event for event in song_object.tracks[track_name]
            if not (s_start_beat <= event.time_start < s_start_beat + s_duration_beats)
        ]
        # Add new events
        song_object.tracks[track_name].extend(new_section_events_by_track.get(track_name, []))
        # Re-sort track events by time (important!)
        song_object.tracks[track_name].sort(key=lambda e: e.time_start)

    return song_object


if __name__ == "__main__":
    print("Song Generator Module Test")

    happy_song = generate_full_song(mood="Happy", key_root_name="C", key_octave=4, bpm=140)
    print(f"Generated song with BPM: {happy_song.bpm}, Key: {music_theory.midi_to_note_name(happy_song.key_root_midi)} {happy_song.key_type}")
    print(f"Number of sections: {len(happy_song.structure)}") # Should be from SONG_STRUCTURE_TEMPLATE

    total_events = 0
    for track_name, events in happy_song.tracks.items():
        print(f"  Track: {track_name}, Number of MIDI events: {len(events)}")
        total_events += len(events)
    print(f"Total MIDI events in song: {total_events}")

    print("\n--- Section Details from happy_song ---")
    for i, detail in enumerate(happy_song.section_details):
        print(f"Section {i+1}: {detail['name']}, Start: {detail['start_beat']:.2f}, Chords: {len(detail['chord_progression'])}")


    # Test section regeneration
    print("\nTesting section regeneration...")
    # Use a fresh song for regen test to avoid side effects if tests are run multiple times
    test_song_for_regen = generate_full_song(mood="Chill", key_root_name="D", key_octave=3, bpm=100)

    section_to_regen_idx = 1 # Regenerate the first Verse (index 1)

    if section_to_regen_idx < len(test_song_for_regen.section_details):
        s_detail_before = test_song_for_regen.section_details[section_to_regen_idx]
        original_melody_events_in_section_count = len([
            e for e in test_song_for_regen.tracks["Melody"]
            if s_detail_before['start_beat'] <= e.time_start < s_detail_before['start_beat'] + s_detail_before['duration_beats']
        ])
        print(f"Original melody in section {section_to_regen_idx} ('{s_detail_before['name']}') had {original_melody_events_in_section_count} events.")

        regenerated_song = regenerate_specific_section(test_song_for_regen, section_to_regen_idx, CHANNEL_MAP)

        s_detail_after = regenerated_song.section_details[section_to_regen_idx]
        melody_events_in_section_after_count = len([
            e for e in regenerated_song.tracks["Melody"]
            if s_detail_after['start_beat'] <= e.time_start < s_detail_after['start_beat'] + s_detail_after['duration_beats']
        ])
        print(f"Melody in section {section_to_regen_idx} ('{s_detail_after['name']}') after regen has {melody_events_in_section_after_count} events.")
        print(f"Total melody events in song after regen: {len(regenerated_song.tracks['Melody'])}")

        # Verify other sections were not inadvertently cleared (simple check)
        # For example, check if section 0 still has events
        if len(regenerated_song.section_details) > 0:
            s0_detail = regenerated_song.section_details[0]
            s0_melody_events = len([e for e in regenerated_song.tracks["Melody"] if s0_detail['start_beat'] <= e.time_start < s0_detail['start_beat'] + s0_detail['duration_beats']])
            print(f"Melody events in section 0 after regen of section {section_to_regen_idx}: {s0_melody_events}")
            assert s0_melody_events > 0, "Section 0 melody events were lost!"
    else:
        print(f"Skipping regen test for section {section_to_regen_idx} - not enough sections.")

    print("Song generator module test finished.")
```

I've also corrected some potential division by zero errors in the generation logic (e.g. `beats_per_chord` if `num_chords` is 0, or `BAR_LENGTH_BEATS` being 0) and made the `__main__` test block for regeneration more robust.

Now that `song_generator.py` should be correctly created with the necessary functions, the `regenerate_section_action` in `main.py` should work as intended.

The Mute/Solo functionality is still a placeholder in the context menu. Implementing full Mute/Solo per layer, especially per-section per-layer, is a significant feature that would likely involve:
*   Adding mute/solo state management (e.g., in the `Song` object or `ProceduralSongGeneratorApp`).
*   Modifying the `synthesizer.render_midi_event` or `synthesizer.render_song_to_audio` to skip rendering muted events/tracks.
*   Updating the UI to reflect and control these states.
For now, the "Regenerate Section" part of the song structure editor is the primary focus.
