# AGENTS.md

## Mission
People in Ukraine pay for, or are refused, care that is free under the NSZU Programme of Medical Guarantees, because they do not know what is free and where. **Гарантовано** turns a plain-language need into NSZU package IDs and shows the nearest contracted facilities from NSZU open data (data.gov.ua), plus an official rights card.

## Rules for every AI agent and human in this repo
1. Read `README.md`, `docs/ARCHITECTURE.md` and your GitHub issue first. Work **only** in the files your issue owns.
2. **Python is the language for all logic** (data, search, LLM, app). Other languages (HTML/CSS/JS snippets) are allowed **only for visualisation** inside Streamlit components, never for logic. No JS/TS source files in the repo (CI checks this).
3. Never push to `main`. Branch `feat-<issue-id>-<short-name>` → PR → CI green → `@codex review` → Nazar merges.
4. No secrets in code, logs, commits or screenshots. Keys come from env vars / Streamlit secrets only.
5. Never invent numbers, sources or test results. Mark unknowns `UNVERIFIED`. Synthetic data is labelled "Demo data".

## Design principles
- **KISS** — the simplest thing that makes the flagship scenario work.
- **DRY** — every path, threshold, keyword list and model id lives in `garantovano/config.py`.
- **SOLID / modular monolith, microservice-ready** — modules talk only through `garantovano/models.py` types: `data` (adapter for files) · `match` (LLM port + validation) · `search` (pure functions) · `app.py` (UI only). No module imports Streamlit except `app.py`.
- **The model only understands; deterministic code decides.** The LLM returns package IDs from `data/packages.csv`; results always come from the open dataset; rights text comes only from `data/rights.json`.
- **Fail closed** — invalid model output, unknown id, low confidence, refusal, timeout or any exception → manual package picker, never a guess, never a crash.
- **Emergency first** — `config.EMERGENCY_KEYWORDS` is checked deterministically before the model; if hit, the UI shows "Дзвоніть 103" before any result.
- **TDD for risky logic** — `match` and `search` have specs in `tests/`; make them pass, then remove the xfail marker.
- No god files (> ~200 lines). Type hints on public functions.

## Review guidelines
Codex: flag only real problems; ignore style nits. Treat these as **P0**:
- An API key, token or secret anywhere in the diff (code, config, notebooks, logs, `.streamlit/secrets.toml`).
- LLM output used without validation against `data/packages.csv` (ids, count 1–3, confidence ≥ `config.MIN_CONFIDENCE`).
- Any path where model text is shown to the user as an answer or medical advice, or where results/rights come from the model instead of `data/`.
- An exception path in `match` (timeout, API error, refusal, invalid JSON) that crashes or returns packages instead of `needs_picker=True`.
- Emergency keywords not forcing `emergency=True`, or the UI showing results before the "103" warning when `emergency` is True.

Treat these as **P1**:
- User text concatenated into the system prompt (prompt injection) or no input length limit (`config.MAX_INPUT_CHARS`).
- `unsafe_allow_html=True` with user-controlled content.
- Business logic in `app.py`; `search.py`/`match.py` importing Streamlit; constants duplicated outside `config.py`.
- New logic without tests, or the xfail marker left on a module the PR implements.
- Logic written in a language other than Python.
- UI claims not backed by data (e.g. "гарантовано безкоштовно" without `config.DISCLAIMER`), or a result without its data source.
