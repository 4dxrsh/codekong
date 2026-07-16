# CodeKong Explained

This file is a plain-English guide for the CodeKong project. It is written for
the team members who built the project with AI help and now need to understand
what is actually happening.

The short version:

CodeKong intentionally plants small bugs into Python code, checks whether the
old tests miss those bugs, then asks a local LLM to write new tests that catch
them. It compares two situations:

- `NO_RAG`: the LLM sees only the changed code and the old tests.
- `RAG`: the LLM also gets useful snippets retrieved from the codebase.

The research question is: does giving the LLM codebase context help it write
better tests?

In the current committed results, yes, but with an important nuance: RAG helps
most when the correct answer depends on facts stored somewhere else in the
codebase, like constants in `rates.py`. It does not magically help everywhere.

## 1. The Big Idea In Simple Words

Imagine you have a working function:

```python
def bulk_discount(quantity):
    for min_qty, frac in BULK_BREAKS:
        if quantity >= min_qty:
            return frac
    return 0.0
```

The actual discount table is somewhere else:

```python
BULK_BREAKS = [(100, 0.18), (50, 0.11), (10, 0.04), (0, 0.0)]
```

An existing test only checks an easy case:

```python
def test_bulk_discount_below_first_break():
    assert bulk_discount(5) == 0.0
```

That test passes, but it does not check `10`, `50`, or `100`.

CodeKong says:

1. Let us create a bugged version of `bulk_discount`.
2. Let us see if the existing tests catch that bug.
3. If the existing tests do not catch it, this is a real gap.
4. Ask the LLM to write a new test for that gap.
5. Only keep the new test if it passes on the correct code and fails on the bugged code.

That last rule is extremely important. CodeKong does not trust a test just
because it looks reasonable. It proves the test catches a specific bug.

## 2. Glossary

### Test suite

A group of tests that check whether code behaves correctly.

Example:

```python
def test_add():
    assert add(2, 3) == 5
```

### Mutation testing

Mutation testing is a way to test your tests.

Instead of asking "does the code pass the tests?", it asks:

"If I secretly introduce a bug, do the tests notice?"

If the tests notice, your tests are strong for that behavior.

If the tests do not notice, your tests have a blind spot.

### Mutant

A mutant is a bugged version of a function.

Original:

```python
if quantity >= min_qty:
    return frac
```

Mutant:

```python
if quantity > min_qty:
    return frac
```

This tiny change might break boundary values like `quantity == 10`.

### Killed mutant

A mutant is "killed" when a test catches it.

In CodeKong, a kill means both of these happened:

- The generated test passes on the original correct code.
- The same generated test fails on the mutated bugged code.

If only one of those is true, it is not a valid kill.

### Surviving mutant

A surviving mutant is a bug that the existing test suite failed to catch.

Those are the interesting mutants. CodeKong tries to generate tests for them.

### RAG

RAG means Retrieval-Augmented Generation.

In normal words: before asking the LLM to write a test, CodeKong searches the
codebase for useful context and includes that context in the prompt.

For example, if the function uses `BULK_BREAKS`, RAG can retrieve the actual
definition from `rates.py`.

### NO_RAG

NO_RAG is the closed-book baseline.

The LLM sees the mutant diff and old tests, but it does not get retrieved
codebase context.

This is important because it lets the project compare:

- "LLM guessing from the local diff"
- versus "LLM with codebase memory"

### LLM

LLM means Large Language Model. In this repo, the LLM is served locally through
Ollama, usually `qwen2.5-coder:7b`.

This project deliberately does not use OpenAI or Anthropic SDKs.

### Ollama

Ollama is the local server that runs the model.

The code talks to Ollama at:

```text
http://localhost:11434
```

### ChromaDB

ChromaDB is the local vector database used for RAG.

Plain-English version: it stores searchable code snippets. CodeKong asks it,
"What parts of the codebase look relevant to this mutant?"

### Embedding

An embedding is a numeric representation of text. Similar text gets similar
numbers. This is how ChromaDB can search code by meaning instead of only exact
words.

### AST

AST means Abstract Syntax Tree.

Plain-English version: Python code turned into a tree structure that the
program can inspect. CodeKong uses ASTs to find functions, docstrings, test
functions, and statements it can delete.

### Pytest

Pytest is the test runner. CodeKong uses it to run both old tests and generated
tests.

## 3. What CodeKong Is Trying To Prove

The project's main hypothesis:

Giving the LLM retrieved codebase context should help it write tests that catch
more hidden bugs.

The project asks four research questions:

### RQ1: Does RAG beat NO_RAG overall?

Do generated tests kill more mutants when the LLM gets retrieved context?

Current combined result from `module4_eval/results/rq_answers.json`:

```text
NO_RAG kill rate: 12.8%
RAG kill rate:    53.0%
```

So in the committed result files, RAG wins overall.

### RQ2: Does RAG help more as bugs get harder?

The intended difficulty order is:

```text
syntactic < semantic < higher_order
```

Current result file says the gradient holds for the classes present:

```text
semantic RAG delta:      +25.6 percentage points
higher_order RAG delta:  +73.3 percentage points
```

Important caveat: the current result set is missing the `syntactic` class
because mutmut integration was skipped or problematic in the run history.

### RQ3: How many retrieved chunks should be used?

RAG retrieves `k` chunks. The project tests `k = 3`, `5`, and `8`.

Current valid-test rates:

