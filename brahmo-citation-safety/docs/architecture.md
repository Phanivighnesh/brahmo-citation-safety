# Architecture: BRAHMO Citation Safety Engine

## Data Flow

```
Input Text
  │
  ├─[0] section_normalizer  (DB hash-map lookup, ~5ms)
  ├─[1] citation_extractor  (regex, 6 patterns from DB)
  ├─[2] hallucination_detector (4 rules, no API)
  ├─[3] citation_verifier   (IK API, parallel threads, cached)
  └─[4] citation_annotator  (badge injection + PipelineReport)
```

## Key Decisions

**SQLite locally, Supabase in production** — same schema.sql/seed.sql works for both. Migration = one connection string swap.

**DB-driven patterns** — Adding a new citation format = one INSERT into citation_patterns. Zero code changes.

**Thread-per-worker DB connections** — SQLite is not thread-safe with shared connections. Each parallel IK worker opens its own connection.

**UNVERIFIED ≠ REMOVED** — Per spec: "Not in IK" ≠ "Hallucinated". Only pre-filter flags OR (IK not found AND pre-filter suspicious) = REMOVED.

**Longest-match-first normalization** — Section 304A IPC regex is tested before Section 304 IPC to avoid partial matches.

## Database Tables

| Table | Rows | Purpose |
|---|---|---|
| citation_patterns | 6 | Regex patterns for Indian citation formats |
| section_mappings | 30 | IPC→BNS / CrPC→BNSS / IEA→BSA conversions |
| verification_cache | dynamic | Cache IK results, avoid redundant API calls |

## Pre-filter Rules (no API cost)

| Rule | Condition | Result |
|---|---|---|
| Future year | year > 2026 | ❌ REMOVED immediately |
| Impossible volume | SCC/SCR vol > 25 | ❌ REMOVED immediately |
| Impossible page | page > 5000 | ⚠️ SUSPICIOUS → sent to IK |
| Pre-modern | year < 1900 | ⚠️ SUSPICIOUS → sent to IK |
