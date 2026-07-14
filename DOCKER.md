# Running CodeKong with Docker

This container serves the CodeKong web UI — the real, committed experiment
results (RQ1–RQ4), the *How It Works* walkthrough, and the *Caught Bugs*
gallery of generated tests — and can run the offline test suite. It is small
(~540 MB), deterministic, and runs anywhere Docker runs (Linux, macOS,
Windows/Docker Desktop). No internet, GPU, or paid API is required for the demo.

## Build

```bash
docker build -t codekong .
```

## Run the web UI

```bash
docker run --rm -p 5001:5001 codekong
```

Then open **http://localhost:5001** in a browser:

- **Results** — RQ1–RQ4 computed live from the real result files (nothing hardcoded)
- **How It Works** — a plain-language walkthrough of the whole pipeline
- **Caught Bugs** — the actual validated tests the system generated
- **Explore** — every mutant, its diff, and the retrieved context

Stop with `Ctrl+C`.

## Verify the code (offline test suite)

```bash
docker run --rm codekong python tests/smoke_all.py
```

Expected output ends with `9/9 passed`.

## Submitting to the review board

**Option A — submit the repository (they build it).**
Include this repo with its `Dockerfile`; the reviewer runs the two commands above.

**Option B — submit a self-contained image file (they only load & run).**
No build or internet needed on their side:

```bash
# you: export the built image to a single file
docker save codekong:latest -o codekong-image.tar

# reviewer: load and run it
docker load -i codekong-image.tar
docker run --rm -p 5001:5001 codekong
```

## Optional: enabling live test generation

The demo shows pre-computed results. To generate tests live, the pipeline needs
the full ML stack (`requirements.txt`: torch, chromadb, sentence-transformers)
and a running **Ollama** server with `qwen2.5-coder:7b`. Point the app at a host
Ollama by setting `llm.local_host` in `config.yaml` to `http://host.docker.internal:11434`
and installing the full requirements. This is not needed to review the results.
