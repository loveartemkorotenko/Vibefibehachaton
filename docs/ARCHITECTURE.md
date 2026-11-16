# Architecture — Гарантовано

Python modular monolith, ports and adapters, microservice-ready: each module can become a service without changing its contract.

```
             user text + region/address
                        │
        ┌───────────────▼────────────────┐
        │ app.py (Streamlit, UI only)    │  Акім
        └──┬──────────────┬───────────┬──┘
           │              │           │
  ┌────────▼───────┐ ┌────▼──────┐ ┌──▼───────────────┐
  │ match.py       │ │ search.py │ │ data.py          │
  │ need → ids     │ │ pure:     │ │ reads data/*.csv │
  │ validate,      │ │ filter +  │ │ rights.json      │
  │ fail closed,   │ │ distance  │ │ meta.json        │
  │ 103 rule       │ │           │ │                  │
  └──────┬─────────┘ └───────────┘ └────────▲─────────┘
         │ LLMPort                          │
  ┌──────▼──────────────┐       ┌───────────┴───────────┐
  │ GemmaClassifier     │       │ scripts/ingest.py     │
  │ (default, Gemini API│       │ data.gov.ua → data/   │
  │ AnthropicClassifier │       │                       │
  │ (fallback, Claude)  │       │                       │
  └─────────────────────┘       └───────────────────────┘
   Діма                          done (weekly NSZU refresh)
```

## Flow (flagship: «Я вагітна, Оболонь, де народжувати безкоштовно?»)
1. `match.match(text, packages, default_classifier())` — Gemma 3 27B by default (`GARANTOVANO_PROVIDER=anthropic` switches to Claude):
   - keyword emergency check (deterministic);
   - the model chooses ids from the package list only;
   - validation: ids exist, 1–3 of them, confidence ≥ 0.6. Otherwise `needs_picker=True`.
2. If `emergency`, the UI shows the red «Дзвоніть 103» block first.
3. If `needs_picker`, the user picks packages by hand. The flow never stops.
4. `search.search(facilities, ids, origin, region)` keeps facilities that have **all** chosen packages and sorts them by distance from the origin. The origin is the geocoded address or the settlement centroid.
5. The UI shows a map, cards and a rights card from `data/rights.json`. It also shows the disclaimer and the data source with its date.

## Contracts (`garantovano/models.py`)
`Package`, `Facility`, `LLMClassification` (untrusted), `MatchResult`, `SearchResult`. The specs are `tests/test_match.py` and `tests/test_search.py`.

## Ownership (one owner per file, no cross-edits)
| Files | Owner | Issue |
|---|---|---|
| `garantovano/match.py`, `tests/test_match.py` | Діма | D1 |
| `pages/1_Де_бракує_допомоги.py`, `garantovano/analytics.py`, `scripts/smoke_match.py` | Діма | D2, D1 |
| `garantovano/search.py`, `tests/test_search.py` | Акім | A1 |
| `app.py` main flow, `.streamlit/`, deploy | Акім | A2, A3 |
| `data/rights.json`, `docs/`, deck | Назар | N1, N3 |
| `config.py`, `models.py`, `data.py`, `scripts/`, CI | Назар (integration owner) | — |

Need a change in someone else's file? Ask the owner in the issue. Do not edit it yourself.

## Data
NSZU on data.gov.ua (no auth). Built by `python scripts/ingest.py`, committed under `data/` so the demo works offline.
- `packages.csv`: 85 packages.
- `facilities.csv`: 10 189 divisions with lat/lng and their package ids. 98.9% of the 25 333 contract rows matched coordinates.
- `meta.json`: source URLs, build time, coverage.

## Extension points (for the pitch: scales without a rewrite)
- **New channel** (Telegram bot, partner API): a new adapter calls the same `match` + `search`.
- **New dataset** (Доступні ліки pharmacies, which already have lat/lng; Kyiv shelters): a new loader in `data.py` and a new layer in the UI.
- **Different LLM or model:** change `GARANTOVANO_MODEL`, or add another `LLMPort` adapter.
- **Customer rules:** keywords, thresholds and limits live in `config.py`.
