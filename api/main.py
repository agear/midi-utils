"""
FastAPI backend for the MIDI stem extraction utility.

Run with:
    uvicorn api.main:app --port 8001
from the midi-utils root directory.
"""
import io
import logging
import os
import sys
import time
import uuid
import threading
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Ensure the project root is on the path so existing modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from controller import Controller          # noqa: E402
from api.schemas import ExtractRequest, StemFile  # noqa: E402

app = FastAPI(title="MIDI Stem Extractor")

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "midi-utils.log")
_LOG_FMT  = "%(asctime)s [WEB] %(levelname)-8s %(name)s: %(message)s"


@app.on_event("startup")
def _setup_logging() -> None:
    """Attach a file handler to the root logger after uvicorn has set up its own handlers."""
    root = logging.getLogger()
    # Guard against duplicate handlers on --reload
    if any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == _LOG_PATH
           for h in root.handlers):
        return
    fh = logging.FileHandler(_LOG_PATH, mode="a", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(_LOG_FMT))
    root.addHandler(fh)
    root.setLevel(logging.INFO)
    logging.info("=" * 72)
    logging.info("Web UI started")

_DEFAULT_SOUNDFONT_ID = "default"
_DEFAULT_SOUNDFONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "soundfonts", "gm.sf2"
)

# sf_id -> {"name": str, "path": str, "is_default": bool}
_soundfonts: Dict[str, dict] = {
    _DEFAULT_SOUNDFONT_ID: {
        "name": "GM (built-in)",
        "path": _DEFAULT_SOUNDFONT_PATH,
        "is_default": True,
    }
}

# file_id  -> absolute path on disk
_uploaded_files: Dict[str, str] = {}

# job_id -> {"progress": int, "message": str, "done": bool,
#             "error": str|None, "song_name": str, "stems": list}
_job_status: Dict[str, dict] = {}

# job_id -> output directory (stable, under the user's output_path)
_job_outputs: Dict[str, str] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _watch_stems(job_id: str, stems_root: str) -> None:
    """Poll stems_root for new files and append them to live_stems as they appear."""
    seen: set = set()
    extra_passes = 0  # keep scanning briefly after job finishes to catch last writes

    while extra_passes < 3:
        if os.path.isdir(stems_root):
            for root, _, files in os.walk(stems_root):
                for fname in sorted(files):
                    full = os.path.join(root, fname)
                    rel  = os.path.relpath(full, stems_root)
                    if rel not in seen:
                        seen.add(rel)
                        _job_status[job_id]["live_stems"].append({
                            "name":   fname,
                            "path":   rel,
                            "is_wav": fname.lower().endswith(".wav"),
                        })
        if _job_status[job_id].get("done"):
            extra_passes += 1
        time.sleep(0.2)


def _update(job_id: str, progress: int, message: str) -> None:
    s = _job_status[job_id]
    s["progress"] = progress
    s["message"] = message
    if progress >= 100:
        s["done"] = True


def _safe_path(output_dir: str, rel: str) -> Optional[str]:
    """Return the absolute path only if it stays inside output_dir."""
    full = os.path.normpath(os.path.join(output_dir, rel))
    if full.startswith(os.path.normpath(output_dir) + os.sep) or \
       full == os.path.normpath(output_dir):
        return full
    return None


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_midi(file: UploadFile = File(...)):
    """Accept a .mid file, persist it to a temp location, return a file_id."""
    if not file.filename.lower().endswith(".mid"):
        raise HTTPException(status_code=400, detail="Only .mid files are accepted.")

    import tempfile
    file_id = str(uuid.uuid4())
    tmp_dir = tempfile.mkdtemp(prefix="midi_upload_")
    dest = os.path.join(tmp_dir, file.filename)

    with open(dest, "wb") as f:
        f.write(await file.read())

    _uploaded_files[file_id] = dest
    return {"file_id": file_id, "filename": file.filename}


