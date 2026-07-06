# CodeKong

A research pipeline testing one hypothesis: giving an LLM retrieved context
from the actual codebase under test (RAG), instead of just the failing mutant
diff, produces test rewrites that kill more surviving mutants — and that this
benefit grows as the injected bug gets harder to detect.

Four mutation classes of increasing difficulty operationalize "harder":
syntactic (mutmut operator swaps), statement-deletion (Python `ast`),
semantic (LLM-generated realistic bugs), and higher-order (two same-function
mutants combined). Each surviving mutant runs through two conditions —
NO_RAG (mutant diff + original test only, MuTAP-style) and RAG (plus top-k
chunks from a local vector index of the repo) — under an agentic layer of
five components (Mutation Generation, Repository Knowledge, Retrieval, Test
Generation, Validation) communicating through JSON files, where a surviving
first attempt triggers exactly one retry with structured validator feedback.

Everything is free and local: mutmut, pytest, Python `ast`,
sentence-transformers (all-MiniLM-L6-v2), ChromaDB, pandas, matplotlib, and
a local Ollama model. No Anthropic/OpenAI SDKs anywhere in this codebase.

## Setting up WSL2 from zero (Windows 11 Home, nothing installed)

The pipeline must run inside WSL2 Ubuntu. This is forced, not stylistic:
mutmut requires `fork()`, which only a real or virtual Linux kernel provides
(plain Windows is out), and WSL2 reaches the laptop's RTX 3050 Ti directly
through the existing Windows NVIDIA driver, which a VMware VM on
Optimus-style hybrid graphics typically cannot do.

