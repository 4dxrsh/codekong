# CodeKong — Docker Submission Guide

Everything you need to run the container yourself and submit it to the review
board. Written for someone who has never used Docker. Your commands are for
**Windows (Docker Desktop + PowerShell)**; the reviewer's commands work on any OS.

---

## 0. What you submit — two files

Both are in your **Downloads** folder (`C:\Users\Adarsh Rajesh\Downloads\`):

| File | Size | What it is |
|---|---|---|
| **`codekong-full.tar`** | ~9 GB | The entire system in one file: web app, real experiment results, a local Ollama server, AND the qwen2.5-coder:7b model baked in. The reviewer needs **no internet, no GPU, no API key, no setup** — just Docker. |
| **`REVIEWER_INSTRUCTIONS.txt`** | 2 KB | The run instructions for the reviewers (already written, sits next to the tar). |

There is also a lightweight alternative, `codekong-image.tar` (124 MB) — same
web UI and results but **without** the LLM (no live generation). Use it only if
the submission portal cannot accept a multi-GB file.

---

## 1. Before anything: start Docker

1. Open **Docker Desktop** (Start menu → "Docker Desktop"). Wait until the
   whale icon in the taskbar is steady (not animating).
2. Open **PowerShell** (Start menu → type "PowerShell" → Enter).
3. Confirm Docker is ready:

```powershell
docker version
```

If it prints version info without an error, you're good.

---

## 2. Test it yourself before submitting (recommended)

This is exactly what the reviewer will do.

**Step 2a — load the container from the file** (takes a few minutes, it's 9 GB):

```powershell
docker load -i "$HOME\Downloads\codekong-full.tar"
```

Expected output: `Loaded image: codekong-full:latest`

**Step 2b — run it:**

```powershell
docker run --rm -p 5001:5001 codekong-full
```

Leave this window open. You'll see `[codekong] starting Ollama server...`,
then `[codekong] Ollama is ready.`, then the web app starting.

**Step 2c — open the website:**

Go to **http://localhost:5001** in your browser. You should see the CodeKong
site: Results (real RQ1–RQ4 numbers), How It Works, Caught Bugs, Explore —
and live generation works because the model is inside the container.

**Step 2d — stop it:** back in PowerShell, press **Ctrl + C**.

**(Optional) prove the test suite passes inside the container:**

```powershell
docker run --rm codekong-full python tests/smoke_all.py
```

Last line should read `9/9 passed`.

---

## 3. What to put in your submission

Upload / hand over these two files together (zip them if the portal wants one file):

1. `codekong-full.tar`
2. `REVIEWER_INSTRUCTIONS.txt`

Nothing else is required.

---

## 4. The reviewer instructions (contents of REVIEWER_INSTRUCTIONS.txt)

```
CodeKong — how to run this submission

Requirements:
  - Docker (Docker Desktop on Windows/Mac, Docker Engine on Linux)
  - ~15 GB free disk and 8 GB of RAM available to Docker
    (Docker Desktop: Settings -> Resources -> Memory >= 8 GB)
  - NO internet, GPU, or API key needed — the language model
    (qwen2.5-coder:7b) and all dependencies are inside the image.

1. Load the image (takes a few minutes, the file is ~9 GB):
      docker load -i codekong-full.tar
   Expected: "Loaded image: codekong-full:latest"

2. Run it:
      docker run --rm -p 5001:5001 codekong-full
   Wait for "[codekong] Ollama is ready." then the web app banner.

3. Open a browser at:
      http://localhost:5001

   - Results: the research findings (RQ1-RQ4), computed from the real
     experiment output files — nothing hardcoded.
   - How It Works: a plain-language walkthrough of the pipeline.
   - Caught Bugs: actual tests the system generated, with the bugs they catch.
   - Live generation runs against the in-container model. Note: the model
     runs on CPU inside Docker, so generation takes ~30s-2min per request.

4. Stop: press Ctrl + C in the terminal.

Verify the code's own test suite (optional):
      docker run --rm codekong-full python tests/smoke_all.py
   Expected: "9/9 passed"

Troubleshooting:
  - "port is already allocated": use another port, e.g.
        docker run --rm -p 8080:5001 codekong-full
    then open http://localhost:8080
  - Model replies never arrive / container is killed: raise Docker's memory
    limit to 8 GB+ (Docker Desktop -> Settings -> Resources).
```

---

## 5. If they'd rather build from source

Give them the repository; it contains two Dockerfiles:

```
docker build -f Dockerfile.full -t codekong-full .   # full (needs internet to build)
docker build -t codekong .                           # lightweight demo
```

---

## 6. Troubleshooting (your side)

| Problem | Fix |
|---|---|
| `docker: command not found` / daemon errors | Docker Desktop isn't running — open it, wait for the steady whale. |
| `port is already allocated` | `docker run --rm -p 8080:5001 codekong-full` → http://localhost:8080 |
| Need to re-export the tar | `docker save codekong-full:latest -o "$HOME\Downloads\codekong-full.tar"` |
| Free the ~12 GB image from disk after submitting | `docker rmi codekong-full` |

---

## Quick reference (the whole thing in 3 commands)

```powershell
docker load -i "$HOME\Downloads\codekong-full.tar"
docker run --rm -p 5001:5001 codekong-full
# open http://localhost:5001 , press Ctrl+C to stop
```
