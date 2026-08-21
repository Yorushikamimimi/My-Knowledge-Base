"""Metric computations for the retrieval-only benchmark.

Ranking metrics operate on raw retrieval results (before min_score filtering),
with rank unit = retrieved chunk rank (no document de-duplication/re-ranking).
Threshold metrics operate on filtered hits only.

Gold semantics (frozen Gold V1):
- source_match = "any": a case is relevant if ANY expected source matches.
- A section-level match requires: document match AND the chunk's attributed
  sections contain the exact expected section title.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExpectedSource:
    document: str
    section: str


def _document_matches(chunk_document: str, sources: list[ExpectedSource]) -> bool:
    return any(s.document == chunk_document for s in sources)


def _section_matches(
    chunk_document: str, attributed_sections: list[str], sources: list[ExpectedSource]
) -> bool:
    return any(
        s.document == chunk_document and s.section in attributed_sections
        for s in sources
    )


@dataclass
class CaseMetrics:
    """Per-case retrieval metrics (computed against raw top-K)."""

    case_id: str
    expected_behavior: str
    expected_sources: list[ExpectedSource] = field(default_factory=list)
    raw_top: list[dict] = field(default_factory=list)  # [{document, chunk_index, score, attributed_sections}]
    filtered_hits: list[dict] = field(default_factory=list)

    # computed
    first_relevant_rank: int | None = None
    document_hit_at: dict[int, bool] = field(default_factory=lambda: {1: False, 3: False, 5: False})
    section_hit_at: dict[int, bool] = field(default_factory=lambda: {1: False, 3: False, 5: False})
    refused: bool = False
    relevant_survived_filter: bool = False
    wrong_context_acceptance: bool = False
    max_score: float | None = None
    highest_false_positive_score: float | None = None
    likely_false_positive_document: str | None = None
    likely_false_positive_section: str | None = None

    def compute(self, min_score: float) -> "CaseMetrics":
        sources = self.expected_scores_as_sources()
        # --- raw ranking (cumulative Hit@K: relevant within top-K) ---
        first_relevant = None
        doc_hit_so_far = False
        sec_hit_so_far = False
        for rank, chunk in enumerate(self.raw_top, start=1):
            doc = chunk.get("document", "")
            secs = chunk.get("attributed_sections", [])
            doc_hit_so_far = doc_hit_so_far or _document_matches(doc, sources)
            sec_hit_so_far = sec_hit_so_far or _section_matches(doc, secs, sources)
            if rank in self.document_hit_at:
                self.document_hit_at[rank] = doc_hit_so_far
            if rank in self.section_hit_at:
                self.section_hit_at[rank] = sec_hit_so_far
            # first relevant by section (any semantics)
            if first_relevant is None and _section_matches(doc, secs, sources):
                first_relevant = rank
        # propagate hits to larger K when fewer than 5 chunks were retrieved
        for k in sorted(self.document_hit_at):
            if k > len(self.raw_top):
                self.document_hit_at[k] = doc_hit_so_far
                self.section_hit_at[k] = sec_hit_so_far
        self.first_relevant_rank = first_relevant

        scores = [c.get("score", 0.0) for c in self.raw_top]
        self.max_score = max(scores) if scores else None

        # --- threshold behavior ---
        self.refused = len(self.filtered_hits) == 0

        relevant_in_filtered = any(
            _section_matches(h.get("document", ""), h.get("attributed_sections", []), sources)
            for h in self.filtered_hits
        )
        if self.expected_behavior == "answer":
            self.relevant_survived_filter = relevant_in_filtered
            self.wrong_context_acceptance = (
                len(self.filtered_hits) > 0 and not relevant_in_filtered
            )

        # --- negative diagnostics ---
        if self.expected_behavior == "refuse" and self.filtered_hits:
            worst = max(self.filtered_hits, key=lambda h: h.get("score", 0.0))
            self.highest_false_positive_score = worst.get("score")
            self.likely_false_positive_document = worst.get("document")
            self.likely_false_positive_section = (
                worst.get("attributed_sections", [None])[0] if worst.get("attributed_sections") else None
            )
        return self

    def expected_scores_as_sources(self) -> list[ExpectedSource]:
        return self.expected_sources


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def aggregate_metrics(
    cases: list[CaseMetrics],
    min_score: float,
    *,
    out_of_corpus_ids: set[str] | None = None,
    hard_negative_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Aggregate per-case metrics into the benchmark report schema.

    `cases` must already be computed (CaseMetrics.compute called).
    """
    positives = [c for c in cases if c.expected_behavior == "answer"]
    negatives = [c for c in cases if c.expected_behavior == "refuse"]

    # --- positive raw ranking ---
    def mean_hit(attr: str, k: int) -> float:
        vals = [getattr(c, attr)[k] for c in positives]
        return _rate(sum(1 for v in vals if v), len(positives))

    mrrs: list[float] = []
    for c in positives:
        if c.first_relevant_rank is not None:
            mrrs.append(1.0 / c.first_relevant_rank)
    section_mrr = round(sum(mrrs) / len(positives), 4) if positives else 0.0

    raw = {
        "document_hit@1": mean_hit("document_hit_at", 1),
        "document_hit@3": mean_hit("document_hit_at", 3),
        "document_hit@5": mean_hit("document_hit_at", 5),
        "section_hit@1": mean_hit("section_hit_at", 1),
        "section_hit@3": mean_hit("section_hit_at", 3),
        "section_hit@5": mean_hit("section_hit_at", 5),
        "section_mrr": section_mrr,
    }

    # --- positive threshold ---
    pos_refused = sum(1 for c in positives if c.refused)
    pos_relevant_survived = sum(1 for c in positives if c.relevant_survived_filter)
    pos_wrong_context = sum(1 for c in positives if c.wrong_context_acceptance)
    pos_threshold = {
        "positive_false_refusal_rate": _rate(pos_refused, len(positives)),
        "positive_relevant_survival_rate": _rate(pos_relevant_survived, len(positives)),
        "positive_wrong_context_acceptance_rate": _rate(pos_wrong_context, len(positives)),
    }

    # --- negative threshold ---
    neg_refused = sum(1 for c in negatives if c.refused)
    neg_accepted = sum(1 for c in negatives if not c.refused)
    neg_threshold = {
        "refusal_accuracy": _rate(neg_refused, len(negatives)),
        "false_acceptance_rate": _rate(neg_accepted, len(negatives)),
    }

    # clean vs hard negative subgroups
    out_of_corpus_ids = out_of_corpus_ids or set()
    hard_negative_ids = hard_negative_ids or set()
    clean_neg = [c for c in negatives if c.case_id in out_of_corpus_ids]
    hard_neg = [c for c in negatives if c.case_id in hard_negative_ids]
    neg_threshold["clean_out_of_corpus_refusal_accuracy"] = _rate(
        sum(1 for c in clean_neg if c.refused), len(clean_neg)
    )
    neg_threshold["hard_negative_refusal_accuracy"] = _rate(
        sum(1 for c in hard_neg if c.refused), len(hard_neg)
    )

    return {
        "raw_ranking": raw,
        "positive_threshold": pos_threshold,
        "negative_threshold": neg_threshold,
    }


def build_case_metrics(
    case: dict,
    raw_top: list[dict],
    filtered_hits: list[dict],
    min_score: float,
) -> CaseMetrics:
    """Build + compute per-case metrics from a gold case dict and retrieval results."""
    sources = [
        ExpectedSource(document=s["document"], section=s["section"])
        for s in case.get("expected_sources", [])
    ]
    metrics = CaseMetrics(
        case_id=case["id"],
        expected_behavior=case["expected_behavior"],
        expected_sources=sources,
        raw_top=raw_top,
        filtered_hits=filtered_hits,
    )
    return metrics.compute(min_score)