```text
k = 3: 69.2%
k = 5: 69.2%
k = 8: 64.1%
```

More context is not always better. Too much context can distract the model.

### RQ4: Is the extra context worth the cost?

The model is local, so there is no dollar bill. The project uses token counts
and wall-clock time as a cost substitute.

For `ctxlib`, the handoff notes say:

```text
NO_RAG: 15,859 tokens per kill
RAG:     2,246 tokens per kill
```

RAG uses more context per call, but because it catches more bugs, it can be
cheaper per actual bug caught.

## 4. The Whole Pipeline At A Glance

Here is the research pipeline:

```text
config.yaml
   |
   v
run_pipeline.py
   |
   +-- mutate
   |      |
   |      v
   |   module1_mutation creates mutants
   |      |
   |      v
   |   existing tests filter out already-caught mutants
   |      |
   |      v
   |   surviving_mutants.json
   |
   +-- index
   |      |
   |      v
   |   module2_rag indexes the subject repo into ChromaDB
   |
   +-- generate
   |      |
   |      +-- NO_RAG generation
   |      |
   |      +-- RAG generation at k = 3, 5, 8
   |      |
   |      v
   |   generated tests + records + metrics CSVs
   |
   +-- evaluate
          |
          v
       RQ answers + figures
```

The user-facing single-file generator uses the same core pieces:

```text
generate_tests.py
   |
   +-- copy uploaded file into subjects/user_<name>/
   +-- create a tiny bootstrap import test
   +-- create mutants
   +-- optionally build RAG index
   +-- ask LLM for tests
   +-- validate each test
   +-- keep only tests that kill mutants
   +-- write generated_test_suites/test_<name>_generated.py
```

## 5. Two Different Uses Of This Repo

### Use 1: Research experiment

Command shape:

```bash
python run_pipeline.py --repo ctxlib --skip-mutmut
```

This runs a subject repo from `config.yaml` and compares RAG vs NO_RAG.

Main outputs:

- `module1_mutation/surviving_mutants.json`
- `module2_rag/chroma_db/`
- `module2_rag/rag_context.json`
- `module3_llm/generated_tests/`
- `module4_eval/results/raw_<repo>.csv`
- `module4_eval/results/summary_<repo>.csv`
- `module4_eval/results/cost_<repo>.csv`
- `module4_eval/results/records_<repo>.json`
- `module4_eval/results/rq_answers.json`
- `module4_eval/figures/*.png`

### Use 2: Generate tests for one Python file

Command shape:

```bash
python generate_tests.py --file demo_range_utils.py --description "numeric range utilities" --limit 8 --skip-semantic --no-rag
```

This does not run the full research comparison. It takes one file and tries to
produce useful pytest tests for it.

Main outputs:

- `subjects/user_demo_range_utils/`
- `generated_test_suites/mutants_user_demo_range_utils.json`
- `generated_test_suites/report_demo_range_utils.json`
- `generated_test_suites/test_demo_range_utils_generated.py`
- generated audit tests under `module3_llm/generated_tests/`

Current demo result:

```text
8 mutants attempted
8 mutants killed
kill rate 100%
model qwen2.5-coder:7b
```

That is a capability probe, not the full research result.

## 6. Detailed Research Run Walkthrough

This section walks through what happens when you run:

```bash
python run_pipeline.py --repo ctxlib --skip-mutmut
```

In practice, mutation phases should be run in WSL2 or another fork-capable
Linux/macOS environment. Native Windows is rejected for mutmut-related safety.

### Step 0: Load config

`run_pipeline.py` calls:

```python
cfg = load_config()
```

That reads `config.yaml`.

Important config values:

```yaml
llm:
  provider: local
  model: qwen2.5-coder:7b
  temperature_testgen: 0.0
  temperature_semantic: 0.7

rag:
  default_k: 5
  k_values: [3, 5, 8]

agentic:
  max_retries: 1
```

Plain-English meaning:

- Use a local Ollama model.
- Generate tests deterministically.
- Generate semantic mutants with a little creativity.
- Try RAG with 3, 5, and 8 retrieved chunks.
- If the first generated test fails, retry exactly once.

### Step 1: Mutate

Mutation means "create bugged versions of functions."

Code path:

```text
run_pipeline.py
-> phase_mutate()
-> agentic/mutation_agent.py
-> module1_mutation/mutant_normalizer.py
```

The normalizer collects mutants from four possible sources:

1. `syntactic`: mechanical changes from mutmut, like `>` to `>=`.
2. `sdl`: statement deletion, like deleting `return hi`.
3. `semantic`: realistic bug generated by the LLM.
4. `higher_order`: two first-order mutants combined into one harder mutant.

The current committed results used `--skip-mutmut`, so syntactic mutants are
not present in those result CSVs.

### Step 2: Normalize every mutant

Every mutant becomes one JSON object with the same fields.

Example fields:

```json
{
  "mutant_id": "sdl_bulk_discount_00aa7bbf25",
  "file": "billing.py",
  "function": "bulk_discount",
  "line": 27,
  "original_code": "...",
  "mutated_code": "...",
  "mutation_operator": "statement_deletion",
  "mutation_source": "ast_sdl",
  "mutation_class": "sdl",
  "mutation_description": "Deleted statement: ...",
  "diff": "...",
  "existing_test_file": "test_ctxlib.py"
}
```

Why this matters:

Downstream code does not need to care whether the mutant came from mutmut, AST
deletion, the LLM, or the HOM combiner. It gets one consistent shape.

