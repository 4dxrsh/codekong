# Running CodeKong on a MacBook

Everything is free and local. Apple Silicon (M1/M2/M3/M4) is the good case —
Ollama uses the GPU via Metal automatically. Intel Macs work but run the
model on CPU (slow; keep the 7b model and expect long batch runs).

## 1. One-time prerequisites

Open Terminal (Cmd+Space, type "Terminal").

    xcode-select --install        # Apple dev tools incl. git; OK if already installed

Install Homebrew (paste the one-liner from https://brew.sh), then RUN THE
"NEXT STEPS" COMMANDS IT PRINTS — on Apple Silicon that's:

    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile

Verify: `brew --version` prints a version. Skipping the next-steps is the #1
setup failure.

## 2. Get the project

Unzip the provided archive into your home directory so the project lands at
~/codekong (do NOT keep it in an iCloud-synced folder like Desktop/Documents
if iCloud Drive sync is on — file-sync layers can make Python run stale
code during mutant application):

    unzip ~/Downloads/codekong_mac.zip -d ~
    mv ~/ck ~/codekong 2>/dev/null || true
    cd ~/codekong
    git log --oneline | head -3     # newest commit should start 8f81c47 or later

## 3. Bootstrap (installs everything)

    bash setup.sh

This detects macOS, installs Python 3.11 if needed, creates the venv,
installs dependencies, installs Ollama via brew, starts the server, pulls
the model from config.yaml, runs a verification generation, and clones +
pins the two subject repos.

Model tier: on a 16GB+ Apple Silicon Mac, edit `llm.model` in config.yaml to
`qwen2.5-coder:14b` BEFORE running setup (better tests, still fast on
Metal). On 8GB keep `qwen2.5-coder:7b`.

Intel Macs only: if `pip install` fails building libcst, run
`brew install rust` and re-run `bash setup.sh`.

## 4. Verify, then use

Every new Terminal window: `cd ~/codekong && source venv/bin/activate`

    python tests/smoke_all.py          # must print 9/9 passed
    python generate_tests.py --file demo_range_utils.py \
        --description "numeric utilities" --limit 8 --skip-semantic
                                       # model capability check: kills > 0 = good

Website (the panel demo):

    python -m frontend.app             # open http://localhost:5001

Upload demo_range_utils.py on the Generate page with "Panel demo mode"
checked and watch the storyboard. Warm the model first
(`ollama run <model> "hi"`) so the demo doesn't spend a silent minute
loading it.

Full research runs (hours):

    python run_pipeline.py --repo sorts
    python run_pipeline.py --repo schedule
    python run_pipeline.py --repo sorts --phase evaluate

Keep the Mac awake during long runs: prefix with `caffeinate -i`.

## Troubleshooting

- `brew: command not found` → you skipped Homebrew's next-steps (section 1).
- Ollama "connection refused" → `brew services start ollama` (or `ollama serve &`).
- Model "not found (404)" → `ollama pull <model from config.yaml>`; check `ollama list`.
- Results from this Mac and the Windows laptop are NOT numerically
  comparable if the model tier differs — only each run's internal
  RAG-vs-NO_RAG delta is. Documented in paper/codekong_notes.md.
