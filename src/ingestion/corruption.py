from __future__ import annotations

from math import ceil

import pandas as pd

from core.utils import write_json


def _rebuild_embedding_text(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["summary_chars"] = result["summary"].fillna("").astype(str).str.len()
    result["text_for_embedding"] = result.apply(
        lambda row: "\n".join(
            [
                f"Title: {row['title']}",
                f"Authors: {row['authors_joined']}",
                f"Published: {row['published']}",
                f"Categories: {row['categories_joined']}",
                f"Summary: {row['summary']}",
            ]
        ),
        axis=1,
    )
    return result

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Inject six deterministic failure modes into a clean dataframe.

    Determinism is intentional: every baseline has the same corrupted counterpart,
    so degradation and repair can be compared honestly without random variation.
    """
    required = {
        "paper_id", "title", "summary", "published", "age_days", "authors_joined",
        "categories_joined", "text_for_embedding",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Cannot corrupt dataframe missing columns: {missing}")
    if len(df) < 10:
        raise ValueError("Corruption suite requires at least ten clean records.")

    ordered = df.sort_values(["published", "paper_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
    drop_count = max(1, ceil(len(ordered) * 0.20))
    dropped = ordered.iloc[:drop_count]
    corrupted = ordered.iloc[drop_count:].copy().reset_index(drop=True)
    changed_count = max(1, ceil(len(corrupted) * 0.20))

    def affected(offset: int) -> list[int]:
        return [(offset + index) % len(corrupted) for index in range(changed_count)]

    blank_indices = affected(0)
    noise_indices = affected(changed_count)
    title_indices = affected(changed_count * 2)
    stale_indices = affected(changed_count * 3)
    duplicate_indices = affected(changed_count * 4)

    corrupted.loc[blank_indices, "summary"] = ""
    corrupted.loc[noise_indices, "summary"] = (
        corrupted.loc[noise_indices, "summary"].fillna("").astype(str)
        + " ###@@@ SYNTHETIC_NOISE 000 ???"
    )
    corrupted.loc[title_indices, "title"] = corrupted.loc[title_indices, "title"].astype(str).str.slice(0, 7)
    corrupted.loc[stale_indices, "published"] = "2000-01-01"
    corrupted.loc[stale_indices, "age_days"] = 3650
    corrupted = _rebuild_embedding_text(corrupted)
    duplicated = corrupted.iloc[duplicate_indices].copy()
    corrupted = pd.concat([corrupted, duplicated], ignore_index=True)

    operations = [
        {
            "operation": "drop_latest_records",
            "count": int(len(dropped)),
            "paper_ids": dropped["paper_id"].astype(str).tolist(),
            "description": "Dropped the newest 20% of records.",
        },
        {
            "operation": "blank_summary",
            "count": len(blank_indices),
            "paper_ids": corrupted.iloc[blank_indices]["paper_id"].astype(str).tolist(),
            "description": "Blanked summaries after ingestion.",
        },
        {
            "operation": "inject_noise",
            "count": len(noise_indices),
            "paper_ids": corrupted.iloc[noise_indices]["paper_id"].astype(str).tolist(),
            "description": "Injected synthetic noise tokens into summaries.",
        },
        {
            "operation": "truncate_title",
            "count": len(title_indices),
            "paper_ids": corrupted.iloc[title_indices]["paper_id"].astype(str).tolist(),
            "description": "Truncated titles to fewer than eight characters.",
        },
        {
            "operation": "stale_date",
            "count": len(stale_indices),
            "paper_ids": corrupted.iloc[stale_indices]["paper_id"].astype(str).tolist(),
            "description": "Backdated publication dates beyond the freshness SLA.",
        },
        {
            "operation": "duplicate_rows",
            "count": len(duplicated),
            "paper_ids": duplicated["paper_id"].astype(str).tolist(),
            "description": "Duplicated rows after all other mutations.",
        },
    ]
    write_json(
        output_log_path,
        {
            "input_rows": int(len(df)),
            "output_rows": int(len(corrupted)),
            "operations": operations,
        },
    )
    return corrupted.reset_index(drop=True)
