from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


QUESTION_TYPES = ("summary", "authors", "date", "categories")

def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build ten deterministic questions across the four required categories."""
    required = {"paper_id", "title", "summary", "authors_joined", "published", "categories_joined"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Clean dataframe is missing columns: {sorted(missing)}")
    if len(df) < 10:
        raise ValueError("At least ten clean documents are required for the benchmark set.")

    # The clean dataframe is sorted deterministically; spacing samples distributes
    # questions across the corpus without requiring random state.
    positions = [round(index * (len(df) - 1) / 9) for index in range(10)]
    questions: list[dict[str, Any]] = []
    for number, position in enumerate(positions, 1):
        row = df.iloc[position]
        question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
        title = str(row["title"])
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            truth = first_sentence(str(row["summary"]))
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            truth = str(row["authors_joined"])
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            truth = str(row["published"])
        else:
            question = f"What categories does the paper '{title}' belong to?"
            truth = str(row["categories_joined"])
        questions.append(
            {
                "id": f"eval_{number:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": truth,
                "ground_truth_doc_ids": [str(row["paper_id"])],
            }
        )
    write_json(output_path, questions)
    return questions
