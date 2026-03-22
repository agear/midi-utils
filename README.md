# midi-utils

A MIDI stem extraction utility that reads multitrack MIDI files and separates each instrument or program into its own MIDI file. Optionally renders each stem to WAV audio using a General MIDI soundfont. Includes a FastAPI web UI for drag-and-drop batch processing.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Setup](#setup)
  - [Clone the repository](#1-clone-the-repository)
  - [Create a virtual environment](#2-create-a-virtual-environment)
  - [Install dependencies](#3-install-dependencies)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI](#cli)
  - [Web UI](#web-ui)
- [Output structure](#output-structure)
- [Running the test suite](#running-the-test-suite)
- [Architecture](#architecture)

---

## Overview

Given a multitrack MIDI file (e.g. a Guitar Pro export), midi-utils:

1. Identifies each instrument track and program change within it.
2. Writes a separate `.mid` file per instrument — a "stem" — preserving the original transport/tempo track.
3. For drum tracks (MIDI channel 9), writes an additional per-percussion-instrument stem inside a subdirectory.
4. Optionally renders every stem to `.wav` using a bundled General MIDI soundfont.

A single-page web UI (FastAPI + vanilla JS) provides drag-and-drop upload and per-stem download links as an alternative to the CLI.

---

## Requirements

- Python **3.8**
- `git` (the `midi` dependency is installed directly from GitHub)
- A General MIDI soundfont (a bundled `soundfonts/gm.sf2` is included in the repository)

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd midi-utils
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> On Windows use `.venv\Scripts\activate` instead.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The `midi` library is pulled directly from GitHub (Python 3 fork) and the rest of the packages are pinned in `requirements.txt`.

To install `pytest` and `pytest-cov` for running the test suite:

```bash
pip install pytest pytest-cov
```

---

## Configuration

All configuration lives in **`config.py`**. Edit this file before running the CLI:

```python
# config.py

convert_to_wav: bool = True          # Set False to skip WAV rendering

soundfont_path: str = "/path/to/your/soundfont.sf2"
# A bundled soundfont is included:
# soundfont_path = "soundfonts/gm.sf2"

output_path: str = "/path/to/output/directory"
# Stems are written under: <output_path>/<song name> Stems/

midi_file_paths: list = [
    "/path/to/Song1.mid",
    "/path/to/Song2.mid",
]
```

| Variable | Description |
|---|---|
| `convert_to_wav` | Whether to render each MIDI stem to WAV using the soundfont |
| `soundfont_path` | Absolute path to a `.sf2` General MIDI soundfont |
| `output_path` | Root directory where stem folders are created |
| `midi_file_paths` | List of MIDI files to process |

The repository includes a bundled General MIDI soundfont at `soundfonts/gm.sf2`, so no external soundfont download is required.

---

## Usage

### CLI

After editing `config.py`:

```bash
python main.py
```

This processes every path in `midi_file_paths` sequentially and prints progress to stdout.

### Web UI

Start the development server from the repository root:

```bash
uvicorn api.main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

**Flow:**
1. Drag and drop one or more `.mid` files onto the upload area (or click to browse).
2. Configure extraction settings in the form.
3. Click **Extract**. The page displays a download link for each stem once processing completes.

Uploaded files and job outputs are held in memory and are lost on server restart — this is intentional for a local dev tool.

---

## Output structure

For a file `MySong.mid` with `output_path = "/Volumes/Stems"`:

```
/Volumes/Stems/MySong Stems/
  midi_stems/
    MySong - 01 - 0 - Acoustic Grand.mid
    MySong - 02 - 32 - Acoustic Bass.mid
    MySong - 03 - 0 - Drum Kit 0/          ← drum subdirectory
      MySong - 03 - 0 - Drum Kit 0 - 36 - Bass Drum 1.mid
      MySong - 03 - 0 - Drum Kit 0 - 38 - Acoustic Snare.mid
  audio_stems/                             ← only if convert_to_wav=True
    MySong - All.wav
    MySong - 01 - 0 - Acoustic Grand.wav
    MySong - 02 - 32 - Acoustic Bass.wav
```

---

## Running the test suite

The test suite requires no real MIDI files — all MIDI data is built programmatically in the fixtures.

**Run all tests:**

```bash
pytest test/
```

**Run with coverage:**

```bash
pytest test/ --cov=. --cov-report=term-missing --ignore=.venv
```

**Run a single test file:**

```bash
pytest test/test_controller.py
```

**Run a single test:**

```bash
pytest test/test_controller.py::TestGetTrackNames::test_single_program_change
```

### Test files

| File | What it covers |
|---|---|
| `test/test_program.py` | `Program` — init, property setter, all 128 program names |
| `test/test_percussion_instrument.py` | `Percussion_Instrument` — init, equality, hashing, set usage |
| `test/test_midi_event.py` | `Encapsulated_Midi_Event` — program resolution, drum channel, meta events, str/repr |
| `test/test_encapsulated_midi_track.py` | `Encapsulated_Midi_Track` — event encapsulation, program tracking, drum detection, muting, file output |
| `test/test_controller.py` | `Controller` — init, directories, transport detection, stem extraction |
| `test/test_main.py` | `main()` — file validation, stem output |
| `test/conftest.py` | Shared fixtures and synthetic MIDI pattern factories |

### Coverage summary

| Module | Coverage |
|---|---|
| `encapsulated_midi_event.py` | 100% |
| `percussion_instrument.py` | 100% |
| `program.py` | 100% |
| `programs.py` | 100% |
| `config.py` | 100% |
| `encapsulated_midi_track.py` | 97% |
| `controller.py` | 88% |
| `main.py` | 72% |

---

## Architecture

```
main.py          Entry point; validates paths, creates Controller, calls extract/convert
controller.py    Per-file orchestrator; reads MIDI, identifies tracks, writes stems
encapsulated_midi_track.py   Wraps one MIDI track; groups events by program; writes .mid files
encapsulated_midi_event.py   Wraps one MIDI event with its resolved program name
program.py       Validated GM program (0–127) with name lookup
percussion_instrument.py     Validated GM percussion instrument with name lookup
programs.py      PROGRAMS dict (0–127 → name) and PERCUSSION dict (27–81 → name)
config.py        Machine-specific paths and flags (edit before use)

api/
  main.py        FastAPI app: /upload, /extract, /download/{job_id}
  schemas.py     Pydantic request/response models

static/
  index.html     Single-page UI
  app.js         Frontend fetch calls and stem download links
```

### Data flow

```
main.py
  └─ Controller.__init__()          load MIDI file, create directories
  └─ Controller.extract_midi_stems()
       └─ _get_transport_track()    find the timing/tempo track
       └─ Encapsulated_Midi_Track() per non-transport track
            └─ encapsulate_midi_events()   tag each event with its program
            └─ _is_drum_track()            detect channel-9 tracks
            └─ extract_programs()          build per-program MIDI patterns
            └─ write()                     save .mid files to midi_stems/
  └─ Controller.convert_to_wav()    render each .mid to .wav via sf2_loader
```
