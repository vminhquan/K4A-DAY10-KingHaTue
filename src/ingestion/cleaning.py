from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Create a deterministic, retrieval-ready dataframe from raw records."""
    if not records:
        raise ValueError("Cannot clean an empty record collection.")
    timestamp = pd.Timestamp(run_date)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")

    rows = []
    for record in records:
        paper_id = normalize_whitespace(record.paper_id).lower()
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        authors = [normalize_whitespace(str(value)) for value in record.authors]
        authors = [value for value in authors if value]
        categories = [normalize_whitespace(str(value)) for value in record.categories]
        categories = [value for value in categories if value]
        published = pd.to_datetime(record.published, errors="coerce", utc=True)
        updated = pd.to_datetime(record.updated, errors="coerce", utc=True)
        if not paper_id or not title or not summary or pd.isna(published):
            continue
        authors_joined = compact_join(authors) or "Unknown authors"
        categories_joined = compact_join(categories) or "Uncategorized"
        published_iso = published.date().isoformat()
        updated_iso = updated.date().isoformat() if not pd.isna(updated) else published_iso
        age_days = max(0, int((timestamp.normalize() - published.normalize()).days))
        text_for_embedding = "\n".join(
            [
                f"Title: {title}",
                f"Authors: {authors_joined}",
                f"Published: {published_iso}",
                f"Categories: {categories_joined}",
                f"Summary: {summary}",
            ]
        )
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": normalize_whitespace(record.primary_category)
                or categories[0]
                if categories
                else "Uncategorized",
                "published": published_iso,
                "updated": updated_iso,
                "age_days": age_days,
                "summary_chars": len(summary),
                "text_for_embedding": text_for_embedding,
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "comment": normalize_whitespace(record.comment),
            }
        )
    columns = [
        "paper_id", "title", "summary", "authors_joined", "categories_joined",
        "primary_category", "published", "updated", "age_days", "summary_chars",
        "text_for_embedding", "abs_url", "pdf_url", "comment",
    ]
    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        raise ValueError("Cleaning removed every record; inspect raw schema.")
    # DOI is the stable primary key. Sorting before dedupe makes output reproducible.
    df = df.sort_values(["paper_id", "published"], kind="stable").drop_duplicates(
        subset=["paper_id"], keep="first"
    )
    return df.sort_values(["published", "paper_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
