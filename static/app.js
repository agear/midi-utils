(() => {
  // ── State ──────────────────────────────────────────────────────────────────
  // Each item: { id, file, name, status, fileId, jobId, progress, message, stems, songName }
  // status: 'pending' | 'uploading' | 'extracting' | 'done' | 'error'
  const fileQueue = [];

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const dropzone   = document.getElementById("dropzone");
  const fileInput  = document.getElementById("fileInput");
  const extractBtn = document.getElementById("extractBtn");
  const statusBox  = document.getElementById("statusBox");
  const statusMsg  = document.getElementById("statusMsg");
  const queueEl        = document.getElementById("queue");
  const globalActions  = document.getElementById("globalActions");
  const globalDlAllBtn = document.getElementById("globalDlAll");
  const sfSelect      = document.getElementById("sfSelect");
  const sfFileInput   = document.getElementById("sfFileInput");
  const sfUploadLabel = document.getElementById("sfUploadLabel");
  const sfStatusEl    = document.getElementById("sfStatus");

  // ── Soundfont management ───────────────────────────────────────────────────
  async function loadSoundfonts() {
    try {
      const res = await fetch("/soundfonts");
      if (!res.ok) return;
      const fonts = await res.json();
      const prev = sfSelect.value;
      sfSelect.innerHTML = "";
      fonts.forEach(sf => {
        const opt = document.createElement("option");
        opt.value = sf.id;
        opt.textContent = sf.name + (sf.is_default ? " ✦" : "");
        sfSelect.appendChild(opt);
      });
      // Restore selection if it still exists
      if (prev && [...sfSelect.options].some(o => o.value === prev)) sfSelect.value = prev;
    } catch (_) {}
  }

  async function uploadSoundfont(file) {
    if (!file.name.toLowerCase().endsWith(".sf2")) {
      sfStatusEl.style.display = "block";
      sfStatusEl.style.color = "#e07d7d";
      sfStatusEl.textContent = "Only .sf2 files are accepted.";
      return;
    }
    sfStatusEl.style.display = "block";
    sfStatusEl.style.color = "#9bb8e0";
    sfStatusEl.textContent = `Uploading ${file.name}…`;
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/soundfonts/upload", { method: "POST", body: form });
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
      const { name } = await res.json();
      await loadSoundfonts();
      [...sfSelect.options].forEach(o => { if (o.textContent === name) sfSelect.value = o.value; });
      sfStatusEl.style.color = "#7dbf9e";
      sfStatusEl.textContent = `"${name}" loaded.`;
    } catch (e) {
      sfStatusEl.style.color = "#e07d7d";
      sfStatusEl.textContent = `Upload failed: ${e.message}`;
    }
  }

  sfFileInput.addEventListener("change", () => {
    const file = sfFileInput.files[0];
    sfFileInput.value = "";
    if (file) uploadSoundfont(file);
  });

  sfUploadLabel.addEventListener("dragover", (e) => {
    e.preventDefault();
    sfUploadLabel.style.borderColor = "#6c8ebf";
    sfUploadLabel.style.background  = "#1f2335";
  });
  sfUploadLabel.addEventListener("dragleave", () => {
    sfUploadLabel.style.borderColor = "";
    sfUploadLabel.style.background  = "";
  });
  sfUploadLabel.addEventListener("drop", (e) => {
    e.preventDefault();
    sfUploadLabel.style.borderColor = "";
    sfUploadLabel.style.background  = "";
    const file = e.dataTransfer.files[0];
    if (file) uploadSoundfont(file);
  });

  // Load soundfonts on startup
  loadSoundfonts();

  // ── Drag-and-drop ──────────────────────────────────────────────────────────
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover",  (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); });
  dropzone.addEventListener("dragleave", ()  => dropzone.classList.remove("drag-over"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
    handleFiles(e.dataTransfer.files);
  });
  fileInput.addEventListener("change", () => { handleFiles(fileInput.files); fileInput.value = ""; });

  // ── Add files to queue ─────────────────────────────────────────────────────
  function handleFiles(fileList) {
    const mids    = [...fileList].filter(f => f.name.toLowerCase().endsWith(".mid"));
    const skipped = fileList.length - mids.length;

    if (mids.length === 0) { showStatus("No .mid files found.", "error"); return; }
    if (skipped > 0) showStatus(`${skipped} non-.mid file(s) ignored.`, "info");

    mids.forEach(file => {
      fileQueue.push({
        id: crypto.randomUUID(),
        file,
        name: file.name,
        status: "pending",
        fileId: null,
        jobId: null,
        progress: 0,
        message: "",
        stems: [],
        liveStems: [],
        songName: "",
        soundfontName: "",
      });
    });

    renderQueue();
    updateExtractBtn();
  }

  // ── Extract button ─────────────────────────────────────────────────────────
  function updateExtractBtn() {
    const n = fileQueue.filter(i => i.status === "pending").length;
    extractBtn.disabled = n === 0;
    extractBtn.textContent = n === 1 ? "Extract 1 File" : `Extract ${n} Files`;
  }

  extractBtn.addEventListener("click", processAll);

  // ── Process all pending items sequentially ─────────────────────────────────
  async function processAll() {
    extractBtn.disabled = true;
    statusBox.hidden = true;

    const pending = fileQueue.filter(i => i.status === "pending");
    for (const item of pending) {
      try {
        await uploadItem(item);
        await extractItem(item);
      } catch (e) {
        item.status = "error";
        item.message = e.message;
        renderQueueItem(item);
      }
    }

    updateExtractBtn();
    updateGlobalActions();
    const errors = fileQueue.filter(i => i.status === "error").length;
    showStatus(
      errors > 0 ? `Finished with ${errors} error(s).` : "All done!",
      errors > 0 ? "error" : "success",
    );
  }

  // ── Upload one item ────────────────────────────────────────────────────────
  async function uploadItem(item) {
    item.status  = "uploading";
    item.message = "Uploading…";
    renderQueueItem(item);

    const form = new FormData();
    form.append("file", item.file);
    const res = await fetch("/upload", { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    item.fileId = (await res.json()).file_id;
  }

  // ── Extract one item (kick off job, then poll) ─────────────────────────────
  async function extractItem(item) {
    item.status   = "extracting";
    item.progress = 0;
    item.message  = "Starting…";
    renderQueueItem(item);

    const res = await fetch("/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: item.fileId, convert_to_wav: true, soundfont_id: sfSelect.value || null }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    item.jobId = (await res.json()).job_id;

    await pollItem(item);
  }

  // ── Poll job status until done ─────────────────────────────────────────────
  function pollItem(item) {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/job/${item.jobId}/status`);
          if (!res.ok) throw new Error(res.statusText);
          const data = await res.json();

          item.progress      = data.progress;
          item.message       = data.message;
          item.liveStems     = data.live_stems || [];
          item.soundfontName = data.soundfont_name || "";
          renderQueueItem(item);

          if (data.done) {
            clearInterval(interval);
            if (data.error) {
              item.status  = "error";
              item.message = data.error;
              renderQueueItem(item);
              reject(new Error(data.error));
            } else {
              item.status        = "done";
              item.stems         = data.stems;
              item.songName      = data.song_name;
              item.soundfontName = data.soundfont_name || "";
              renderQueueItem(item);
              resolve();
            }
          }
        } catch (e) {
          clearInterval(interval);
          item.status  = "error";
          item.message = e.message;
          renderQueueItem(item);
          reject(e);
        }
      }, 500);
    });
  }

  // ── Render helpers ─────────────────────────────────────────────────────────
  function renderQueue() {
    queueEl.innerHTML = "";
    fileQueue.forEach(item => queueEl.appendChild(buildQueueItemEl(item)));
  }

  function renderQueueItem(item) {
    const el = buildQueueItemEl(item);
    const existing = document.getElementById(`qi-${item.id}`);
    if (existing) existing.replaceWith(el);
    else queueEl.appendChild(el);
  }

  const BADGE = { pending: "○", uploading: "↑", extracting: "⟳", done: "✓", error: "✕" };

  function buildQueueItemEl(item) {
    const wrap = document.createElement("div");
    wrap.className = `queue-item status-${item.status}`;
    wrap.id = `qi-${item.id}`;

    // Header: badge + filename + status message
    const header = el("div", "qi-header");

    const badge = el("span", `qi-badge qi-badge-${item.status}`);
    badge.textContent = BADGE[item.status] ?? "○";

    const name = el("span", "qi-name");
    name.textContent = item.name;

    const msg = el("span", "qi-msg");
    if (item.status === "extracting") {
      msg.textContent = `${item.message} (${item.progress}%)`;
    } else if (item.status === "uploading" || item.status === "error") {
      msg.textContent = item.message;
    }

    // Collapse toggle (done or extracting with live stems)
    if (item.status === "done" || (item.status === "extracting" && item.liveStems.length > 0)) {
      const toggle = el("button", "qi-toggle");
      toggle.textContent = item.expanded === false ? "▶" : "▼";
      toggle.title = "Toggle stems";
      header.append(toggle);
    }

    header.append(badge, name, msg);
    wrap.appendChild(header);

    // Soundfont label — always visible, outside the collapsible section
    if (item.soundfontName) {
      const sf = el("div");
      sf.style.cssText = "font-size:0.75rem;color:#555;margin-top:0.3rem;padding-left:1.6rem;";
      sf.textContent = `Soundfont: ${item.soundfontName}`;
      wrap.appendChild(sf);
    }

    // Overall progress bar while extracting
    if (item.status === "extracting") {
      const pw    = el("div", "qi-progress-wrap");
      const track = el("div", "progress-track");
      const fill  = el("div", "progress-bar-fill");
      fill.style.width = `${item.progress}%`;
      track.appendChild(fill);
      pw.appendChild(track);
      wrap.appendChild(pw);
    }

    // Live stems appearing during extraction
    if (item.status === "extracting" && item.liveStems.length > 0) {
      const liveSection = buildLiveStemsSection(item);
      liveSection.hidden = item.expanded === false;
      wrap.appendChild(liveSection);

      const toggle = wrap.querySelector(".qi-toggle");
      if (toggle) {
        toggle.addEventListener("click", () => {
          item.expanded      = liveSection.hidden;
          liveSection.hidden = !item.expanded;
          toggle.textContent = item.expanded ? "▼" : "▶";
        });
      }
    }


    // Full stems + download actions when done
    if (item.status === "done" && item.stems.length > 0) {
      const stemsSection = buildStemsSection(item);
      stemsSection.hidden = item.expanded === false;
      wrap.appendChild(stemsSection);

      const toggle = wrap.querySelector(".qi-toggle");
      if (toggle) {
        toggle.addEventListener("click", () => {
          item.expanded       = stemsSection.hidden;
          stemsSection.hidden = !item.expanded;
          toggle.textContent  = item.expanded ? "▼" : "▶";
        });
      }
    }

    return wrap;
  }

  // ── Live stems (shown while extracting) ───────────────────────────────────
  function buildLiveStemsSection(item) {
    const div   = el("div", "qi-stems");
    const midis = item.liveStems.filter(s => !s.is_wav);
    const wavs  = item.liveStems.filter(s =>  s.is_wav);

    if (midis.length > 0) {
      const lbl = el("div", "group-label"); lbl.textContent = "MIDI Stems";
      const ul  = el("ul", "stem-list");
      midis.forEach(s => ul.appendChild(buildLiveStemRow(s, item.jobId)));
      div.append(lbl, ul);
    }
    if (wavs.length > 0) {
      const lbl = el("div", "group-label");
      lbl.innerHTML = "WAV Stems" + (item.soundfontName ? ` <span style="font-weight:400;color:#555;text-transform:none;letter-spacing:normal;font-size:0.75rem;">· ${item.soundfontName}</span>` : "");
      const ul  = el("ul", "stem-list");
      wavs.forEach(s => ul.appendChild(buildLiveStemRow(s, item.jobId)));
      div.append(lbl, ul);
    }

    // "Processing…" pending row at the bottom
    const pending = el("li", "stem-row");
    const top     = el("div", "stem-row-top");
    const spinner = el("span", "stem-spinner"); spinner.textContent = "⟳";
    const label   = el("span", "stem-name");
    label.textContent = "Processing…";
    label.style.cssText = "color:#555;font-style:italic";
    top.append(spinner, label);
    const bar = el("div", "stem-bar stem-bar-active");
    pending.append(top, bar);
    div.appendChild(pending);

    return div;
  }

  function buildLiveStemRow(stem, jobId) {
    const li  = buildStemRow(stem, jobId);
    const bar = el("div", "stem-bar stem-bar-done");
    li.appendChild(bar);
    return li;
  }

  // ── Stems section for a completed item ────────────────────────────────────
  function buildStemsSection(item) {
    const section = el("div", "qi-stems");

    const midis = item.stems.filter(s => !s.is_wav);
    const wavs  = item.stems.filter(s =>  s.is_wav);

    if (midis.length > 0) {
      const lbl = el("div", "group-label"); lbl.textContent = "MIDI Stems";
      const ul  = el("ul", "stem-list");
      midis.forEach(stem => ul.appendChild(buildStemRow(stem, item.jobId)));
      section.append(lbl, ul);
    }

    if (wavs.length > 0) {
      const lbl = el("div", "group-label");
      lbl.innerHTML = "WAV Stems" + (item.soundfontName ? ` <span style="font-weight:400;color:#555;text-transform:none;letter-spacing:normal;font-size:0.75rem;">· ${item.soundfontName}</span>` : "");
      const ul  = el("ul", "stem-list");
      wavs.forEach(stem => ul.appendChild(buildStemRow(stem, item.jobId)));
      section.append(lbl, ul);
    }

    // Actions row: select links + download buttons
    const actRow = el("div", "qi-actions-row");

    const selLinks = el("span", "select-links");
    const selAll   = el("a"); selAll.textContent = "Select all";   selAll.href = "#";
    const deselAll = el("a"); deselAll.textContent = "Deselect all"; deselAll.href = "#";
    selLinks.append(selAll, " · ", deselAll);

    const dlAll = el("button", "dl-btn dl-btn-primary");
    dlAll.textContent = "Download All";

    const dlSel = el("button", "dl-btn dl-btn-secondary");
    const allCount = item.stems.length;
    dlSel.textContent = `Download Selected (${allCount})`;

    const actions = el("div", "dl-actions");
    actions.append(dlAll, dlSel);
    actRow.append(selLinks, actions);
    section.appendChild(actRow);

    // Events
    selAll.addEventListener("click", (e) => {
      e.preventDefault();
      section.querySelectorAll(".stem-check").forEach(cb => cb.checked = true);
      syncDlSel();
    });
    deselAll.addEventListener("click", (e) => {
      e.preventDefault();
      section.querySelectorAll(".stem-check").forEach(cb => cb.checked = false);
      syncDlSel();
    });
    section.addEventListener("change", syncDlSel);

    function syncDlSel() {
      const n = section.querySelectorAll(".stem-check:checked").length;
      dlSel.disabled = n === 0;
      dlSel.textContent = n > 0 ? `Download Selected (${n})` : "Download Selected";
    }

    dlAll.addEventListener("click", () => triggerZip(item.jobId, []));
    dlSel.addEventListener("click", () => {
      const paths = [...section.querySelectorAll(".stem-check:checked")].map(cb => cb.dataset.path);
      triggerZip(item.jobId, paths);
    });

    return section;
  }

  // ── Individual stem row ────────────────────────────────────────────────────
  function buildStemRow(stem, jobId) {
    const li  = el("li", "stem-row");
    const top = el("div", "stem-row-top");

    const cb = el("input");
    cb.type = "checkbox"; cb.className = "stem-check";
    cb.dataset.path = stem.path; cb.checked = true;

    const name = el("span", "stem-name");
    name.textContent = stem.name;

    const dl = el("a", "download-btn");
    dl.textContent = "↓"; dl.title = "Download";
    dl.href = `/download/${jobId}?path=${encodeURIComponent(stem.path)}`;
    dl.download = stem.name;

    top.append(cb, name);

    if (stem.is_wav) {
      const playBtn = el("button", "play-btn");
      playBtn.textContent = "▶"; playBtn.title = "Preview";

      const audioWrap = el("div", "audio-wrap");
      audioWrap.hidden = true;

      const canvas = el("canvas");
      canvas.height = 96;
      canvas.style.cssText = "width:100%;height:96px;display:block;border-radius:4px;cursor:pointer;margin-bottom:4px;";

      const audio = el("audio");
      audio.controls = true; audio.preload = "none";
      audio.src = `/download/${jobId}?path=${encodeURIComponent(stem.path)}`;
      audio.addEventListener("ended", () => { playBtn.textContent = "▶"; });
      audioWrap.append(canvas, audio);

      setupWaveform(audio, canvas, audio.src);

      playBtn.addEventListener("click", () => {
        const wasHidden = audioWrap.hidden;
        audioWrap.hidden = !wasHidden;
        if (wasHidden) {
          canvas.width = canvas.offsetWidth || 600;
          audio.play();
          playBtn.textContent = "■";
        } else {
          audio.pause();
          audio.currentTime = 0;
          playBtn.textContent = "▶";
        }
      });

      if (stem.duration_seconds != null) {
        const mins = Math.floor(stem.duration_seconds / 60);
        const secs = String(Math.floor(stem.duration_seconds % 60)).padStart(2, "0");
        const dur = el("span");
        dur.style.cssText = "font-size:0.75rem;color:#555;flex-shrink:0;";
        dur.textContent = `${mins}:${secs}`;
        top.append(dur);
      }
      top.append(playBtn, dl);
      li.append(top, audioWrap);
    } else {
      top.appendChild(dl);
      li.appendChild(top);
    }

    return li;
  }

  // ── Zip download ───────────────────────────────────────────────────────────
  async function triggerZip(jobId, paths) {
    try {
      const res = await fetch(`/download-zip/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(paths),
      });
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
      const url = URL.createObjectURL(await res.blob());
      const a   = Object.assign(el("a"), { href: url, download: filenameFromResponse(res, "stems.zip") });
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      showStatus(`Download failed: ${e.message}`, "error");
    }
  }

  // ── Global "Download All Files" button ────────────────────────────────────
  function updateGlobalActions() {
    const done = fileQueue.filter(i => i.status === "done");
    globalActions.hidden = done.length === 0;
  }

  globalDlAllBtn.addEventListener("click", async () => {
    const jobIds = fileQueue.filter(i => i.status === "done").map(i => i.jobId);
    if (jobIds.length === 0) return;
    try {
      const res = await fetch("/download-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jobIds),
      });
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
      const url = URL.createObjectURL(await res.blob());
      const a   = Object.assign(el("a"), { href: url, download: "all_stems.zip" });
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      showStatus(`Download failed: ${e.message}`, "error");
    }
  });

  // ── Waveform renderer ─────────────────────────────────────────────────────
  function setupWaveform(audio, canvas, url) {
    let offscreen = null;
    let rafId = null;

    async function load() {
      try {
        const resp    = await fetch(url);
        const buf     = await resp.arrayBuffer();
        const actx    = new (window.AudioContext || window.webkitAudioContext)();
        const decoded = await actx.decodeAudioData(buf);
        actx.close();

        const w   = canvas.width  || (canvas.width = canvas.offsetWidth || 600);
        const h   = canvas.height;
        const mid = h / 2;
        const ch  = decoded.getChannelData(0);
        const step = Math.ceil(ch.length / w);

        offscreen       = document.createElement("canvas");
        offscreen.width = w; offscreen.height = h;
        const oc = offscreen.getContext("2d");

        oc.fillStyle = "#161926";
        oc.fillRect(0, 0, w, h);

        oc.strokeStyle = "#2a2d3a";
        oc.lineWidth = 1;
        oc.beginPath(); oc.moveTo(0, mid); oc.lineTo(w, mid); oc.stroke();

        // Build per-pixel peaks
        const peaks = new Float32Array(w);
        let globalPeak = 0;
        for (let x = 0; x < w; x++) {
          let p = 0;
          for (let i = 0; i < step; i++) {
            const v = Math.abs(ch[x * step + i] || 0);
            if (v > p) p = v;
          }
          peaks[x] = p;
          if (p > globalPeak) globalPeak = p;
        }

        // Normalize so the loudest peak fills ~95% of the half-height
        const scale = globalPeak > 0 ? (mid * 0.95) / globalPeak : 1;
        oc.fillStyle = "#4a72a8";
        for (let x = 0; x < w; x++) {
          const amp = peaks[x] * scale;
          oc.fillRect(x, mid - amp, 1, amp * 2 || 1);
        }

        drawFrame();
      } catch (e) {
        console.warn("Waveform render failed:", e);
      }
    }

    function drawFrame() {
      if (!offscreen) return;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(offscreen, 0, 0);
      if (audio.duration) {
        const x = Math.round((audio.currentTime / audio.duration) * canvas.width);
        ctx.strokeStyle = "rgba(255,255,255,0.85)";
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      if (!audio.paused && !audio.ended) {
        rafId = requestAnimationFrame(drawFrame);
      }
    }

    audio.addEventListener("play", () => {
      if (!offscreen) { load(); return; }
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(drawFrame);
    });
    audio.addEventListener("pause",  () => { if (rafId) cancelAnimationFrame(rafId); drawFrame(); });
    audio.addEventListener("ended",  () => { if (rafId) cancelAnimationFrame(rafId); drawFrame(); });
    audio.addEventListener("seeked", () => { drawFrame(); });

    canvas.addEventListener("click", (e) => {
      if (!audio.duration) return;
      const r = canvas.getBoundingClientRect();
      audio.currentTime = ((e.clientX - r.left) / r.width) * audio.duration;
    });
  }

  // ── Utilities ──────────────────────────────────────────────────────────────
  function el(tag, className) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    return e;
  }

  function filenameFromResponse(res, fallback) {
    const cd = res.headers.get("Content-Disposition") || "";
    const m  = cd.match(/filename="?([^";\n]+)"?/);
    return m ? m[1] : fallback;
  }

  function showStatus(msg, type) {
    statusMsg.textContent = msg;
    statusBox.className   = `status-box status-${type}`;
    statusBox.hidden      = false;
  }
})();
