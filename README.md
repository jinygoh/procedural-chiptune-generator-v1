# Procedural Chiptune Song Generator

This application allows users to generate musically coherent, full-length chiptune songs with a single click, and then offer tools to tweak and export the result.

## A) Setup Instructions

### Prerequisites

*   **Python**: Version 3.11 or newer is recommended.
*   **pip**: Python package installer (usually comes with Python).
*   **FFmpeg (for MP3 export)**: To export songs in MP3 format, you need to have FFmpeg installed on your system and accessible in your system's PATH.
    *   Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add the `bin` directory to your PATH.
    *   macOS (using Homebrew): `brew install ffmpeg`
    *   Linux (using apt): `sudo apt update && sudo apt install ffmpeg`

### Required Python Libraries

The application relies on the following Python libraries:

*   `numpy`: For numerical operations, especially audio data manipulation.
*   `sounddevice`: For audio playback.
*   `scipy`: For signal processing (e.g., EQ filters, WAV export).
*   `mido`: For MIDI file processing (export).
*   `pydub`: For audio manipulation and MP3 export.
*   `tkinter`: (Standard library) For the graphical user interface.

### Installation

1.  **Clone the repository or download the source code.**
    (Assuming the code is already available in a directory)

2.  **Navigate to the project directory** in your terminal:
    ```bash
    cd path/to/procedural-song-generator
    ```

3.  **Install dependencies** using pip and the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

Once the dependencies are installed, you can run the application from the project directory using:

```bash
python main.py
```

## B) How to Use (User Guide)

### Main Workflow

The primary way to use the Procedural Song Generator is straightforward:

1.  **(Optional) Select a Mood**: Choose a mood ("Happy," "Sad," or "Chill") using the radio buttons. This will influence the musical key, tempo range, and other generative parameters.
2.  **(Optional) Adjust BPM**: Use the BPM (Beats Per Minute) slider to set your desired tempo.
3.  **Generate Song**:
    *   Click the **"Generate Full Song"** button to create a new song based on the current Mood and BPM settings (defaults to C Major if no specific key selection UI is present yet).
    *   Alternatively, click the **"Randomize All"** button to generate a song with a randomly selected mood and BPM.
4.  **Play/Listen**:
    *   The song will usually auto-play after generation.
    *   Use the **"Play" / "Pause"** button to control playback.
    *   Use the **"Stop"** button to halt playback and return the playhead to the beginning.

### UI Controls and Features

*   **Mood Selection Buttons** (`Happy`, `Sad`, `Chill`):
    *   Determines the overall musical character.
    *   `Happy`: Major key, faster tempo, rhythmically active.
    *   `Sad`: Minor key, slower tempo, simpler melodies.
    *   `Chill`: Major or Minor key, relaxed tempo, syncopated drums, prominent pads.

*   **BPM (Tempo) Slider**:
    *   Adjusts the speed of the song in Beats Per Minute. The current BPM value is displayed next to the slider.

*   **"Generate Full Song" Button**:
    *   Generates a complete song based on the selected Mood and BPM. The song structure is fixed: Chorus - Verse - Chorus - Verse - Chorus - Bridge - Chorus.

*   **"Randomize All" Button**:
    *   Generates a complete song with a randomly chosen Mood and BPM.

*   **Playback Controls**:
    *   **"Play" / "Pause" Button**: Starts playback of the generated song from the current playhead position, or pauses if already playing.
    *   **"Stop" Button**: Stops playback and resets the playhead to the beginning of the song.

*   **MIDI Visualizer (Central Panel)**:
    *   Displays all generated notes in a piano-roll style.
    *   Notes are color-coded by instrument/layer.
    *   A red playhead line moves across the visualizer in sync with audio playback.
    *   Notes light up (turn white) as they are played.
    *   You can scroll horizontally and vertically to view different parts of the song.

*   **Song Structure Editor (Bottom Panel)**:
    *   Displays the song's sections (e.g., "Chorus," "Verse") as clickable blocks.
    *   **Clicking a section block** opens a context menu with options:
        *   **"Regenerate '[Section Name]'"**: Re-runs the generation algorithm for only that specific section, creating new musical content while keeping the rest of the song intact. The song's audio and visualizer will update.
        *   `Mute/Solo Track (Song-wide WIP)`: Placeholder for future mute/solo functionality for entire instrument tracks.

*   **Export Buttons**:
    *   These buttons become active after a song has been generated.
    *   **"MIDI (.mid)"**: Exports the entire song as a Standard MIDI File. Each instrument layer (Melody, Bassline, Drums, etc.) is saved as a separate track within the MIDI file.
    *   **"WAV (.wav)"**: Exports the full song mix as a high-quality, uncompressed WAV audio file (float32 format).
    *   **"MP3 (.mp3)"**: Exports the full song mix as a compressed MP3 audio file (typically 192kbps bitrate). *Note: This requires FFmpeg to be installed and accessible on your system.*

### Tips
*   If MP3 export fails, ensure FFmpeg is correctly installed and added to your system's PATH.
*   Experiment with different Mood and BPM combinations to explore various musical outputs.
*   Use the "Regenerate Section" feature if you like most of the song but want to try a different variation for a particular part (e.g., a new Chorus).

---
Enjoy creating your chiptunes!
