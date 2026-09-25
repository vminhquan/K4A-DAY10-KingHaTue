from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import main as run_phase1
from retrieval.index import LocalEmbeddingIndex

def main() -> None:
    """Demonstrate corruption detection, source-based repair, and recovery."""
    settings = load_settings()
    if not settings.paths.clean_json.exists() or not settings.paths.baseline_metrics.exists():
        run_phase1()
    baseline = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    corrupted = corrupt_clean_dataframe(baseline, settings.paths.corruption_log)
    write_csv(corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted.to_dict(orient="records"))
    corrupted_quality = run_data_quality_checks(corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )
    if corrupted_quality["success"]:
        raise RuntimeError("Synthetic corruption was not detected by the quality gate.")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_evaluation = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )

    # Repair starts from the immutable raw artifact, never from corrupted rows.
    repaired = build_clean_dataframe(load_raw_records(settings.paths.raw_records_json), now_utc())
    write_csv(repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired.to_dict(orient="records"))
    repaired_quality = run_data_quality_checks(repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )
    if not repaired_quality["success"]:
        raise RuntimeError("Repair quality gate failed; repair artifact is not trustworthy.")
    repaired_index = LocalEmbeddingIndex.build(repaired, settings, settings.paths.repaired_embeddings_json)
    repaired_evaluation = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print(
        "Corruption flow complete: "
        f"baseline={baseline_metrics['retrieval_hit_rate']:.3f}, "
        f"corrupted={corrupted_evaluation.summary['retrieval_hit_rate']:.3f}, "
        f"repaired={repaired_evaluation.summary['retrieval_hit_rate']:.3f}"
    )