### Step 3: Survival filtering

Code path:

```text
module1_mutation/mutation_runner.py
-> confirm_survival()
```

For each mutant:

1. Make a scratch copy of the subject repo.
2. Replace the original function with the mutated function.
3. Run the existing tests.
4. If the existing tests fail, the mutant was already caught, so CodeKong drops it.
5. If the existing tests pass, the mutant survived, so CodeKong keeps it.

Plain-English version:

"Only keep bugs that the old tests missed."

### Step 4: Build the RAG index

Code path:

```text
run_pipeline.py
-> phase_index()
-> agentic/knowledge_agent.py
-> module2_rag/rag_indexer.py
```

The indexer scans the subject repo and stores searchable chunks:

- function bodies
- function docstrings
- test functions
- module-level constants, like `BULK_BREAKS`

The constants part is especially important. Earlier versions indexed functions
but missed values in files like `rates.py`, which meant RAG could not retrieve
the actual facts needed to write correct tests.

### Step 5: Generate tests in NO_RAG mode

Code path:

```text
run_pipeline.py
-> phase_generate()
-> agentic/test_gen_agent.py
-> module3_llm/llm_rewriter.py
-> module3_llm/ollama_client.py
```

For each surviving mutant, the LLM gets:

- the function name
- the mutation description
- the diff
- the original correct function
- sometimes the mutated function
- existing test material
- no retrieved context

It writes one pytest file.

### Step 6: Validate the generated test

Code path:

```text
agentic/validation_agent.py
```

Validation is two-stage:

1. Run the generated test against the original code.
2. Run the same generated test against the mutated code.

Possible outcomes:

- `KILLED`: passes original, fails mutant.
- `SURVIVED`: passes original, but also passes mutant.
- `INVALID_TEST`: does not pass original.
- `GEN_FAILED`: model did not produce parseable Python.

### Step 7: Retry once if needed

If the generated test does not kill the mutant, CodeKong gives the LLM the
validator's feedback and tries once more.

Example feedback:

```text
Test passes on BOTH original and mutant. It does not exercise the mutated behavior.
Target inputs where the diff changes the output.
```

There is exactly one retry. This is a research invariant.

### Step 8: Generate tests in RAG mode

For RAG, CodeKong first retrieves useful context.

Code path:

```text
module2_rag/retriever.py
```

Retrieval is mutation-class-aware:

- syntactic mutant: query function name plus diff
- SDL mutant: query function name plus deleted statement
- semantic mutant: query original function plus bug description
- higher-order mutant: query each component mutation and merge results

It also directly fetches definitions of symbols the function reads.

Example:

`bulk_discount()` reads `BULK_BREAKS`, so retrieval tries to include the
definition of `BULK_BREAKS`.

### Step 9: Log metrics

Code path:

```text
module4_eval/metrics_logger.py
```

It writes:

- raw result rows
- summary rows
- token/cost rows from the LLM call log

### Step 10: Evaluate research questions

Code path:

```text
module4_eval/compare_conditions.py
```

It combines `raw_*.csv`, answers RQ1-RQ4, and creates figures.

## 7. Worked Example: bulk_discount

This is the easiest example to understand because it shows why RAG matters.

### The real code

`subjects/ctxlib/billing.py`:

```python
def bulk_discount(quantity):
    """Return the bulk discount fraction earned for ordering `quantity` units,
    per the volume breakpoints in rates.BULK_BREAKS."""
    for min_qty, frac in BULK_BREAKS:
        if quantity >= min_qty:
            return frac
    return 0.0
```

`subjects/ctxlib/rates.py`:

```python
BULK_BREAKS = [(100, 0.18), (50, 0.11), (10, 0.04), (0, 0.0)]
```

### The shallow existing test

`subjects/ctxlib/test_ctxlib.py`:

```python
def test_bulk_discount_below_first_break():
    assert bulk_discount(5) == 0.0
```

This checks only one easy value. It does not check `10`, `50`, or `100`.

### A mutant

One SDL mutant deletes an important statement or branch. The old test still
passes, so the mutant survives.

That means CodeKong has found a test gap.

### What NO_RAG did

The saved NO_RAG generated test guessed the wrong business rule:

```python
from billing import bulk_discount

def test_bulk_discount_above_first_break():
    assert bulk_discount(10) == 0.1, "Should return 0.1 for quantity >= 5"
```

This test fails on the original correct code because the real value is `0.04`,
not `0.1`.

So CodeKong marks it:

```text
INVALID_TEST
```

This is not counted as a kill, because a test that fails on correct code is a
bad test.

### What RAG did

RAG retrieved this context:

```text
BULK_BREAKS = [(100, 0.18), (50, 0.11), (10, 0.04), (0, 0.0)]
```

The saved RAG generated test was:

```python
from billing import bulk_discount

def test_bulk_discount_above_first_break():
    assert bulk_discount(10) == 0.04
```

That passes on the original code and fails on the mutant.

So CodeKong marks it:

```text
KILLED
```

That is the project in one example.

## 8. Worked Example: demo_range_utils

`demo_range_utils.py` is a small demo file with functions like:

- `clamp`
- `lerp`
- `letter_grade`
- `running_total`

The current generated report is:

```text
generated_test_suites/report_demo_range_utils.json
mutants_attempted: 8
mutants_killed: 8
kill_rate: 1.0
wall_seconds: 161.1
model: qwen2.5-coder:7b
```

One generated test:

