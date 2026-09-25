from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question

def main() -> None:
    """Run the clean, offline-capable baseline from source to report."""
    settings = load_settings()
    records = fetch_source_records(settings)
    clean = build_clean_dataframe(records, now_utc())
    write_csv(clean, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean.to_dict(orient="records"))

    quality = run_data_quality_checks(clean, settings, "baseline")
    freshness = build_freshness_report(clean, settings, settings.paths.freshness_report)
    if not quality["success"]:
        raise RuntimeError("Baseline quality gate failed; refusing to index untrusted data.")

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(clean, settings.paths.eval_testset)
    else:
        test_set = read_json(settings.paths.eval_testset)
    index = LocalEmbeddingIndex.build(clean, settings, settings.paths.embeddings_json)
    evaluation = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    demo = []
    for item in test_set[:2]:
        result = answer_question(item["question"], settings, index)
        demo.append(
            {
                "question": item["question"],
                "answer": result.answer,
                "retrieved_doc_ids": result.retrieved_doc_ids,
            }
        )
    write_json(settings.paths.demo_answers, demo)
    generate_phase1_report(
        settings.paths.baseline_report,
        {
            "mode": "live_api" if settings.refresh_source else "offline_snapshot",
            "raw_records": len(records),
            "clean_records": len(clean),
            "embedding_model": settings.embedding_model,
            "collection_name": settings.baseline_collection_name,
        },
        evaluation.summary,
        quality,
        freshness,
    )
    print(
        "Phase 1 complete: "
        f"{len(clean)} clean documents, hit_rate={evaluation.summary['retrieval_hit_rate']:.3f}, "
        f"token_f1={evaluation.summary['mean_token_f1']:.3f}"
    )