# ---------------------------------------------------------------------------
# Soundfonts
# ---------------------------------------------------------------------------

@app.get("/soundfonts")
def list_soundfonts():
    """Return all registered soundfonts."""
    return [
        {"id": sf_id, "name": entry["name"], "is_default": entry["is_default"]}
        for sf_id, entry in _soundfonts.items()
    ]


@app.post("/soundfonts/upload")
async def upload_soundfont(file: UploadFile = File(...)):
    """Accept a .sf2 file, persist it, and register it as a selectable soundfont."""
    if not file.filename.lower().endswith(".sf2"):
        raise HTTPException(status_code=400, detail="Only .sf2 files are accepted.")

    import tempfile
    sf_id = str(uuid.uuid4())
    tmp_dir = tempfile.mkdtemp(prefix="midi_sf_")
    dest = os.path.join(tmp_dir, file.filename)

    with open(dest, "wb") as f:
        f.write(await file.read())

    name = os.path.splitext(file.filename)[0]
    _soundfonts[sf_id] = {"name": name, "path": dest, "is_default": False}
    return {"id": sf_id, "name": name}


# ---------------------------------------------------------------------------
# Extract  (starts a background thread, returns job_id immediately)
# ---------------------------------------------------------------------------

def _extraction_worker(job_id: str, midi_path: str, req: ExtractRequest) -> None:
    status = _job_status[job_id]
    job_start = time.perf_counter()
    try:
        sf_id = req.soundfont_id or _DEFAULT_SOUNDFONT_ID
        sf_entry = _soundfonts.get(sf_id)
        if not sf_entry:
            raise ValueError(f"Soundfont '{sf_id}' not found.")
        soundfont_path = sf_entry["path"]

        _update(job_id, 10, "Initializing controller…")
        controller = Controller(
            midi_file_path=midi_path,
            soundfont_path=soundfont_path,
            convert_to_wav=req.convert_to_wav,
            output_path=None,
        )

        # Start directory watcher so stems appear in the UI as they're written
        threading.Thread(
            target=_watch_stems,
            args=(job_id, controller.stems_path),
            daemon=True,
        ).start()

        _update(job_id, 35, "Extracting MIDI stems…")
        controller.extract_midi_stems()

        if req.convert_to_wav:
            _update(job_id, 65, "Converting stems to WAV…")
            controller.convert_to_wav(path=controller.midi_stem_path)

        _update(job_id, 88, "Collecting output files…")

        song_name = Path(midi_path).stem
        stems_root = os.path.join(os.path.dirname(midi_path), f"{song_name} Stems")

        if not os.path.isdir(stems_root):
            raise RuntimeError("Extraction ran but output directory was not found.")

        _job_outputs[job_id] = stems_root

        import wave as _wave
        stems = []
        for root, _, files in os.walk(stems_root):
            for fname in sorted(files):
                full = os.path.join(root, fname)
                rel  = os.path.relpath(full, stems_root)
                duration = None
                if fname.lower().endswith(".wav"):
                    try:
                        with _wave.open(full, "r") as wf:
                            duration = wf.getnframes() / wf.getframerate()
                    except Exception:
                        pass
                stems.append(StemFile(
                    name=fname,
                    path=rel,
                    is_wav=fname.lower().endswith(".wav"),
                    duration_seconds=duration,
                ).model_dump())

        status["stems"] = stems
        status["song_name"] = song_name
        _update(job_id, 100, "Done!")
        logging.getLogger(__name__).info(
            "Job %s (%s) completed in %.2fs", job_id, song_name, time.perf_counter() - job_start
        )

    except Exception as exc:
        elapsed = time.perf_counter() - job_start
        logging.getLogger(__name__).error(
            "Job %s failed after %.2fs: %s", job_id, elapsed, exc
        )
        status["error"] = str(exc)
        status["message"] = f"Error: {exc}"
        status["done"] = True