```python
from demo_range_utils import clamp

def test_clamp_upper_bound_m1():
    assert clamp(15, 0, 10) == 10, "Should return hi when x > hi"
```

Why this kills a mutant:

- Original `clamp(15, 0, 10)` returns `10`.
- A mutant where the upper-bound return was deleted returns `15`.
- The test passes original and fails mutant.

## 9. Current Results In This Workspace

The result files are under:

```text
module4_eval/results/
```

### Combined RQ answers

From `rq_answers.json`:

```text
NO_RAG kill rate: 12.8%
RAG kill rate:    53.0%
RAG wins overall: true
```

### ctxlib

From `summary_ctxlib.csv`:

```text
NO_RAG higher_order: 0/4 killed, kill rate 0.0%
NO_RAG sdl:          2/13 killed, kill rate 15.4%
NO_RAG semantic:     1/7 killed, kill rate 14.3%

RAG higher_order:    11/12 killed, kill rate 91.7%
RAG sdl:             32/39 killed, kill rate 82.1%
RAG semantic:        13/21 killed, kill rate 61.9%
```

Plain-English interpretation:

`ctxlib` is context-dependent. Many correct answers depend on constants in
`rates.py`. RAG helps a lot because it can retrieve those constants.

### sorts_focused

From `summary_sorts_focused.csv`:

```text
NO_RAG sdl:       0/3 killed
NO_RAG semantic:  2/6 killed

RAG sdl:          0/9 killed
RAG semantic:     6/18 killed
```

The overall subject-level handoff says `sorts_focused` tied at 22.2% vs 22.2%.

Plain-English interpretation:

Sorting functions are mostly self-contained. If the answer is already inside
the function, retrieval has less extra information to add.

### schedule

From `summary_schedule.csv`:

```text
NO_RAG: 0 kills
RAG:    0 kills
```

Plain-English interpretation:

The small local model struggled to write valid tests for this object-oriented
library. This is a model limitation, not a RAG success.

### Important honesty note

The project should not claim "RAG always wins."

The better claim is:

RAG helps when the missing test needs facts located elsewhere in the codebase.

## 10. Important Invariants

These rules are part of the project's scientific integrity.

### Only `ollama_client.py` talks to the model

All LLM calls go through:

```text
module3_llm/ollama_client.py
```

Do not add random model calls elsewhere.

### Test generation uses temperature 0.0

Temperature controls randomness.

CodeKong sets test generation to `0.0` to make outputs as deterministic as
possible.

### Semantic mutant generation uses temperature 0.7

Semantic mutants are intentionally a little creative because they are supposed
to look like realistic developer mistakes.

### A kill requires two checks

The generated test must:

1. Pass on original code.
2. Fail on mutated code.

Never weaken this.

### Exactly one retry

The agentic loop allows one retry after validator feedback.

More retries would change the experiment.

### UI must show real data only

The UI should never invent numbers. Missing data should appear as an empty
state.

### User uploads must not overwrite research data

Single-file generation writes to:

```text
generated_test_suites/mutants_<key>.json
```

It should not overwrite:

```text
module1_mutation/surviving_mutants.json
```

## 11. File And Folder Map

This section explains what each important file or folder does.

### Root files

#### `README.md`

Human-facing overview and setup instructions. It explains the research idea,
WSL2 setup, Ollama setup, running the pipeline, web UI, and threats to
validity.

Some state inside it may be older than `HANDOFF.md`.

#### `AGENTS.md`

Instructions for AI coding agents working on this repo. It lists invariants,
hazards, and working norms.

#### `CLAUDE.md`

Older AI handoff/instructions file. Similar to `AGENTS.md`. Its "current
state" section is stale according to `HANDOFF.md`.

#### `HANDOFF.md`

Most current session handoff. It says the real experiment results have been
run and explains the current findings, known hazards, and open work.

Use this when README/CLAUDE disagree with the actual result files.

#### `config.yaml`

The central configuration file.

It defines:

- which LLM provider and model to use
- RAG settings
- mutation limits
- retry limit
- subject repos
- output paths

Important: model and provider live here, not hardcoded in code.

#### `run_pipeline.py`

The main research entry point.

It runs:

```text
mutate -> index -> generate -> evaluate
```

Useful commands:

```bash
python run_pipeline.py --repo ctxlib --skip-mutmut
python run_pipeline.py --repo ctxlib --phase generate --conditions RAG --k 3 5 8
python run_pipeline.py --repo ctxlib --phase evaluate
```

It also uses checkpointing during generation, so a long run can resume.

#### `generate_tests.py`

The practical single-file test generator.

It takes one Python file and a plain-English description, creates mutants,
asks the LLM for tests, validates the tests, and writes a final pytest file
containing only tests that killed mutants.

#### `demo_range_utils.py`

Small demo input file. Used to quickly check whether the model can generate
useful tests.

#### `view_rag.py`

Small inspection script that prints what is stored in the ChromaDB RAG memory
for a subject.

Example:

```bash
python view_rag.py ctxlib
```

#### `setup.sh`

Bootstrap script for WSL2/Linux/macOS.

It installs dependencies, creates a virtual environment, installs Ollama,
pulls the configured model, and clones/pins subject repos.

#### `requirements.txt`

Full dependency list for live pipeline work. Includes mutmut, pytest,
sentence-transformers, ChromaDB, Ollama, pandas, matplotlib, Flask, and config
helpers.

#### `requirements-demo.txt`

