# LA 311 Sanitation Requests 2024 — Illegal Dumping Service Analysis

**Question.** How well did Los Angeles Sanitation (LASAN) keep up with residents' illegal-dumping reports in 2024 — how much came in each week, how much got closed, what stayed open, and where/when the service falls behind?

**Data.** MyLA311 Service Request Data 2024 (City of Los Angeles open data), 1,442,297 requests created 1 Jan – 31 Dec 2024, status as of 18 Jul 2025.
Downloaded from the Hack for LA mirror: https://huggingface.co/datasets/311-data/2024 (`2024.parquet`, GPL-3.0).
The official portal (data.lacity.org) was not reachable from Vietnam (HTTP 403), so the mirror was used.

**Scope.** LASAN waste-collection request types: Bulky Items, Illegal Dumping Pickup, Metal/Household Appliances, Electronic Waste — 947,425 requests. Deep dive on **Illegal Dumping Pickup** (114,263 requests), the complaint-driven type; the other three are scheduled pickups used as a benchmark.

## Files
| File | What it is |
|---|---|
| `queries.sql` | All SQL (DuckDB). Each `-- name:` block is one question |
| `run_analysis.py` | Runs every query, saves `results/*.csv`, draws `charts/*.png`, writes `findings.json` |
| `results/` | One CSV per query — every number in `findings.md` comes from these |
| `charts/` | Weekly intake vs. closures + backlog; unresolved share by council district; weekday pattern |
| `findings.md` | Insights, recommendations and caveats |

## Reproduce
```bash
pip install duckdb pandas matplotlib
python run_analysis.py --data ../2024.parquet
```
Runs in a few seconds on a laptop (DuckDB reads the parquet file directly).

## Method notes
- *Resolved* = has a `ClosedDate` (includes cancelled requests). *Unresolved* = no `ClosedDate` at the snapshot.
- Days to close = `ClosedDate − CreatedDate`, computed on `Status = 'Closed'` only.
- Weekly backlog = requests created before the end of the week and not closed by then (full Mon–Sun weeks).
- Data-quality checks (`results/data_quality.csv`): 0 duplicate request numbers, 0 closed-before-created, 102 in-scope rows marked Closed without a closed date.

## Verification
All 30 headline figures in `findings.md` were re-computed independently with separate pandas code (no shared SQL).
29 matched on the first pass; the one mismatch (phone share of reports, 52.3% → 51.9%) came from a denominator that excluded small channels and was fixed in `queries.sql`.
