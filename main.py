import tkinter as tk
from tkinter import ttk, filedialog, messagebox # Added filedialog and messagebox here
import numpy as np # For audio data
import sounddevice as sd
import threading # To prevent GUI freezing during playback

# Import our other modules
import song_generator
import synthesizer
import music_theory # Potentially for key selection later
import exporter # For saving files

class ProceduralSongGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procedural Chiptune Song Generator")
        self.root.geometry("1200x800")

        self.current_song_data = None # To hold the generated song object
        self.current_audio_data = None # To hold the rendered audio samples
        self.playback_stream = None
        self.is_playing = False


        # Configure dark theme
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        dark_bg = "#2E2E2E"
        light_fg = "#EAEAEA"
        # select_bg = "#555555" # Keep for later if needed
        # select_fg = "#FFFFFF"

        self.style.configure("TFrame", background=dark_bg)
        self.style.configure("TLabel", background=dark_bg, foreground=light_fg, font=("Arial", 10))
        self.style.configure("TButton", background="#4A4A4A", foreground=light_fg, font=("Arial", 10), borderwidth=1)
        self.style.map("TButton",
                       background=[('active', '#606060'), ('pressed', '#3E3E3E')],
                       foreground=[('active', light_fg)])
        self.style.configure("TRadiobutton", background=dark_bg, foreground=light_fg, font=("Arial", 10))
        self.style.map("TRadiobutton",
                       background=[('active', dark_bg)],
                       indicatorcolor=[('selected', light_fg), ('!selected', "#888888")])

        self.root.configure(bg=dark_bg)

        # Main layout frames
        self.controls_frame = ttk.Frame(self.root, padding="10")
        self.controls_frame.pack(side=tk.TOP, fill=tk.X)

        self.visualizer_frame = ttk.Frame(self.root, padding="10")
        self.visualizer_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.structure_editor_frame = ttk.Frame(self.root, padding="10")
        self.structure_editor_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._setup_controls()
        self._setup_visualizer_placeholder()
        self._setup_structure_editor_placeholder()

        # Stop playback when window is closed
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_controls(self):
        # Clear placeholder
        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        # Generation and Playback Controls
        gen_play_frame = ttk.Frame(self.controls_frame)
        gen_play_frame.pack(side=tk.LEFT, padx=5)

        self.btn_generate_full_song = ttk.Button(gen_play_frame, text="Generate Full Song", command=self.generate_full_song_action)
        self.btn_generate_full_song.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_randomize_all = ttk.Button(gen_play_frame, text="Randomize All", command=self.randomize_all_action)
        self.btn_randomize_all.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_play_pause = ttk.Button(gen_play_frame, text="Play", command=self.toggle_play_pause, state=tk.DISABLED)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop = ttk.Button(gen_play_frame, text="Stop", command=self.stop_playback, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        # Mood selection (placeholder, will be improved)
        mood_frame = ttk.Frame(self.controls_frame)
        mood_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(mood_frame, text="Mood:").pack(side=tk.LEFT)
        self.mood_var = tk.StringVar(value="Happy")
        moods = ["Happy", "Sad", "Chill"]
        for mood in moods:
            rb = ttk.Radiobutton(mood_frame, text=mood, variable=self.mood_var, value=mood)
            rb.pack(side=tk.LEFT, padx=2)

        # BPM Control (placeholder)
        bpm_frame = ttk.Frame(self.controls_frame)
        bpm_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(bpm_frame, text="BPM:").pack(side=tk.LEFT)
        self.bpm_var = tk.IntVar(value=120)
        self.bpm_scale = ttk.Scale(bpm_frame, from_=60, to_=180, variable=self.bpm_var, orient=tk.HORIZONTAL, command=lambda v: self.bpm_var.set(int(float(v))))
        self.bpm_scale.pack(side=tk.LEFT, padx=5)
        self.lbl_bpm_value = ttk.Label(bpm_frame, text="120")
        self.lbl_bpm_value.pack(side=tk.LEFT)
        self.bpm_var.trace_add("write", lambda *args: self.lbl_bpm_value.config(text=str(self.bpm_var.get())))

        # Export Controls
        export_frame = ttk.Frame(self.controls_frame)
        export_frame.pack(side=tk.LEFT, padx=30)

        ttk.Label(export_frame, text="Export:").pack(side=tk.LEFT, pady=5)
        self.btn_export_midi = ttk.Button(export_frame, text="MIDI (.mid)", command=self.export_midi, state=tk.DISABLED)
        self.btn_export_midi.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_export_wav = ttk.Button(export_frame, text="WAV (.wav)", command=self.export_wav, state=tk.DISABLED)
        self.btn_export_wav.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_export_mp3 = ttk.Button(export_frame, text="MP3 (.mp3)", command=self.export_mp3, state=tk.DISABLED)
        self.btn_export_mp3.pack(side=tk.LEFT, padx=5, pady=5)


    def _setup_visualizer_placeholder(self):
        # Clear placeholder label if it exists
        for widget in self.visualizer_frame.winfo_children():
            widget.destroy()

        self.midi_canvas_width = 1000 # Initial width, can be dynamic
        self.midi_canvas_height = 400 # Initial height

        self.canvas_frame = ttk.Frame(self.visualizer_frame) # Frame to hold canvas and scrollbar
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.midi_canvas = tk.Canvas(self.canvas_frame, bg="#1E1E1E", scrollregion=(0, 0, self.midi_canvas_width, self.midi_canvas_height))

        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.midi_canvas.xview)
        self.midi_canvas.configure(xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.midi_canvas.yview)
        self.midi_canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.midi_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Define piano roll parameters
        self.note_height = 5  # Height of each note rectangle
        self.beats_per_pixel = 0.1 # How many beats one pixel represents horizontally (lower = more zoomed in)
        self.pixels_per_beat = 1.0 / self.beats_per_pixel # Higher = more space per beat

        # MIDI note range to display (e.g., C1 to C8 for a typical piano roll)
        self.min_display_midi = 24  # C1
        self.max_display_midi = 108 # C8
        self.num_display_notes = self.max_display_midi - self.min_display_midi + 1

        # Update canvas height based on note range
        self.midi_canvas_height = self.num_display_notes * self.note_height
        self.midi_canvas.config(scrollregion=(0, 0, self.midi_canvas_width, self.midi_canvas_height))

        # Colors for different tracks (can be expanded)
        self.track_colors = {
            "Melody": "#FF6B6B", "Harmony Line": "#FFD166", "Counter-Melody": "#06D6A0",
            "Bassline": "#118AB2", "Pads": "#7A4FBF", "Drums": "#8D8D8D", # Grey for drums
            "Default": "#CCCCCC"
        }
        self.playing_note_color = "#FFFFFF" # White for currently playing note highlight

        # Store drawn note items for updates (mapping event_id to canvas_item_id)
        self.drawn_note_items = {} # Using (track_name, event_index) as key
        self.playhead_line = None


    def draw_all_midi_notes(self):
        if not self.current_song_data:
            return

        self.midi_canvas.delete("all") # Clear previous drawing
        self.drawn_note_items = {}

        max_beat_time = 0
        if self.current_song_data and self.current_song_data.tracks:
            for track_name, events in self.current_song_data.tracks.items():
                for event in events:
                    event_end_time = event.time_start + event.duration
                    if event_end_time > max_beat_time:
                        max_beat_time = event_end_time

        # Update canvas width based on total song duration
        self.midi_canvas_width = int(max_beat_time * self.pixels_per_beat) + int(2 * self.pixels_per_beat) # Add some padding
        self.midi_canvas.config(scrollregion=(0, 0, self.midi_canvas_width, self.midi_canvas_height))


        for track_idx, (track_name, events) in enumerate(self.current_song_data.tracks.items()):
            color = self.track_colors.get(track_name, self.track_colors["Default"])
            for event_idx, event in enumerate(events):
                if event.type == 'note':
                    # Y position based on MIDI note value
                    # Higher MIDI note = lower Y on canvas (top is 0)
                    y_pos = (self.max_display_midi - event.note) * self.note_height

                    # X position based on time_start
                    x_start = event.time_start * self.pixels_per_beat

                    # Width based on duration
                    note_width = event.duration * self.pixels_per_beat

                    if self.min_display_midi <= event.note <= self.max_display_midi :
                        # Only draw notes within the displayable MIDI range
                        item_id = self.midi_canvas.create_rectangle(
                            x_start, y_pos,
                            x_start + note_width, y_pos + self.note_height,
                            fill=color, outline="#333333", tags=(track_name, f"note_{event_idx}")
                        )
                        self.drawn_note_items[(track_name, event_idx)] = item_id

        # Draw horizontal lines for note pitches (like a piano roll background)
        for i in range(self.num_display_notes):
            y = i * self.note_height
            line_color = "#303030" # Darker lines for C notes
            midi_val = self.max_display_midi - i
            if midi_val % 12 == music_theory.NOTES.index("C"): # C notes
                 line_color = "#454545"
            self.midi_canvas.create_line(0, y, self.midi_canvas_width, y, fill=line_color, tags="grid_line")

        # Draw vertical lines for beats/bars
        num_total_beats = int(max_beat_time) +1
        for beat in range(num_total_beats):
            x = beat * self.pixels_per_beat
            line_color = "#454545" # Bar lines
            if beat % song_generator.BAR_LENGTH_BEATS != 0:
                line_color = "#303030" # Beat lines
            self.midi_canvas.create_line(x, 0, x, self.midi_canvas_height, fill=line_color, tags="grid_line")
            if beat % song_generator.BAR_LENGTH_BEATS == 0: # Add bar numbers
                self.midi_canvas.create_text(x + 2, 10, text=str(beat // song_generator.BAR_LENGTH_BEATS + 1), fill="#777777", anchor=tk.NW, font=("Arial", 8))

        # Create playhead line (initially off-screen or at start)
        self.playhead_line = self.midi_canvas.create_line(0, 0, 0, self.midi_canvas_height, fill="red", width=2, tags="playhead")
        self.midi_canvas.tag_raise("playhead") # Ensure it's on top of notes


    def update_playhead(self, current_beat_time):
        if self.playhead_line:
            x_pos = current_beat_time * self.pixels_per_beat
            self.midi_canvas.coords(self.playhead_line, x_pos, 0, x_pos, self.midi_canvas_height)

            # Auto-scroll canvas to keep playhead in view
            # Scroll if playhead is near the right edge of the visible area
            visible_x_start = self.midi_canvas.canvasx(0)
            visible_x_end = self.midi_canvas.canvasx(self.midi_canvas.winfo_width())

            # If playhead is past 75% of the view, scroll
            if x_pos > visible_x_start + (visible_x_end - visible_x_start) * 0.75 :
                scroll_to_x = x_pos - (visible_x_end - visible_x_start) * 0.25 # Scroll to keep playhead at 25%
                self.midi_canvas.xview_moveto(scroll_to_x / self.midi_canvas_width if self.midi_canvas_width > 0 else 0)

            # Highlight playing notes (basic implementation)
            # This part needs to be efficient. Iterating all notes on every update is slow.
            # A better way is to get events around current_beat_time.
            # For now, a simple visual indication without per-note highlighting during playback loop.
            # Per-note highlighting will be added if performance allows or a better method is found.

    def _start_visualizer_update_loop(self):
        if self.is_playing and self.current_song_data:
            # Calculate current beat time based on sample position
            current_time_seconds = self.current_sample_pos / synthesizer.SAMPLE_RATE
            current_beat_time = (current_time_seconds * self.current_song_data.bpm) / 60.0

            self.update_playhead(current_beat_time)

            # Highlight notes that are currently "on"
            # This is a simplified approach. For precise highlighting, we'd track note on/off events.
            # We need to iterate through self.drawn_note_items and check their timing against current_beat_time

            active_notes_this_frame = [] # Store (track_name, event_idx) of active notes

            for (track_name, event_idx), item_id in self.drawn_note_items.items():
                try:
                    event = self.current_song_data.tracks[track_name][event_idx]
                    is_active = (event.time_start <= current_beat_time < (event.time_start + event.duration))

                    original_color = self.track_colors.get(track_name, self.track_colors["Default"])
                    current_color = self.midi_canvas.itemcget(item_id, "fill")

                    if is_active:
                        active_notes_this_frame.append((track_name, event_idx))
                        if current_color != self.playing_note_color:
                             self.midi_canvas.itemconfig(item_id, fill=self.playing_note_color)
                    else:
                        if current_color == self.playing_note_color: # Was highlighted, now turn off
                            self.midi_canvas.itemconfig(item_id, fill=original_color)

                except (IndexError, KeyError) as e:
                    # print(f"Error accessing event for highlighting: {track_name}, {event_idx} - {e}")
                    pass # Event might not exist if song structure changes, or bad index

            # Reset color for notes that were active last frame but not this one
            # This is covered by the else clause above now.

            self.root.after(30, self._start_visualizer_update_loop) # Approx 30 FPS update for playhead

    def _stop_visualizer_update_loop(self):
        # This function isn't strictly necessary if the loop self-terminates
        # when self.is_playing is False, but can be called explicitly.
        # The loop condition `if self.is_playing` handles stopping.
        # Reset all highlighted notes to original color when stopping playback
        if self.current_song_data and self.drawn_note_items:
             for (track_name, event_idx), item_id in self.drawn_note_items.items():
                original_color = self.track_colors.get(track_name, self.track_colors["Default"])
                self.midi_canvas.itemconfig(item_id, fill=original_color) # Reset color


    def _setup_structure_editor_placeholder(self):
        for widget in self.structure_editor_frame.winfo_children(): # Clear placeholder
            widget.destroy()

        ttk.Label(self.structure_editor_frame, text="Song Structure:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(0,10), pady=5)

        self.section_block_frames = [] # To hold references to frame for each block

        # Initial display based on template. Will be updated when a song is generated.
        # If a song is already loaded (e.g. app restarted with saved state later), use its structure
        if self.current_song_data and self.current_song_data.section_details:
            self.display_song_structure([details['name'] for details in self.current_song_data.section_details])
        else:
            self.display_song_structure(song_generator.SONG_STRUCTURE_TEMPLATE)


    def display_song_structure(self, structure_template):
        # Clear existing blocks first
        for frame in self.section_block_frames:
            frame.destroy() # This should destroy child labels too
        self.section_block_frames = []

        for i, section_name in enumerate(structure_template):
            # Using a tk.Frame for better background control with dark theme
            block_frame = tk.Frame(self.structure_editor_frame, relief=tk.RAISED, borderwidth=2, bg="#3C3C3C") # Darker block
            block_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=5) # expand + fill both

            # Make the label itself part of the clickable area and themed
            lbl = tk.Label(block_frame, text=section_name, bg="#3C3C3C", fg="#EAEAEA", font=("Arial", 10, "bold"), padx=10, pady=10)
            lbl.pack(expand=True, fill=tk.BOTH)

            # Store frame and section info for interaction
            block_frame.section_index = i # Keep 0-based index
            block_frame.section_name = section_name

            # Add click binding to both label and frame for better clickability
            lbl.bind("<Button-1>", lambda event, s_index=i, s_name=section_name: self.on_section_block_click(event, s_index, s_name))
            block_frame.bind("<Button-1>", lambda event, s_index=i, s_name=section_name: self.on_section_block_click(event, s_index, s_name))

            self.section_block_frames.append(block_frame)

    def on_section_block_click(self, event, section_index, section_name):
        if not self.current_song_data or section_index >= len(self.current_song_data.section_details):
            print(f"No song data or invalid section index for click: {section_index}")
            # Could offer to generate a song if none exists
            return

        print(f"Clicked section: Index {section_index}, Name: {section_name}")

        # Create a context menu
        menu = tk.Menu(self.root, tearoff=0, bg=self.style.lookup("TFrame", "background"), foreground=self.style.lookup("TLabel","foreground"))
        menu.add_command(label=f"Regenerate '{section_name}'", command=lambda: self.regenerate_section_action(section_index))

        menu.add_separator()
        menu.add_command(label="Mute/Solo Track (Song-wide WIP)", state=tk.DISABLED) # Placeholder for future

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def regenerate_section_action(self, section_index_to_regenerate):
        if not self.current_song_data or section_index_to_regenerate >= len(self.current_song_data.section_details):
            print("Cannot regenerate: No song data or invalid section index.")
            return

        section_to_regen_name = self.current_song_data.section_details[section_index_to_regenerate]['name']
        print(f"Regenerating section {section_index_to_regenerate}: {section_to_regen_name}")

        if self.is_playing:
            self.stop_playback()
            sd.wait(timeout=100)

        try:
            # This method needs to be added to song_generator.py
            self.current_song_data = song_generator.regenerate_specific_section(
                self.current_song_data,
                section_index_to_regenerate,
                song_generator.CHANNEL_MAP
            )
        except AttributeError:
            print("Error: `song_generator.regenerate_specific_section` not yet implemented.")
            tk.messagebox.showerror("Error", "Section regeneration function is not available in song_generator.py.")
            return
        except Exception as e:
            print(f"Error during section regeneration call: {e}")
            tk.messagebox.showerror("Error", f"An error occurred during section regeneration: {e}")
            return

        print(f"Section {section_index_to_regenerate} ({section_to_regen_name}) events regenerated by song_generator.")
        print("Re-rendering audio and updating visualizer...")
        self.current_audio_data = synthesizer.render_song_to_audio(
            self.current_song_data,
            sample_rate=synthesizer.SAMPLE_RATE
        )
        self.draw_all_midi_notes()

        can_play = self.current_audio_data is not None and len(self.current_audio_data) > 0
        self.btn_play_pause.config(state=tk.NORMAL if can_play else tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL if can_play else tk.DISABLED)
        self._update_export_buttons_state() # Update export button states after section regen

        print(f"Section {section_index_to_regenerate} regenerated and audio/visuals updated.")

    def generate_full_song_action(self, mood=None, bpm=None, key_root_name="C", key_octave=4, auto_play=True):
        """
        Core action for generating a song. Can be called by "Generate Full Song"
        or "Randomize All" buttons.
        If mood or bpm are None, they are taken from UI controls.
        """
        original_button_text_gen = self.btn_generate_full_song.cget("text")
        original_button_text_rand = self.btn_randomize_all.cget("text")
        self.btn_generate_full_song.config(state=tk.DISABLED, text="Generating...")
        self.btn_randomize_all.config(state=tk.DISABLED, text="Generating...")
        self.root.update_idletasks()

        if self.playback_stream and self.is_playing:
            self.stop_playback()
            sd.wait()

        selected_mood = mood if mood is not None else self.mood_var.get()
        selected_bpm = bpm if bpm is not None else self.bpm_var.get()

        # Update UI if parameters were chosen randomly
        if mood is not None: self.mood_var.set(selected_mood)
        if bpm is not None: self.bpm_var.set(selected_bpm)

        print(f"Generating song: Mood={selected_mood}, BPM={selected_bpm}, Key={key_root_name}{key_octave}")
        self.current_song_data = song_generator.generate_full_song(
            mood=selected_mood,
            key_root_name=key_root_name,
            key_octave=key_octave,
            bpm=selected_bpm
        )
        print("Song generation complete. Rendering to audio...")
        self.current_audio_data = synthesizer.render_song_to_audio(
            self.current_song_data,
            sample_rate=synthesizer.SAMPLE_RATE
        )
        print(f"Audio rendering complete. Shape: {self.current_audio_data.shape}")

        self.draw_all_midi_notes()
        if self.current_song_data and self.current_song_data.section_details: # Update structure display
            self.display_song_structure([details['name'] for details in self.current_song_data.section_details])


        self.btn_generate_full_song.config(state=tk.NORMAL, text=original_button_text_gen)
        self.btn_randomize_all.config(state=tk.NORMAL, text=original_button_text_rand)

        if self.current_audio_data is not None and len(self.current_audio_data) > 0:
            self.btn_play_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            if auto_play:
                self.play_audio()
        else:
            print("No audio data generated.")
            self.btn_play_pause.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.DISABLED)
        self._update_export_buttons_state() # Update export button states after main generation

    def randomize_all_action(self):
        random_mood = random.choice(["Happy", "Sad", "Chill"])

        # Get BPM range from the scale widget if possible, else default
        min_bpm = 60
        max_bpm = 180
        try:
            min_bpm = int(self.bpm_scale.cget("from"))
            max_bpm = int(self.bpm_scale.cget("to"))
        except: # In case scale not fully initialized or attributes not standard
            pass
        random_bpm = random.randint(min_bpm, max_bpm)

        # For now, key is still C4. Key randomization can be added.
        # random_key_root_name = random.choice(music_theory.NOTES)
        # random_key_octave = random.choice([3, 4, 5])

        self.generate_full_song_action(mood=random_mood, bpm=random_bpm, auto_play=True)

    # def generate_and_play_song(self): # This is the original method name, now refactored into generate_full_song_action
    #     self.btn_generate_full_song.config(state=tk.DISABLED, text="Generating...") # Corrected button name
    #     self.root.update_idletasks() # Update GUI before blocking task

    #     # Stop any existing playback before generating a new song
        if self.playback_stream and self.is_playing:
            self.stop_playback()
            # Wait for stream to properly stop if it was playing in a thread
            # This might need more robust handling like joining the thread or using events
            sd.wait()

        selected_mood = self.mood_var.get()
        selected_bpm = self.bpm_var.get()
        # Key selection will be added later, default C4 for now

        print(f"Generating song: Mood={selected_mood}, BPM={selected_bpm}")
        self.current_song_data = song_generator.generate_full_song(
            mood=selected_mood,
            key_root_name="C", # Default for now
            key_octave=4,      # Default for now
            bpm=selected_bpm
        )
        print("Song generation complete. Rendering to audio...")
        self.current_audio_data = synthesizer.render_song_to_audio(
            self.current_song_data,
            sample_rate=synthesizer.SAMPLE_RATE
        )
        print(f"Audio rendering complete. Shape: {self.current_audio_data.shape}")

        self.draw_all_midi_notes() # Draw the notes on the canvas

        self.btn_generate_play.config(state=tk.NORMAL, text="Generate & Play")

        if self.current_audio_data is not None and len(self.current_audio_data) > 0:
            self.btn_play_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.play_audio() # Auto-play after generation
        else:
            print("No audio data generated.")
            self.btn_play_pause.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.DISABLED)

    def play_audio(self):
        if self.current_audio_data is None or len(self.current_audio_data) == 0:
            print("No audio data to play.")
            return

        if self.playback_stream and self.is_playing: # Already playing
            return

        try:
            print(f"Attempting to play audio. Sample rate: {synthesizer.SAMPLE_RATE}, Channels: 1 (mono)")

            # Ensure any previous stream is closed before starting a new one
            if self.playback_stream:
                self.playback_stream.stop(ignore_errors=True)
                self.playback_stream.close(ignore_errors=True)
                self.playback_stream = None

            self.playback_stream = sd.OutputStream(
                samplerate=synthesizer.SAMPLE_RATE,
                channels=2, # Stereo audio now
                dtype='float32',
                callback=self._audio_callback
            )
            self.current_sample_pos = 0 # Reset position for new playback
            self.playback_stream.start()
            self.is_playing = True
            self.btn_play_pause.config(text="Pause")
            print("Playback started.")
            self._start_visualizer_update_loop() # Start visualizer updates
        except Exception as e:
            print(f"Error starting playback: {e}")
            self.is_playing = False
            if self.playback_stream:
                self.playback_stream.stop(ignore_errors=True)
                self.playback_stream.close(ignore_errors=True)
                self.playback_stream = None
            self.btn_play_pause.config(text="Play", state=tk.NORMAL if self.current_audio_data is not None else tk.DISABLED)


    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(status, flush=True) # Print any errors from sounddevice

        if self.current_audio_data is None or not self.is_playing:
            outdata[:] = 0 # Output silence
            # If playback is stopped externally, this might not be enough to stop the stream immediately
            # Raising sd.CallbackStop() is cleaner
            if not self.is_playing and self.playback_stream: # Ensure this check is robust
                 print("Callback: Playback stopped, raising CallbackStop.")
                 raise sd.CallbackStop
            return

        chunk_end = self.current_sample_pos + frames
        if chunk_end > self.current_audio_data.shape[0]: # current_audio_data is now stereo (N, 2)
            # Reached end of audio data
            remaining_frames = self.current_audio_data.shape[0] - self.current_sample_pos
            if remaining_frames > 0:
                outdata[:remaining_frames] = self.current_audio_data[self.current_sample_pos : self.current_sample_pos + remaining_frames]
            if frames > remaining_frames: # If outdata is larger than remaining audio
                 outdata[remaining_frames:] = 0 # Fill rest with silence

            self.current_sample_pos += remaining_frames # Move to end

            self.root.after(0, self._playback_finished)
            raise sd.CallbackStop
        else:
            outdata[:] = self.current_audio_data[self.current_sample_pos : chunk_end]
            self.current_sample_pos = chunk_end


    def _playback_finished(self):
        """Called when audio naturally reaches its end or is stopped."""
        print("Playback finished or stopped.")
        self.is_playing = False
        if self.playback_stream:
            # Stream should already be stopped by CallbackStop or explicit stop command
            # self.playback_stream.stop(ignore_errors=True)
            # self.playback_stream.close(ignore_errors=True)
            # self.playback_stream = None # Cleared by stop_playback or play_audio
            pass

        self.btn_play_pause.config(text="Play")
        # Do not disable stop button if audio is loaded, allow re-play
        # self.btn_stop.config(state=tk.DISABLED)
        self.current_sample_pos = 0 # Reset for next play
        self.update_playhead(0) # Reset playhead to start visually
        self._stop_visualizer_update_loop() # Ensure notes are de-highlighted

    def toggle_play_pause(self):
        if self.current_audio_data is None: return

        if self.is_playing: # Pause
            if self.playback_stream:
                self.playback_stream.stop() # Stops calling the callback
                # Don't close it, so we can resume
            self.is_playing = False # This will stop the _start_visualizer_update_loop
            self.btn_play_pause.config(text="Play")
            # No need to call _stop_visualizer_update_loop here, as notes should remain as they are when paused
            print("Playback paused.")
        else: # Play (or Resume)
            if self.playback_stream and not self.playback_stream.active: # Resuming a paused stream
                try:
                    # self.current_sample_pos is maintained from where it paused
                    self.playback_stream.start()
                    self.is_playing = True
                    self.btn_play_pause.config(text="Pause")
                    self._start_visualizer_update_loop() # Restart visualizer updates
                    print("Playback resumed.")
                except Exception as e:
                    print(f"Error resuming playback: {e}. Re-initializing stream.")
                    # If stream can't be resumed (e.g., closed due to system event), re-init
                    self.play_audio()
            else: # Start new playback (e.g. if stopped or first play)
                 self.play_audio()


    def stop_playback(self):
        print("Stop playback requested.")
        if self.playback_stream:
            self.is_playing = False # Signal callback to stop producing data
            self.playback_stream.stop(ignore_errors=True)
            self.playback_stream.close(ignore_errors=True)
            self.playback_stream = None
            print("Playback stream stopped and closed.")

        # Call _playback_finished directly to update UI state
        # Use root.after to ensure it runs in the main GUI thread
        self.root.after(0, self._playback_finished)


    def _on_closing(self):
        print("Application closing...")
        self.stop_playback()
        # Wait for sounddevice to clean up if necessary
        # sd.wait(timeout=100) # Timeout in ms, may not be needed if stream closed properly
        self.root.destroy()

    def _update_export_buttons_state(self):
        """Enable export buttons if song data and audio data exist."""
        has_song_data = self.current_song_data is not None
        has_audio_data = self.current_audio_data is not None and len(self.current_audio_data) > 0

        self.btn_export_midi.config(state=tk.NORMAL if has_song_data else tk.DISABLED)
        self.btn_export_wav.config(state=tk.NORMAL if has_audio_data else tk.DISABLED)
        self.btn_export_mp3.config(state=tk.NORMAL if has_audio_data else tk.DISABLED)


    def export_midi(self):
        if not self.current_song_data:
            tk.messagebox.showwarning("Export Error", "No song data to export. Please generate a song first.")
            return

        filepath = tk.filedialog.asksaveasfilename(
            defaultextension=".mid",
            filetypes=[("MIDI Files", "*.mid"), ("All Files", "*.*")],
            title="Save MIDI File"
        )
        if not filepath: return # User cancelled

        try:
            exporter.save_midi_file(self.current_song_data, filepath)
            tk.messagebox.showinfo("Export Successful", f"MIDI file saved to:\n{filepath}")
        except Exception as e:
            tk.messagebox.showerror("Export Error", f"Failed to export MIDI: {e}")


    def export_wav(self):
        if self.current_audio_data is None or len(self.current_audio_data) == 0:
            tk.messagebox.showwarning("Export Error", "No audio data to export. Please generate and render a song first.")
            return

        filepath = tk.filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV Files", "*.wav"), ("All Files", "*.*")],
            title="Save WAV File"
        )
        if not filepath: return

        try:
            exporter.save_wav_file(self.current_audio_data, filepath, synthesizer.SAMPLE_RATE)
            tk.messagebox.showinfo("Export Successful", f"WAV file saved to:\n{filepath}")
        except Exception as e:
            tk.messagebox.showerror("Export Error", f"Failed to export WAV: {e}")


    def export_mp3(self):
        if self.current_audio_data is None or len(self.current_audio_data) == 0:
            tk.messagebox.showwarning("Export Error", "No audio data to export. Please generate and render a song first.")
            return

        filepath = tk.filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")],
            title="Save MP3 File"
        )
        if not filepath: return

        try:
            exporter.save_mp3_file(self.current_audio_data, filepath, synthesizer.SAMPLE_RATE)
            tk.messagebox.showinfo("Export Successful", f"MP3 file saved to:\n{filepath}")
        except RuntimeError as e: # Catch specific RuntimeError from pydub for ffmpeg issue
            tk.messagebox.showerror("Export Error", str(e)) # Show the detailed message from exporter
        except Exception as e:
            tk.messagebox.showerror("Export Error", f"Failed to export MP3: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    # filedialog and messagebox are now imported at the top
    app = ProceduralSongGeneratorApp(root)
    root.mainloop()