Smaller dependency list for the demo Docker container. Enough to serve the UI
and run smoke tests, but not enough for full live RAG generation.

#### `requirements.lock.txt`

Frozen installed versions from setup. Used for reproducibility.

#### `Dockerfile`

Lightweight demo container. Serves the web UI with committed results. Does not
bundle the full LLM stack.

#### `Dockerfile.full`

Large full container. Attempts to include Ollama, the model, and the ML stack
so live generation can work offline inside Docker.

#### `DOCKER.md`

Docker usage guide.

#### `SUBMISSION.md`

Submission instructions for reviewers, especially for the full Docker image.

#### `LICENSE`

Project license.

#### `codekong_mac.zip`

Zip artifact in the repo. It appears to be a packaged copy for macOS or
transfer. It is not part of the runtime pipeline.

### `core/`

Shared low-level utilities used by all modules.

#### `core/config.py`

Loads `config.yaml` and `.env`.

Provides:

- `load_config()`
- `resolve()`
- `ollama_api_key()`

#### `core/guards.py`

Protects the project from unsafe environments.

It refuses native Windows for mutation phases because mutmut needs `fork()`.
It also refuses WSL projects located under `/mnt/c/...` because Windows-drive
metadata caching can corrupt mutation results.

#### `core/hardware.py`

Checks GPU/system memory and recommends an Ollama model tier.

The config still wins. This is advisory.

#### `core/schema.py`

Defines the unified mutant schema.

Every mutant must have fields like:

- `mutant_id`
- `file`
- `function`
- `original_code`
- `mutated_code`
- `mutation_class`
- `diff`

It also validates that mutated code still parses as Python.

#### `core/srcmap.py`

Finds Python files and extracts function source code using AST parsing.

Used by mutation generation and RAG indexing.

#### `core/testexec.py`

Runs pytest safely and applies/restores mutants.

Important pieces:

- `run_tests()`: runs pytest with timeout.
- `MutantApplier`: temporarily swaps original code for mutated code, then
  restores it.

It disables bytecode caching with `-B` because this project rewrites files in
place.

#### `core/input_security.py`

Validates uploaded files and descriptions in the web UI.

It checks:

- filename safety
- `.py` extension
- UTF-8 text
- file size
- syntax validity
- description length

### `module1_mutation/`

Creates and filters mutants.

#### `module1_mutation/mutant_normalizer.py`

Main mutation orchestrator.

It collects:

- syntactic mutants from mutmut
- SDL mutants from AST statement deletion
- semantic mutants from the LLM
- higher-order mutants from combinations

Then it filters for survivors and writes the final mutant JSON.

#### `module1_mutation/sdl_generator.py`

Creates statement-deletion mutants.

Example:

Original:

```python
if x > hi:
    return hi
```

Mutated:

```python
if x > hi:
    pass
```

#### `module1_mutation/hom_combiner.py`

Creates higher-order mutants by combining two first-order mutants in the same
function.

Example:

- delete lower-bound guard
- delete upper-bound guard
- combine both into one harder mutant

#### `module1_mutation/mutation_runner.py`

Applies mutants to a scratch copy and runs the existing tests to check whether
each mutant survived.

#### `module1_mutation/baseline_norag.py`

Older or separate runner for the NO_RAG baseline. The main pipeline now handles
both NO_RAG and RAG in `run_pipeline.py`.

#### `module1_mutation/_scratch/`

Generated working copies of subject repos. These are temporary mutation
workspaces.

Do not treat these as source-of-truth code.

### `module2_rag/`

Builds and queries the RAG memory.

#### `module2_rag/rag_indexer.py`

Scans a subject repo and stores searchable chunks in ChromaDB.

Chunks include:

- function bodies
- docstrings
- test functions
- module-level constants

The constants are crucial for `ctxlib`.

#### `module2_rag/retriever.py`

Given a mutant, retrieves useful codebase context.

It builds different queries depending on the mutant class and also fetches
definitions of referenced symbols.

Example:

If a function references `BULK_BREAKS`, retriever tries to include the actual
`BULK_BREAKS` definition.

#### `module2_rag/chroma_db/`

Generated ChromaDB database folder. Stores embeddings and documents for RAG.

It is normally gitignored or treated as generated data.

#### `module2_rag/rag_context.json`

Generated handoff file showing which chunks were retrieved for each mutant.

### `module3_llm/`

Builds prompts, calls the local model, and stores generated tests.

#### `module3_llm/ollama_client.py`

The only model integration point.

It supports local Ollama and Ollama Cloud, logs every call, and retries once
when it needs JSON or Python but the model returns invalid output.

#### `module3_llm/llm_rewriter.py`

Builds the final test-generation prompt and calls `OllamaClient`.

It chooses the correct prompt template for the mutant class and injects RAG
context when available.

It also builds import hints, including special handling for methods.

#### `module3_llm/prompts/prompt_syntactic.txt`

Prompt template for simple mechanical mutants.

#### `module3_llm/prompts/prompt_sdl.txt`

Prompt template for statement-deletion mutants.

#### `module3_llm/prompts/prompt_semantic.txt`

Prompt template for realistic LLM-generated bugs.

#### `module3_llm/prompts/prompt_hom.txt`

Prompt template for higher-order mutants.

#### `module3_llm/generated_tests/`

Audit folder containing every generated test attempt.

The current workspace has many files here. Naming pattern:

```text
<mutation_class>_<function>_<hash>_<condition>_a<attempt>.py
```

