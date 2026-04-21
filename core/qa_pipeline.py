"""
QA Pipeline - runs quality checks on agent output.
Returns a composite score 0-100.
"""

import textstat
from pydantic import BaseModel


class QAResult(BaseModel):
    overall_score: float
    readability_score: float
    word_count: int
    sentence_count: int
    reading_level: str
    issues: list[str] = []


def run_qa(text: str, min_words: int = 50) -> QAResult:
    issues = []
    words = text.split()
    word_count = len(words)

    if word_count < min_words:
        issues.append(f"Too short: {word_count} words (minimum {min_words})")

    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    sentence_count = len(sentences)

    try:
        flesch = textstat.flesch_reading_ease(text)
    except Exception:
        flesch = 50.0

    try:
        grade = textstat.text_standard(text, float_output=False)
    except Exception:
        grade = "Unknown"

    if text.strip().startswith(("I'd be happy to", "Sure,", "Certainly!", "Of course")):
        issues.append("Starts with AI preamble - should be removed")

    if text.count("\n\n\n") > 0:
        issues.append("Contains excessive blank lines")

    readability_component = min(max(flesch, 0), 100) * 0.4
    length_component = min(word_count / max(min_words * 2, 1), 1.0) * 30
    structure_component = min(sentence_count / 5, 1.0) * 20
    issue_penalty = len(issues) * 5
    overall = max(0, min(100, readability_component + length_component + structure_component - issue_penalty))

    return QAResult(
        overall_score=round(overall, 1),
        readability_score=round(flesch, 1),
        word_count=word_count,
        sentence_count=sentence_count,
        reading_level=grade,
        issues=issues,
    )