Step 1. Open PowerShell **as Administrator** (right-click Start → "Terminal
(Admin)") and run:

    wsl --install -d Ubuntu

On a current Windows 11 build this one command installs both the WSL2 kernel
and Ubuntu. Windows 11 **Home** supports this out of the box via the lighter
Virtual Machine Platform feature — the Pro-only Hyper-V role is NOT required.

Step 2. Reboot if prompted. On first launch of Ubuntu (Start menu → Ubuntu)
it asks you to create a Linux username and password — pick anything, this is
separate from your Windows login.

Step 3. Inside that Ubuntu shell, before installing anything else:

    nvidia-smi

You should see the RTX 3050 Ti listed. If you don't, the fix is almost always
updating the NVIDIA driver **on the Windows host** — WSL2 uses that driver
directly; there is no separate Linux driver to install inside WSL. Do not
continue until the GPU is visible (or you've consciously accepted CPU-only).

Step 4. Get this repo into WSL and run the bootstrap. **Clone into your Linux
home directory (e.g. `~/codekong`), never into `/mnt/c/...`** — the Windows
drive mount (drvfs) caches file metadata, and this pipeline rewrites source
files in place during mutant application; stale metadata can make Python's
bytecode cache serve pre-mutation code (we hit exactly this bug during
development; `run_tests` also passes `-B` as a second line of defense):

    sudo apt update && sudo apt install -y git
    git clone <your-fork-or-this-repo-url> codekong && cd codekong
    bash setup.sh

`setup.sh` installs python3-venv/pip, creates the venv, installs pinned
dependencies (and freezes exact versions to `requirements.lock.txt`),
installs Ollama via its official Linux script, pulls the configured model,
runs a verification generation, clones both subject repos, and pins them to
commit SHAs written into `config.yaml` (commit that change — it is what makes
mutation results reproducible).

Manual equivalent of the environment portion:

    sudo apt update && sudo apt install -y python3-venv python3-pip
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen2.5-coder:7b
    ollama run qwen2.5-coder:7b "write a one-line python function"

Watch how fast that last response comes back — it is the quickest way to tell
whether the GPU is actually in use or the model silently fell back to CPU.

## Hardware and model choice

Probe the machine with `python -m core.hardware`. Tiers: ≤8GB VRAM/RAM →
`qwen2.5-coder:7b`; 12–16GB → `qwen2.5-coder:14b` or
`deepseek-coder-v2:16b-lite-instruct`; ≥24GB → `qwen2.5-coder:32b` or
`qwen3-coder:30b` (MoE, fits a 24GB card). The model and provider live in
`config.yaml` (`llm.model`, `llm.provider`) — never in code.

On the target laptop's RTX 3050 Ti (fixed 4GB VRAM regardless of vendor), a
Q4-quantized 7B needs roughly 5–6GB with context headroom, so Ollama will
partially offload to system RAM and run noticeably slower than published
7B-on-8GB benchmarks. That is expected on this card, not a sign anything is
broken — budget batch runs (dozens of mutants × two conditions × two repos)
accordingly.

Ollama has two faces and they are not interchangeable. **Local Ollama**
(default) is free, unlimited, keyless, at `http://localhost:11434`. **Ollama
Cloud** is a separate hosted product with an `OLLAMA_API_KEY` and a
rate-limited free tier (session limits resetting every 5 hours, weekly caps,
one concurrent model) — not built for firing off hundreds of sequential batch
calls, which is exactly what this pipeline does. Use cloud only as a
documented, deliberate exception for machines that cannot run even the 7B
tier at usable speed (no discrete GPU, under 8GB free RAM): set
`llm.provider: cloud` in `config.yaml`, put the key in `.env` (see
`.env.example`), and expect to split batch runs across multiple 5-hour
sessions.

## Running

    source venv/bin/activate
    python run_pipeline.py --repo sorts                # everything
    python run_pipeline.py --repo schedule             # second subject
    python run_pipeline.py --repo sorts --phase mutate # single phase
    python run_pipeline.py --repo sorts --limit 10 --skip-semantic  # smoke run

Phases: `mutate` (mutmut + SDL + semantic + HOM → survival-filtered
`module1_mutation/surviving_mutants.json`), `index` (AST-walk → embeddings →
ChromaDB), `generate` (NO_RAG then RAG at each k in `rag.k_values`, one-retry
agentic loop, results CSVs), `evaluate` (RQ answers →
`module4_eval/results/rq_answers.json`, four figures →
`module4_eval/figures/`).

A guard refuses to run mutation phases outside a fork-capable Linux kernel
and tells you to switch to a WSL2 terminal instead of letting mutmut die with
a cryptic fork error.

## Repository layout

    config.yaml               repo paths, k values, provider + model, caps
    core/                     config/guards/hardware/schema/test-exec plumbing
    module1_mutation/         four mutant sources, normalizer, survival runner,
                              NO_RAG baseline driver; surviving_mutants.json
    module2_rag/              indexer + class-aware retriever; chroma_db/ (gitignored)
    module3_llm/              ollama_client (THE single model integration point),
                              class-specific prompts, rewriter, JSONL call log
    agentic/                  five agents; one-retry refinement; structured validation
    module4_eval/             audits, metrics, RAG-vs-NO_RAG comparison, figures
    run_pipeline.py           single entry point
    setup.sh                  Phase 0 bootstrap (WSL2 Ubuntu)
    paper/codekong_notes.md   running notes toward the paper

## Threats to validity (read before citing numbers)

The original design used the Claude API for semantic-mutant generation and
test rewriting. This implementation deliberately substitutes an open local
model via Ollama, which lowers the ceiling on instruction-following and
code-generation quality. The RAG-vs-NO_RAG comparison inside a run is still
internally valid (both conditions share model, prompts, temperature), but
absolute kill-rate and valid-test-rate numbers are not comparable to a
Claude-backed run and should not be presented as such. Full list in
`paper/codekong_notes.md`.

If batch runs show a high rate of `GEN_FAILED` (model never produced
parseable Python), the audit in `module4_eval/validator.py` will flag it —
that means the model tier must go up before the comparison means anything.

## License

MIT (subject repos keep their own MIT licenses; they are cloned, pinned, and
never vendored).