Example:

```text
sdl_bulk_discount_00aa7bbf25_RAG_a1.py
```

Meaning:

- SDL mutant
- function `bulk_discount`
- unique hash `00aa7bbf25`
- RAG condition
- attempt 1

#### `module3_llm/llm_calls.jsonl`

JSON Lines call log. Each line records one model call with purpose, model,
temperature, token counts when available, and timing.

Used for RQ4 cost analysis.

### `agentic/`

Thin "agent" wrappers around the modules.

These are not autonomous magical agents. They are regular Python files that
organize the workflow.

#### `agentic/mutation_agent.py`

Calls module 1 and writes the shared surviving-mutant handoff.

#### `agentic/knowledge_agent.py`

Builds the RAG index and writes an index manifest.

#### `agentic/retrieval_agent.py`

Retrieves chunks for mutants and writes `module2_rag/rag_context.json`.

#### `agentic/test_gen_agent.py`

Owns the one-retry loop.

For each mutant:

1. Build prompt.
2. Ask LLM for test.
3. Validate test.
4. If needed, retry once with feedback.
5. Save record and generated test.

#### `agentic/validation_agent.py`

Judges one generated test against one mutant.

It returns structured verdicts rather than a bare true/false.

### `module4_eval/`

Turns raw results into research metrics.

#### `module4_eval/metrics_logger.py`

Converts result records to dataframes and writes:

- `raw_<subject>.csv`
- `summary_<subject>.csv`
- `cost_<subject>.csv`

#### `module4_eval/compare_conditions.py`

Combines raw CSVs, answers RQ1-RQ4, and creates figure PNGs.

#### `module4_eval/validator.py`

Audits whole result sets for suspicious patterns.

Example warnings:

- kill rate suspiciously high
- too many generations failed
- a kill was recorded without original-code pass

#### `module4_eval/checkpoint.py`

Crash-safe checkpointing for long generation runs.

It writes an append-only JSONL side file while generation is running. If the
process crashes, rerunning the same command skips completed work.

#### `module4_eval/results/`

Committed result data.

Important files:

- `raw_ctxlib.csv`
- `summary_ctxlib.csv`
- `cost_ctxlib.csv`
- `records_ctxlib.json`
- `raw_sorts_focused.csv`
- `summary_sorts_focused.csv`
- `cost_sorts_focused.csv`
- `records_sorts_focused.json`
- `raw_schedule.csv`
- `summary_schedule.csv`
- `cost_schedule.csv`
- `rq_answers.json`

Note: the workspace currently has result files for `schedule` and
`sorts_focused`, but the local `subjects/` folder shown here may not contain
those subject directories.

#### `module4_eval/figures/`

Output folder for generated figures.

In this workspace it currently contains only `.gitkeep`, so figures may need
to be regenerated with:

```bash
python run_pipeline.py --repo ctxlib --phase evaluate
```

or by calling the evaluation module after raw CSVs exist.

### `frontend/`

Flask web UI.

#### `frontend/app.py`

The web application.

Routes include:

- `/`: home
- `/pipeline`: how it works
- `/research-questions`: results
- `/explore`: mutant browser
- `/explore/<mutant_id>`: one mutant detail page
- `/passed-tests`: generated tests that passed validation
- `/generate`: upload a `.py` file and start live generation
- `/generate/job/<job_id>`: job status
- `/generate/job/<job_id>/download`: download generated tests

The app is local and single-user.

#### `frontend/data.py`

Flask-free data layer.

It reads real JSON/CSV output files and prepares data for the UI. It does not
invent placeholder metrics.

#### `frontend/uploads/`

Generated upload storage for files submitted through the UI.

### `subjects/`

Subject repos are the codebases being tested.

#### `subjects/ctxlib/`

Small context-dependent benchmark.

Files:

- `billing.py`: billing helpers like `bulk_discount`, `member_price`, `late_fee`.
- `shipping.py`: delivery-day helper.
- `grading.py`: grade helpers.
- `rates.py`: constants and tables used by the helpers.
- `test_ctxlib.py`: intentionally shallow baseline tests.

This subject is designed so RAG has something meaningful to retrieve.

#### `subjects/user_demo_range_utils/`

Generated subject folder created by `generate_tests.py` for
`demo_range_utils.py`.

Contains:

- copied source file
- `test_bootstrap.py`
- `DESCRIPTION.md`

#### Configured but not currently present here

`config.yaml` also mentions:

- `sorts`
- `sorts_focused`
- `schedule`

The result files indicate experiments were run for `sorts_focused` and
`schedule`, but those subject folders are not present in this current Windows
workspace snapshot except through committed results.

### `generated_test_suites/`

Outputs from the single-file generator.

Current files:

- `mutants_user_demo_range_utils.json`: mutants produced for the demo file.
- `report_demo_range_utils.json`: generation report and per-mutant records.
- `test_demo_range_utils_generated.py`: final curated tests that killed mutants.

### `tests/`

Project verification tests.

#### `tests/smoke_all.py`

Offline smoke suite. It avoids network, ChromaDB, real Ollama, and mutmut.

It checks:

- SDL generator
- HOM combiner
- schema validation
- mutmut output parser
- fake Ollama client path
- prompt formatting
- one-retry agent loop
- metrics and figures
- core guards and srcmap
- input security
- checkpointing

Current file defines 11 checks, even though some older docs still say 9.

#### `tests/oracle_e2e.py`

