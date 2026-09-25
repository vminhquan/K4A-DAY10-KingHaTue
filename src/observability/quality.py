from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the required Great Expectations 1.x gate on a dataframe.

    The ephemeral context avoids creating mutable GX project state, which keeps
    repeated baseline/corruption/repair runs reproducible.
    """
    import great_expectations as gx

    required = {"paper_id", "title", "text_for_embedding", "summary", "age_days", "published"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Quality gate missing required columns: {missing}")
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name="papers_source")
    asset = source.add_dataframe_asset(name="papers_asset")
    batch_definition = asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df.copy()})

    expectations = [
        ("row_count_between_5_and_5000", gx.expectations.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)),
        ("paper_id_not_null", gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id")),
        ("title_not_null", gx.expectations.ExpectColumnValuesToNotBeNull(column="title")),
        ("text_for_embedding_not_null", gx.expectations.ExpectColumnValuesToNotBeNull(column="text_for_embedding")),
        ("paper_id_unique", gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id")),
        ("summary_length_at_least_30", gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30, max_value=None)),
    ]
    checks = []
    for name, expectation in expectations:
        result = batch.validate(expectation)
        details = result.result if isinstance(result.result, dict) else {}
        checks.append(
            {
                "name": name,
                "success": bool(result.success),
                "unexpected_count": int(details.get("unexpected_count", 0) or 0),
            }
        )
    freshness = _freshness_payload(df, settings)
    gx_success = all(check["success"] for check in checks)
    payload = {
        "report_name": report_name,
        "success": gx_success and freshness["is_fresh"],
        "gx_success": gx_success,
        "gx_version": getattr(gx, "__version__", "unknown"),
        "checks": checks,
        "freshness": freshness,
    }
    if report_name == "baseline":
        path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        path = settings.paths.corrupted_quality_report
    else:
        path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Persist a standalone freshness SLA report for the supplied dataset."""
    payload = _freshness_payload(df, settings)
    write_json(report_path, payload)
    return payload


def _freshness_payload(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    if "age_days" not in df or "published" not in df:
        raise ValueError("Freshness monitoring requires age_days and published columns.")
    ages = pd.to_numeric(df["age_days"], errors="coerce")
    published = pd.to_datetime(df["published"], errors="coerce", utc=True)
    total_rows = int(len(df))
    stale_mask = ages > settings.freshness_threshold_days
    stale_rows = int(stale_mask.fillna(True).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    latest = published.max()
    oldest = published.min()
    return {
        "freshness_threshold_days": settings.freshness_threshold_days,
        "latest_published": latest.date().isoformat() if not pd.isna(latest) else None,
        "oldest_published": oldest.date().isoformat() if not pd.isna(oldest) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "max_stale_ratio": 0.25,
        "is_fresh": bool(total_rows and stale_ratio <= 0.25),
    }
