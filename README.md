# genai-eval-framework — a pluggable LLM evaluation harness

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97757?logo=anthropic&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20models-000000?logo=ollama&logoColor=white)
![Status](https://img.shields.io/badge/status-scaffolding-orange)

A small, provider-agnostic framework for benchmarking large language models
through a common adapter interface, with parallel evaluation and on-disk response
caching so runs are fast and reproducible.

> **Status:** scaffolding / design blueprint. The model adapters, the parallel
> MMLU evaluator, and the cache are implemented and the cache is unit-tested. The
> shared base classes (`BaseEvaluator`, `BaseModelAdapter`) that the concrete
> components subclass are the next pieces to land — see
> [Architecture](#architecture--how-it-works) and [Roadmap](#roadmap).

---

## Overview & Aim

Comparing models fairly means running the *same* prompts through every model,
parsing answers consistently, and not paying (in latency or API cost) to
re-evaluate identical prompts. This framework factors those concerns apart:

- **Models** are hidden behind a uniform adapter (`complete(prompt, **kw) → {"text": ...}`),
  so a benchmark never knows whether it is talking to a hosted API or a local model.
- **Evaluators** own a dataset, an answer-parsing rule, and an aggregation, and
  run independently of which model they score.
- **Caching** sits underneath, keyed by `(prompt, model)`, so repeated runs hit
  disk instead of the network.

This separation is what lets the same MMLU harness score a frontier API model and
a locally-hosted open model with no code change.

---

## Architecture / How It Works

```
            ┌──────────────────────────────┐
 dataset ──▶│        MMLUEvaluator         │
            │  (ThreadPoolExecutor, 4 wkrs)│
            │  evaluate_single() per item  │
            └───────────────┬──────────────┘
                            │ model.complete(prompt, max_tokens)
                            ▼
            ┌──────────────────────────────┐
            │     Model adapter (uniform)  │
            │  AnthropicAdapter | Ollama   │
            └───────────────┬──────────────┘
                            │ (prompt, model) key
                            ▼
            ┌──────────────────────────────┐
            │  EvalCache  (sha256 → .json) │
            └──────────────────────────────┘
```

### Parallel evaluator

[`MMLUEvaluator`](src/evaluators/mmlu.py) loads a multiple-choice dataset, fans
the items out across a `ThreadPoolExecutor` (4 workers), and for each item:

1. prompts the model for a single-token answer,
2. extracts the first `A`/`B`/`C`/`D` token via regex,
3. records a boolean `correct`.

Aggregation reduces to `accuracy = mean(correct)`. Thread-level parallelism is the
right tool here because each evaluation is I/O-bound on a model call.

### Model adapters

A concrete adapter implements `_call_api(prompt, **kw)` and returns `{"text": ...}`:

- [`AnthropicAdapter`](src/models/anthropic_adapter.py) — wraps the official
  `anthropic` SDK (`messages.create`), reading `ANTHROPIC_API_KEY` from the
  environment and defaulting to `claude-3-haiku-20240307`.
- [`OllamaAdapter`](src/models/ollama_adapter.py) — talks to a local Ollama
  server over `POST /api/generate` (stdlib `urllib`, no extra dependency),
  defaulting to `llama3:8b`.

### Response cache

[`EvalCache`](src/utils/cache.py) hashes `(prompt, model)` with SHA-256 and stores
each response as a JSON file under `.eval_cache/`. A cache miss returns `None`; a
hit returns the stored payload — making re-runs deterministic and free.

---

## Tech Stack & Tools

- **Python 3.11+** with `concurrent.futures` for parallelism
- **anthropic** — official SDK for the Claude adapter
- **Ollama** HTTP API — local open-model serving (via stdlib `urllib`)
- `hashlib` / `json` / `os` — dependency-free disk cache
- **pytest** — unit tests

---

## Project Structure

```
genai-eval-framework/
├── src/
│   ├── evaluators/
│   │   └── mmlu.py               # MMLUEvaluator: parallel run + accuracy aggregate
│   ├── models/
│   │   ├── anthropic_adapter.py  # Claude via the anthropic SDK
│   │   └── ollama_adapter.py     # local models via the Ollama HTTP API
│   └── utils/
│       └── cache.py              # EvalCache: sha256((prompt, model)) → JSON
├── tests/
│   └── test_utils.py            # cache hit/miss behavior (tempdir-isolated)
└── docs/
    └── BENCHMARKS.md            # reference leaderboard numbers (see note below)
```

---

## Key Features

- **Uniform adapter contract** — benchmarks are model-agnostic.
- **Hosted + local out of the box** — Claude (API) and Ollama (local) adapters.
- **Parallel evaluation** — `ThreadPoolExecutor` over I/O-bound model calls.
- **Deterministic, free re-runs** — content-addressed JSON cache keyed by
  `(prompt, model)`.
- **Single-token MC parsing** — robust `A/B/C/D` extraction for MMLU-style tasks.

---

## Results

This repository is an **evaluation harness, not a published benchmark run**. The
MMLU evaluator currently loads a small built-in stub dataset for wiring/tests, so
it does not yet produce headline accuracy figures.

> **Note on `docs/BENCHMARKS.md`:** that file lists *illustrative reference
> leaderboard numbers* (e.g. for frontier API models) to document the intended
> output format. They are **not** measurements produced by this code and are not
> claimed as results of this project.

---

## Getting Started

```bash
pip install anthropic
python -m pytest tests/ -q          # cache unit tests

export ANTHROPIC_API_KEY=sk-...     # for the Claude adapter
# ollama serve                       # for the local adapter (separate process)
```

```python
from src.models.anthropic_adapter import AnthropicAdapter
from src.evaluators.mmlu import MMLUEvaluator

model = AnthropicAdapter(model="claude-3-haiku-20240307")
acc = MMLUEvaluator(model).run(max_samples=50)   # {"accuracy": ...}
```

---

## Challenges

- **Provider heterogeneity** — hosted SDKs and local HTTP servers expose very
  different shapes; the adapter contract normalizes them to `{"text": ...}`.
- **Answer extraction** — free-form generations must be parsed to a single choice
  without over-counting; a strict first-`[ABCD]` regex keeps this honest.
- **Cost & reproducibility** — the content-addressed cache removes both repeated
  spend and run-to-run nondeterminism for identical prompts.

## Roadmap

- Ship the `BaseEvaluator` / `BaseModelAdapter` base classes the concrete
  components subclass (the abstract `complete()` / caching glue).
- Wire the real MMLU dataset (HuggingFace `datasets`) behind `load_dataset()`.
- Add HumanEval / GSM8K evaluators reusing the same adapter contract.
- Integrate the cache into the adapter call path automatically.
- Temperature/seed pinning and per-run metadata for fully reproducible reports.

## Conclusion

`genai-eval-framework` is the skeleton of a clean, provider-agnostic LLM
evaluation stack: uniform adapters, parallel scoring, and a content-addressed
cache. The plumbing is in place; the next step is the shared base layer and a real
dataset behind the evaluator.