End-to-end oracle test using a "perfect model" stand-in.

It proves the pipeline can kill mutants when given behaviorally correct tests.
It does not prove the real LLM is good.

### `paper/`

Research writing artifacts.

#### `paper/codekong_notes.md`

Research notes, hypothesis, RQs, method, and threats to validity.

#### `paper/CodeKong_RAG_Mutation_Testing.docx`

Draft paper document.

### `docker/`

Docker support files.

#### `docker/start.sh`

Entrypoint for the full Docker image. Starts Ollama, checks the model, then
starts the Flask app.

### Generated and environment folders

#### `venv/`

Python virtual environment. Not source code.

#### `__pycache__/`

Python bytecode cache folders. Not source code.

#### `.git/`

Git repository data.

#### `.claude/`, `.codex/`, `.agents/`

Tooling/session folders for AI/editor environments.

## 12. What Gets Generated

### During mutation

Generated:

```text
module1_mutation/_scratch/<subject>/
module1_mutation/surviving_mutants.json
```

Scratch folders are temporary copies.

`surviving_mutants.json` is the main mutant handoff for the research pipeline.

### During indexing

Generated:

```text
module2_rag/chroma_db/
module2_rag/index_manifest.json
```

The ChromaDB folder contains the searchable RAG memory.

### During retrieval

Generated:

```text
module2_rag/rag_context.json
```

This records the retrieved context chunks per mutant.

### During test generation

Generated:

```text
module3_llm/generated_tests/*.py
module3_llm/llm_calls.jsonl
module4_eval/results/_checkpoint_<repo>.jsonl
```

The checkpoint file is temporary and should disappear after successful
consolidation into `records_<repo>.json`.

### During metrics logging

Generated:

```text
module4_eval/results/raw_<repo>.csv
module4_eval/results/summary_<repo>.csv
module4_eval/results/cost_<repo>.csv
module4_eval/results/records_<repo>.json
```

### During evaluation

Generated:

```text
module4_eval/results/rq_answers.json
module4_eval/figures/fig1_mutation_score_before_after.png
module4_eval/figures/fig2_killrate_rag_vs_norag.png
module4_eval/figures/fig3_ablation_retry.png
module4_eval/figures/fig4_validrate_by_k.png
```

### During single-file generation

Generated:

```text
subjects/user_<module>/
generated_test_suites/mutants_user_<module>.json
generated_test_suites/report_<module>.json
generated_test_suites/test_<module>_generated.py
```

## 13. How To Read A Result Record

A record in `records_ctxlib.json` looks conceptually like this:

```json
{
  "mutant_id": "sdl_bulk_discount_00aa7bbf25",
  "mutation_class": "sdl",
  "condition": "RAG",
  "k": 5,
  "subject": "ctxlib",
  "status": "KILLED",
  "attempts": 1,
  "retry_used": false,
  "valid_test_produced": true,
  "validation": [...],
  "test_file": "...",
  "context_chunks": [...]
}
```

Important fields:

- `condition`: `RAG` or `NO_RAG`.
- `k`: how many chunks were retrieved. `null` for NO_RAG.
- `status`: final outcome.
- `attempts`: 1 or 2.
- `retry_used`: whether the second attempt was used.
- `valid_test_produced`: whether at least one test passed original code.
- `validation`: detailed pass/fail explanation.
- `context_chunks`: retrieved RAG evidence.

## 14. How To Read A Generated Test Filename

Example:

```text
semantic_bulk_discount_dfd032435f_RAG_a1.py
```

Meaning:

- `semantic`: mutation class
- `bulk_discount`: function
- `dfd032435f`: unique hash
- `RAG`: condition
- `a1`: first attempt

Example:

```text
sdl_bulk_discount_00aa7bbf25_NO_RAG_a2.py
```

Meaning:

- statement-deletion mutant
- `bulk_discount`
- NO_RAG condition
- second attempt after retry feedback

## 15. How The Web UI Works

Run:

```bash
python -m frontend.app
```

Open:

```text
http://localhost:5001
```

The UI does not run all experiments by itself. It mostly reads existing output
files.

### Home

Explains the project visually.

### How It Works

Plain-language walkthrough of mutation, RAG, generation, and validation.

### Results

Reads CSV/JSON results from `module4_eval/results/`.

If result files are missing, it should show empty states instead of fake
numbers.

### Explore

Shows mutants, diffs, AST view, attempts, and RAG chunks.

### Caught Bugs

Shows generated tests that produced valid tests, prioritizing killed mutants.

### Try It

Lets a user upload one `.py` file and generate tests through the same backend
as `generate_tests.py`.

## 16. Common Commands

### Run smoke tests

```bash
python tests/smoke_all.py
```

Expected current behavior: all checks pass.

### Run the web UI

```bash
python -m frontend.app
```

### Run the demo single-file generator

```bash
python generate_tests.py --file demo_range_utils.py --description "numeric range utilities" --limit 8 --skip-semantic --no-rag
```

### Inspect committed results

```bash
python run_pipeline.py --repo ctxlib --phase evaluate
```

### Inspect RAG memory

```bash
python view_rag.py ctxlib
```

### Full research-style run

In WSL2/Linux/macOS:

```bash
python run_pipeline.py --repo ctxlib --skip-mutmut
```

For native Windows, mutation phases are restricted. The UI and some smoke tests
can run on Windows, but full mutation experiments are meant for WSL2 or macOS.

## 17. Known Caveats And Hazards

