# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the web UI (from the repo root):**
```bash
uvicorn api.main:app --reload
```
Then open http://localhost:8000.

**Run the CLI script directly:**
```bash
python main.py
```

**Run all tests:**
```bash
pytest test/
```

**Run a single test file:**
```bash
pytest test/test_encapsulated_midi_track.py
```

**Run a single test:**
```bash
pytest test/test_controller.py::TestController::test_init
```

## Architecture

This is a MIDI stem extraction utility. It reads multitrack MIDI files, separates each instrument/program into its own MIDI file (stem), and optionally converts those stems to WAV audio using a soundfont.

### Data flow

`main.py` → `Controller` → `Encapsulated_Midi_Track` → `Encapsulated_Midi_Event`

1. `config.py` holds the list of MIDI files to process, the soundfont path, and whether to convert to WAV.
2. `Controller` (controller.py) is instantiated per MIDI file. It reads the file, identifies tracks, and calls `extract_midi_stems()` to write per-instrument MIDI files. If `convert_to_wav` is enabled, it converts each stem using a soundfont.
3. `Encapsulated_Midi_Track` (encapsulated_midi_track.py) wraps a raw MIDI track. It groups events by program number, handles drum tracks (channel 9), formats output filenames, and writes per-instrument MIDI patterns.
4. `Encapsulated_Midi_Event` (encapsulated_midi_event.py) wraps a single MIDI event with its resolved program name. It handles the special case of drum events on channel 9 and meta events (EndOfTrack, SetTempo, etc.) that don't have a program.

### Reference data

- `programs.py`: `PROGRAMS` dict (0–127 → instrument name) and `PERCUSSION` dict (drum instrument mappings).
- `program.py`: `Program` class with validation (number 0–127).
- `percussion_instrument.py`: `Percussion_Instrument` class with validation against the `PERCUSSION` dict.

### Output structure

For a file `MySong.mid` processed with `base_path = "/Volumes/AGM/Stems"`:
```
/Volumes/AGM/Stems/MySong/
  midi_stems/    ← per-instrument .mid files
  audio_stems/   ← per-instrument .wav files (if convert_to_wav=True)
```

### Hardcoded paths

`config.py` contains machine-specific paths (`soundfont_path`, `base_path`, `midi_file_paths`). These are not parameterized and must be edited directly for each environment.

## Web UI

```
api/
  main.py      ← FastAPI app: /upload, /extract, /download/{job_id}
  schemas.py   ← Pydantic models for request/response
static/
  index.html   ← Single-page UI (drag-drop upload, settings form, results list)
  app.js       ← Frontend: fetch calls to API, renders stem download links
```

**Flow:** browser uploads `.mid` → `/upload` returns `file_id` → `/extract` runs `Controller`, copies output to `base_path`, returns stem list → each stem has a `/download/{job_id}?path=…` link.

Uploaded files and job outputs are stored in-memory (`_uploaded_files`, `_job_outputs` dicts in `api/main.py`). They are lost on server restart — this is intentional for a local dev tool.
