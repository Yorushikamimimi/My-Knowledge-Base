"""Threshold experiment support (Phase 2B-2b).

Pure functions for offline threshold scanning on a fixed raw retrieval
snapshot. The retrieval (embedding + pgvector raw top5) runs exactly once;
the 17-grid threshold scan re-filters that same raw data offline.

Frozen experiment design: docs/phase2/threshold-experiment-design-v1.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from eval.metrics import ExpectedSource

# Frozen grid: 0.35 -> 0.75 step 0.025 (17 points). Do not add DEV-specific values.
THRESHOLD_GRID = [
    0.350, 0.375, 0.400, 0.425, 0.450, 0.475, 0.500, 0.525,
    0.550, 0.575, 0.600, 0.625, 0.650, 0.675, 0.700, 0.725, 0.750,
]


@dataclass
class CaseScores:
    """Per-case threshold-relevant scores computed once from raw top5."""

    case_id: str
    expected_behavior: str
    expected_sources: list[ExpectedSource]
    raw_top: list[dict]  # [{rank, document, chunk_index, score, attributed_sections}]

    # positive
    positive_relevant_score: float | None = None
    ranking_failure: bool = False
    # negative
    negative_max_score: float | None = None
    top_fp_document: str | None = None
    top_fp_section: str | None = None

    def compute(self) -> "CaseScores":
        if self.expected_behavior == "answer":
            rel_scores = [
                c.get("score", 0.0)
                for c in self.raw_top
                if self._is_relevant(c)
            ]
            if rel_scores:
                self.positive_relevant_score = max(rel_scores)
            else:
                self.positive_relevant_score = None
                self.ranking_failure = True
        else:  # refuse
            if self.raw_top:
                top = self.raw_top[0]
                self.negative_max_score = top.get("score")
                self.top_fp_document = top.get("document")
                secs = top.get("attributed_sections") or []
                self.top_fp_section = secs[0] if secs else None
        return self

    def _is_relevant(self, chunk: dict) -> bool:
        return any(
            s.document == chunk.get("document")
            and s.section in (chunk.get("attributed_sections") or [])
            for s in self.expected_sources
        )

    def relevant_survives(self, threshold: float) -> bool:
        return (
            self.expected_behavior == "answer"
            and self.positive_relevant_score is not None
            and self.positive_relevant_score >= threshold
        )


def compute_case_scores(case: dict, raw_top: list[dict]) -> CaseScores:
    sources = [
        ExpectedSource(document=s["document"], section=s["section"])
        for s in case.get("expected_sources", [])
    ]
    return CaseScores(
        case_id=case["id"],
        expected_behavior=case["expected_behavior"],
        expected_sources=sources,
        raw_top=raw_top,
    ).compute()


def _rate(n: int, d: int) -> float:
    return round(n / d, 4) if d else 0.0


@dataclass
class ThresholdRow:
    threshold: float
    end_to_end_survival: float
    conditional_retention: float
    false_refusal: float
    wrong_context: float
    negative_refusal: float
    clean_refusal: float
    hard_refusal: float
    balanced: float
    case_ids: dict = field(default_factory=dict)


def scan_thresholds(
    cases: list[CaseScores],
    *,
    clean_negative_ids: set[str],
    hard_negative_ids: set[str],
    grid: list[float] | None = None,
) -> list[ThresholdRow]:
    """Offline threshold scan over a frozen grid. Returns one row per threshold."""
    grid = grid or THRESHOLD_GRID
    positives = [c for c in cases if c.expected_behavior == "answer"]
    negatives = [c for c in cases if c.expected_behavior == "refuse"]
    rankable = [c for c in positives if not c.ranking_failure]
    n_pos, n_rank, n_neg = len(positives), len(rankable), len(negatives)

    rows: list[ThresholdRow] = []
    for t in grid:
        # positive
        e2e = sum(1 for c in positives if c.relevant_survives(t))
        cond = sum(1 for c in rankable if c.relevant_survives(t))
        false_refusal_ids = [
            c.case_id for c in positives
            if not c.relevant_survives(t) and c.positive_relevant_score is not None
        ]
        # wrong-context: filtered_hits != [] but no relevant among hits
        wrong_ids = []
        for c in positives:
            kept = [ch for ch in c.raw_top if ch.get("score", 0.0) >= t]
            if kept and not c.relevant_survives(t):
                wrong_ids.append(c.case_id)
        # negative: refused iff negative_max_score < t (strict)
        neg_refused_ids = [
            c.case_id for c in negatives
            if c.negative_max_score is None or c.negative_max_score < t
        ]
        clean_refused = sum(
            1 for c in negatives
            if c.case_id in clean_negative_ids and c.case_id in neg_refused_ids
        )
        hard_refused = sum(
            1 for c in negatives
            if c.case_id in hard_negative_ids and c.case_id in neg_refused_ids
        )
        n_clean = sum(1 for c in negatives if c.case_id in clean_negative_ids)
        n_hard = sum(1 for c in negatives if c.case_id in hard_negative_ids)

        neg_refusal = _rate(len(neg_refused_ids), n_neg)
        balanced = round((_rate(cond, n_rank) + neg_refusal) / 2, 4)

        rows.append(
            ThresholdRow(
                threshold=t,
                end_to_end_survival=_rate(e2e, n_pos),
                conditional_retention=_rate(cond, n_rank),
                false_refusal=_rate(len(false_refusal_ids), n_pos),
                wrong_context=_rate(len(wrong_ids), n_pos),
                negative_refusal=neg_refusal,
                clean_refusal=_rate(clean_refused, n_clean),
                hard_refusal=_rate(hard_refused, n_hard),
                balanced=balanced,
                case_ids={
                    "positive_false_refusal_ids": false_refusal_ids,
                    "positive_relevant_dropped_ids": [
                        c.case_id for c in positives if not c.relevant_survives(t)
                    ],
                    "positive_wrong_context_ids": wrong_ids,
                    "negative_refused_ids": neg_refused_ids,
                    "negative_false_accept_ids": [
                        c.case_id for c in negatives if c.case_id not in neg_refused_ids
                    ],
                },
            )
        )
    return rows


def select_threshold(rows: list[ThresholdRow]) -> ThresholdRow:
    """Pre-registered selection: highest Balanced Score; tie-break order frozen."""
    best = rows[0]
    for r in rows[1:]:
        if r.balanced > best.balanced:
            best = r
            continue
        if r.balanced < best.balanced:
            continue
        # tie: 1. higher negative refusal, 2. lower wrong-context,
        #      3. higher e2e survival, 4. lower threshold
        if r.negative_refusal > best.negative_refusal:
            best = r
        elif r.negative_refusal < best.negative_refusal:
            continue
        elif r.wrong_context < best.wrong_context:
            best = r
        elif r.wrong_context > best.wrong_context:
            continue
        elif r.end_to_end_survival > best.end_to_end_survival:
            best = r
        elif r.end_to_end_survival < best.end_to_end_survival:
            continue
        elif r.threshold < best.threshold:
            best = r
    return best


def score_distribution(values: list[float]) -> dict:
    if not values:
        return {"count": 0}
    s = sorted(values)
    n = len(s)
    def pct(p: float) -> float:
        idx = min(n - 1, int(p * (n - 1)))
        return round(s[idx], 4)
    return {
        "count": n,
        "min": round(s[0], 4),
        "p25": pct(0.25),
        "median": pct(0.5),
        "p75": pct(0.75),
        "max": round(s[-1], 4),
    }