### mutmut integration is currently a known issue

`HANDOFF.md` says mutmut 3.6 changed output and caused integration problems.
The committed research runs used `--skip-mutmut`, so the syntactic class is
missing from the main results.

Do not pretend the syntactic class was measured if it was skipped.

### ctxlib is synthetic

`ctxlib` was purpose-built to test context-dependent behavior. That is fine,
but it must be disclosed.

The honest finding is:

RAG helps strongly on code where important facts live elsewhere.

### The model is not Claude

The original design apparently imagined Claude. This implementation uses a
local Ollama model.

That means the absolute kill rates should not be compared to a Claude-backed
study.

The RAG vs NO_RAG comparison inside this repo is still internally meaningful
because both conditions use the same local model.

### Equivalent mutants can exist

Some mutants may behave the same as the original for all practical inputs.
Neither RAG nor NO_RAG can kill those.

### Do not run from `/mnt/c/...` in WSL

The project rewrites files during mutation. Windows-drive metadata caching can
make Python run stale bytecode. The guard refuses this setup for a reason.

### Native Windows cannot run mutmut properly

mutmut needs `fork()`. Use WSL2 or macOS for full mutation phases.

## 18. What To Say In A Presentation

Simple version:

"CodeKong evaluates whether retrieval helps an LLM write better regression
tests. It creates mutants, keeps only the ones the old tests missed, then asks
the LLM to write tests under two conditions: with and without retrieved
codebase context. A generated test only counts if it passes on the original
code and fails on the mutant. In our results, RAG helped a lot on
context-dependent code like `ctxlib`, tied on self-contained sorting code, and
did not help on the schedule library where the small local model struggled to
write valid tests."

Shorter version:

"We are not just asking AI to write tests. We are proving whether each generated
test catches a real injected bug."

## 19. Mental Model For The Team

Think of CodeKong as five workers:

1. Mutator: "I will plant bugs."
2. Old test suite: "I will tell you which bugs I already catch."
3. Retriever: "I will find useful codebase facts for the LLM."
4. Test writer: "I will ask the LLM to write a pytest test."
5. Judge: "I will only approve the test if it passes good code and fails bugged code."

The judge is the most important worker. Without the judge, the project would
just produce plausible-looking tests. With the judge, it produces audited
evidence.

## 20. Quick Debugging Guide

### The model returns nonsense

Check:

- Is Ollama running?
- Is `qwen2.5-coder:7b` pulled in the same Ollama store?
- Does `module3_llm/llm_calls.jsonl` show calls?
- Is `GEN_FAILED` high in results?

### Generated tests fail on original code

That is `INVALID_TEST`.

Common reason:

The model guessed a business rule instead of retrieving the actual constant.

Example:

`bulk_discount(10) == 0.1` was invalid because the real value is `0.04`.

### RAG does not help

Check whether the correct answer actually depends on external context.

If the function is self-contained, RAG may not add anything useful.

### Results look too good

Run or inspect:

```text
module4_eval/validator.py
```

Suspiciously high kill rates can mean the validator is wrong or the mutant was
not actually applied.

### Generated tests import the wrong thing

Check:

```text
module3_llm/llm_rewriter.py
```

Especially `make_import_hint()`. Methods need class imports, not method imports.

### A long run crashed

Check for:

```text
module4_eval/results/_checkpoint_<repo>.jsonl
```

Rerun the same command. The checkpoint system should skip already completed
units.

## 21. What The Team Should Understand Deeply

The project is not mainly a web app. The web app is a viewer and demo surface.

The real core is this contract:

```text
surviving mutant + generated test -> validator -> KILLED/SURVIVED/INVALID/GEN_FAILED
```

Everything else supports that contract.

The scientific value comes from the fact that every kill is checked by running
real code twice:

1. once without the mutant
2. once with the mutant applied

That is why the generated tests are more than text. They are measured behavior.

## 22. Current Workspace Notes

Observed while writing this guide:

- `module4_eval/results/` contains committed results for `ctxlib`,
  `sorts_focused`, and `schedule`.
- `subjects/` currently contains `ctxlib` and `user_demo_range_utils`.
- `module3_llm/generated_tests/` currently contains many generated test attempt
  files.
- `generated_test_suites/` contains the demo output for `demo_range_utils`.
- `module4_eval/figures/` currently only shows `.gitkeep` in this workspace,
  even though evaluation code can generate figures.
- The git worktree already had uncommitted/untracked changes before this guide
  was added.

## 23. Where To Start Reading The Code

Recommended order:

1. `config.yaml`
2. `run_pipeline.py`
3. `generate_tests.py`
4. `core/schema.py`
5. `module1_mutation/mutant_normalizer.py`
6. `agentic/test_gen_agent.py`
7. `agentic/validation_agent.py`
8. `module2_rag/rag_indexer.py`
9. `module2_rag/retriever.py`
10. `module4_eval/metrics_logger.py`
11. `frontend/data.py`
12. `frontend/app.py`

That path follows the actual data flow and avoids getting lost in UI code too
early.

## 24. Final Summary

CodeKong is a local, free, mutation-testing research pipeline.

It creates bugs, finds which bugs the old tests missed, asks a local LLM to
write new tests, and compares whether retrieved codebase context helps.

The most important sentence in the whole project is:

```text
A generated test counts only if it passes on the original code and fails on the mutant.
```

If your team remembers that, the rest of the architecture becomes much easier
to understand.
