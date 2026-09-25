# Corruption and Idempotent Repair Report

## Three-state performance comparison

| Metric | Baseline | Corrupted | Repaired | Repaired - Baseline |
| --- | ---: | ---: | ---: | ---: |
| retrieval_hit_rate | 1.000 | 0.700 | 1.000 | 0.000 |
| mean_token_f1 | 1.000 | 0.800 | 1.000 | 0.000 |
| judge_accuracy | 1.000 | 0.800 | 1.000 | 0.000 |
| mean_judge_score | 5 | 4.400 | 5 | 0 |

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| GX quality success | N/A | **False** | **True** |
| Combined quality/freshness success | N/A | **False** | **True** |
| Stale rows / total | N/A | 6 / 23 | 1 / 24 |
| Stale ratio | N/A | 0.261 | 0.042 |
| Is fresh | N/A | **False** | **True** |

## Interpretation

The corrupted state is intentionally built with six logged failure modes: missing
recent records, blank summaries, injected noise, truncated titles, stale dates,
and duplicate rows. The quality gate should reject this state before serving it.
Repair rebuilds the clean dataframe only from preserved raw records, then rebuilds
the index and evaluates the unchanged benchmark. Therefore, repeated repair runs
are idempotent: they overwrite derived artifacts with the same source-derived
baseline state rather than mutating already-corrupted data.