@app.post("/extract")
def extract(req: ExtractRequest):
    """Validate inputs, kick off a background extraction, return job_id."""
    midi_path = _uploaded_files.get(req.file_id)
    if not midi_path:
        raise HTTPException(404, "file_id not found. Upload the MIDI file first.")
    if not Path(midi_path).exists():
        raise HTTPException(410, "Uploaded file is no longer available.")
    sf_id = req.soundfont_id or _DEFAULT_SOUNDFONT_ID
    if sf_id not in _soundfonts:
        raise HTTPException(400, f"Soundfont '{sf_id}' not found.")
    if not Path(_soundfonts[sf_id]["path"]).exists():
        raise HTTPException(500, f"Soundfont file missing on disk: {_soundfonts[sf_id]['name']}")

    job_id = str(uuid.uuid4())
    _job_status[job_id] = {
        "progress": 0,
        "message": "Queued…",
        "done": False,
        "error": None,
        "song_name": "",
        "soundfont_name": _soundfonts[sf_id]["name"],
        "stems": [],
        "live_stems": [],
    }

    thread = threading.Thread(
        target=_extraction_worker,
        args=(job_id, midi_path, req),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id}


# ---------------------------------------------------------------------------
# Job status  (polled by the frontend)
# ---------------------------------------------------------------------------

@app.get("/job/{job_id}/status")
def job_status(job_id: str):
    status = _job_status.get(job_id)
    if not status:
        raise HTTPException(404, "Job not found.")
    return status


# ---------------------------------------------------------------------------
# Download single file
# ---------------------------------------------------------------------------

@app.get("/download/{job_id}")
def download_stem(job_id: str, path: str):
    output_dir = _job_outputs.get(job_id)
    if not output_dir:
        raise HTTPException(404, "Job not found.")

    full_path = _safe_path(output_dir, path)
    if not full_path or not os.path.isfile(full_path):
        raise HTTPException(404, "File not found.")

    return FileResponse(full_path, filename=os.path.basename(full_path))


# ---------------------------------------------------------------------------
# Download zip  (POST body: list of relative paths; empty list = all)
# ---------------------------------------------------------------------------

@app.post("/download-zip/{job_id}")
def download_zip(job_id: str, paths: List[str] = Body(default=[])):
    """
    Return a zip archive.  `paths` is a JSON array of relative file paths
    (as returned by /job/{id}/status → stems[].path).
    Pass an empty array to download every stem.
    """
    output_dir = _job_outputs.get(job_id)
    if not output_dir:
        raise HTTPException(404, "Job not found.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if not paths:
            # all files
            for root, _, files in os.walk(output_dir):
                for fname in sorted(files):
                    full = os.path.join(root, fname)
                    zf.write(full, os.path.relpath(full, output_dir))
        else:
            for rel in paths:
                full = _safe_path(output_dir, rel)
                if full and os.path.isfile(full):
                    zf.write(full, rel)

    buf.seek(0)
    song_name = (_job_status.get(job_id) or {}).get("song_name") or Path(output_dir).name
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{song_name}.zip"'},
    )


# ---------------------------------------------------------------------------
# Download all jobs in one zip
# ---------------------------------------------------------------------------

@app.post("/download-all")
def download_all(job_ids: List[str] = Body(...)):
    """Zip every stem from every supplied job_id into one archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for job_id in job_ids:
            output_dir = _job_outputs.get(job_id)
            if not output_dir:
                continue
            folder = Path(output_dir).name
            for root, _, files in os.walk(output_dir):
                for fname in sorted(files):
                    full = os.path.join(root, fname)
                    # Prefix with song folder so files from different jobs don't collide
                    arcname = os.path.join(folder, os.path.relpath(full, output_dir))
                    zf.write(full, arcname)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="all_stems.zip"'},
    )


# ---------------------------------------------------------------------------
# Static frontend  (mounted last so API routes take priority)
# ---------------------------------------------------------------------------

_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
