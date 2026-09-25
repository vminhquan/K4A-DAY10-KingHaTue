from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html import unescape
import re
from pathlib import Path
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Map a Crossref response into stable, lineage-friendly records."""
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()

    def text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return normalize_whitespace(unescape(re.sub(r"<[^>]+>", " ", value)))

    def date_value(item: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if not isinstance(value, dict):
                continue
            parts = value.get("date-parts")
            if isinstance(parts, list) and parts and isinstance(parts[0], list):
                numbers = parts[0]
                if numbers and isinstance(numbers[0], int):
                    year = numbers[0]
                    month = numbers[1] if len(numbers) > 1 and isinstance(numbers[1], int) else 1
                    day = numbers[2] if len(numbers) > 2 and isinstance(numbers[2], int) else 1
                    try:
                        return date(year, month, day).isoformat()
                    except ValueError:
                        continue
            timestamp = value.get("date-time")
            if isinstance(timestamp, str) and len(timestamp) >= 10:
                return timestamp[:10]
        return ""

    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = text(str(item.get("DOI", ""))).lower()
        titles = item.get("title")
        title = text(titles[0]) if isinstance(titles, list) and titles else text(item.get("title"))
        if not paper_id or not title or paper_id in seen_ids:
            continue
        seen_ids.add(paper_id)
        authors = []
        for author in item.get("author", []):
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(" ".join(str(author.get(key, "")) for key in ("given", "family")))
            if name:
                authors.append(name)
        categories = [text(value) for value in item.get("subject", []) if text(value)]
        published = date_value(item, "published", "published-online", "published-print", "issued")
        updated = date_value(item, "updated", "created", "deposited") or published
        url = text(item.get("URL")) or f"https://doi.org/{paper_id}"
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=text(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref in live mode, with deterministic snapshot fallback."""
    snapshot_path = settings.paths.raw_api_response
    payload: dict[str, Any] | None = None
    if settings.refresh_source:
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
            "select": "DOI,title,abstract,author,subject,published,issued,created,URL",
        }
        for attempt in range(3):
            try:
                response = requests.get(
                    "https://api.crossref.org/works",
                    params=params,
                    headers={"User-Agent": "day10-data-observability-lab/0.1"},
                    timeout=20,
                )
                if response.status_code in {429, 503}:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                candidate = response.json()
                if isinstance(candidate, dict):
                    payload = candidate
                    write_json(snapshot_path, payload)
                    break
            except (requests.RequestException, ValueError):
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
    if payload is None:
        if not snapshot_path.exists():
            raise RuntimeError("Crossref is unavailable and no local raw snapshot exists.")
        payload = read_json(snapshot_path)
    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("Crossref payload produced no valid records.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the preserved record artifact and validate its minimal contract."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list of records.")
    records = []
    fields = set(PaperRecord.__dataclass_fields__)
    for row in payload:
        if not isinstance(row, dict):
            continue
        values = {name: row.get(name, [] if name in {"authors", "categories"} else "") for name in fields}
        if not isinstance(values["authors"], list) or not isinstance(values["categories"], list):
            raise ValueError(f"{path} contains invalid authors/categories.")
        if not values["paper_id"] or not values["title"]:
            continue
        records.append(PaperRecord(**values))
    if not records:
        raise ValueError(f"{path} contains no valid PaperRecord.")
    return records
