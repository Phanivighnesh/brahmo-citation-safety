# BRAHMO Citation Safety Engine

> **Make AI Safe for Lawyers** — A deterministic citation verification pipeline for Indian legal text.

Catches hallucinated citations, flags repealed IPC/CrPC sections, and verifies real cases against the Indian Kanoon database — before a lawyer ever sees the AI's output.

---

## Why This Exists

In 2023, attorneys filing Mata v. Avianca cited six cases fabricated by ChatGPT. Every one was fictional. The lawyers were sanctioned. Their names are now permanently linked to the first major AI citation scandal.

In India, the problem compounds: the entire criminal code changed on 1 July 2024. The IPC (1860) became the BNS (2023). LLMs still cite "Section 420 IPC" — which is repealed. This engine catches both failure modes.

---

## Architecture (30-second summary)

```
Input text (AI-generated legal memo)
  │
  ├─ Stage 0: section_normalizer   → IPC/CrPC/IEA  →  BNS/BNSS/BSA  (~5ms, DB lookup)
  ├─ Stage 1: citation_extractor   → regex scan for 6 Indian citation formats
  ├─ Stage 2: hallucination_detector → 4 rule-based pre-filter checks (no API cost)
  ├─ Stage 3: citation_verifier    → Indian Kanoon API (parallel, cached)
  └─ Stage 4: citation_annotator   → badge injection + report

Output: annotated text  +  PipelineReport
```

---

## Setup

### Prerequisites

- Python 3.10+
- (Optional) Indian Kanoon API key — free at [api.indiankanoon.org/signup](https://api.indiankanoon.org/signup/) (₹500 credit)

### Install

```bash
git clone <repo>
cd brahmo-citation-safety

pip install -r requirements.txt

# Optional: add your IK API key
cp .env.example .env
# Edit .env → INDIAN_KANOON_API_KEY=your_key
```

The SQLite database is created automatically on first run — no Supabase account needed locally.
To use Supabase in production, see `docs/architecture.md § Database`.

---

## Run the Demo

```bash
python demo/run_demo.py
```

Without an IK API key the engine runs in **mock mode** — citations are marked `⚠️ UNVERIFIED` instead of `✅ VERIFIED`.  All pre-filter catches (future year, impossible volume) still fire deterministically with no API key.

With an IK key:
```bash
export INDIAN_KANOON_API_KEY=your_key_here
python demo/run_demo.py
```

---

## Run Tests

```bash
python -m pytest tests/ -v
```

- `tests/test_extractor.py`  — 16 tests covering all 6 citation formats
- `tests/test_detector.py`   — 17 tests covering all 4 pre-filter rules
- `tests/test_normalizer.py` — 35 tests covering all 30 section mappings

All 68 tests pass with zero external dependencies.

---

## Use the Pipeline Directly

```python
from src.database import get_connection
from src.pipeline import run_pipeline

conn = get_connection()

ai_output = """
In Siddharth v. State of UP (2021) 10 SCC 1, the Court held X.
In (2028) 3 SCC 45, the Court supposedly held Y.
Section 420 IPC applies here.
"""

annotated_text, report = run_pipeline(ai_output, conn=conn, mock_mode=True)

print(annotated_text)
print(f"Total: {report.total} | Removed: {report.removed} | Cost: ₹{report.total_cost_inr}")
```

---

## Demo Scenarios

| Scenario | Input | Engine catches |
|---|---|---|
| 1 — Hallucinated citation | AI memo with 2 fabricated SCC citations | `❌ REMOVED` — case not in IK |
| 2 — Repealed law | Complaint citing Section 420 IPC | `⚠️ ALERT` → converted to Section 318 BNS |
| 3 — Impossible citation | `(2028) 3 SCC 45` and `(2024) 47 SCC 123` | `❌ REMOVED` — pre-filter, no API call |
| 4 — Format errors | `SCC Online` vs `SCC OnLine`, `Delhi` vs `Del` | `⚠️ CORRECTED` |

---

## Project Structure

```
brahmo-citation-safety/
├── README.md
├── .env.example              ← Copy to .env, add your API keys
├── requirements.txt
├── db/
│   ├── schema.sql            ← CREATE TABLE statements
│   ├── seed.sql              ← 30 mappings + 6 citation patterns
│   └── citations.db          ← Auto-created SQLite (gitignored)
├── src/
│   ├── database.py           ← SQLite bootstrap + connection
│   ├── types.py              ← Shared dataclasses
│   ├── citation_extractor.py ← Stage 1: regex extraction
│   ├── hallucination_detector.py ← Stage 2: pre-filter rules
│   ├── citation_verifier.py  ← Stage 3: IK API + caching
│   ├── section_normalizer.py ← Stage 0: IPC→BNS conversion
│   ├── citation_annotator.py ← Stage 4: badge injection + report
│   └── pipeline.py           ← Orchestrator
├── demo/
│   └── run_demo.py           ← 4 scenario demo
├── tests/
│   ├── test_extractor.py
│   ├── test_detector.py
│   └── test_normalizer.py
└── docs/
    ├── architecture.md
    └── data_sources.md
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `INDIAN_KANOON_API_KEY` | No (mock mode without) | IK API key for real verification |
| `LLM_API_KEY` | No (for LLM integration only) | Any LLM provider key |

---

*BRAHMO Citation Safety Engine — v1.0*
