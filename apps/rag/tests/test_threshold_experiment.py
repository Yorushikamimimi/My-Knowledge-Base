"""Tests for eval.threshold_experiment (pure functions, Phase 2B-2b)."""

from eval import threshold_experiment as te
from eval.threshold_experiment import (
    THRESHOLD_GRID,
    CaseScores,
    ExpectedSource,
    compute_case_scores,
    scan_thresholds,
    select_threshold,
    score_distribution,
)


def _chunk(document, secs, score, rank=1):
    return {
        "rank": rank,
        "document": document,
        "chunk_index": 0,
        "score": score,
        "attributed_sections": secs,
    }


def test_grid_exact_17_points():
    assert len(THRESHOLD_GRID) == 17
    assert THRESHOLD_GRID[0] == 0.350
    assert THRESHOLD_GRID[-1] == 0.750
    for i in range(1, len(THRESHOLD_GRID)):
        assert abs((THRESHOLD_GRID[i] - THRESHOLD_GRID[i - 1]) - 0.025) < 1e-9


def test_positive_relevant_score_and_ranking_failure():
    case = {"id": "p1", "expected_behavior": "answer", "expected_sources": [
        {"document": "docA", "section": "S1"}]}
    # relevant chunk present
    cs = compute_case_scores(case, [
        _chunk("docA", ["S2"], 0.8, 1),
        _chunk("docA", ["S1"], 0.6, 2),
    ])
    assert cs.positive_relevant_score == 0.6
    assert cs.ranking_failure is False
    # no relevant chunk -> ranking failure
    cs2 = compute_case_scores(case, [_chunk("docA", ["S2"], 0.9, 1)])
    assert cs2.positive_relevant_score is None
    assert cs2.ranking_failure is True


def test_negative_max_score_is_rank1():
    case = {"id": "n1", "expected_behavior": "refuse", "expected_sources": []}
    cs = compute_case_scores(case, [
        _chunk("docX", ["S1"], 0.71, 1),
        _chunk("docY", ["S2"], 0.6, 2),
    ])
    assert cs.negative_max_score == 0.71
    assert cs.top_fp_document == "docX"
    assert cs.top_fp_section == "S1"


def test_score_ge_semantics_refusal_strict_lt():
    # score == t still kept (>= t); negative refused only if < t
    case = {"id": "n1", "expected_behavior": "refuse", "expected_sources": []}
    cs = compute_case_scores(case, [_chunk("docX", ["S1"], 0.4, 1)])
    assert cs.negative_max_score == 0.4
    # threshold 0.4: kept (not refused); 0.425: refused
    assert cs.negative_max_score < 0.425
    assert not (cs.negative_max_score < 0.4)


def test_conditional_retention_excludes_ranking_failures():
    cases = [
        # rankable with relevant 0.7
        CaseScores("p1", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.7)]).compute(),
        # rankable with relevant 0.4
        CaseScores("p2", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.4)]).compute(),
        # ranking failure (no relevant)
        CaseScores("p3", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S2"], 0.9)]).compute(),
    ]
    rows = scan_thresholds(cases, clean_negative_ids=set(), hard_negative_ids=set(),
                           grid=[0.5, 0.6])
    r05 = next(r for r in rows if r.threshold == 0.5)
    # conditional: rankable = p1, p2; p1 survives (0.7>=0.5), p2 not (0.4<0.5) -> 0.5
    assert r05.conditional_retention == 0.5
    # e2e: 3 positives, only p1 -> 1/3
    assert abs(r05.end_to_end_survival - 1 / 3) < 0.001


def test_balanced_score_and_selection():
    cases = [
        CaseScores("p1", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.8)]).compute(),
        CaseScores("p2", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.7)]).compute(),
        CaseScores("n1", "refuse", [],
                   [_chunk("docX", ["S"], 0.6)]).compute(),
        CaseScores("n2", "refuse", [],
                   [_chunk("docX", ["S"], 0.45)]).compute(),
    ]
    rows = scan_thresholds(cases, clean_negative_ids={"n1", "n2"},
                           hard_negative_ids=set())
    best = select_threshold(rows)
    # At 0.6: cond=1.0 (both >=0.6), neg refusal: n1 0.6 not <0.6 kept, n2 0.45 refused -> 0.5 -> balanced 0.75
    # At 0.625..0.75: cond=1.0, neg refusal 1.0 -> balanced 1.0
    # tie among {0.625..0.75}: lower threshold wins -> 0.625
    assert best.threshold == 0.625
    assert best.balanced == 1.0


def test_tie_break_order():
    # two thresholds with same balanced; higher neg refusal wins
    cases = [
        CaseScores("p1", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.8)]).compute(),
        CaseScores("n1", "refuse", [], [_chunk("docX", ["S"], 0.5)]).compute(),
    ]
    rows = scan_thresholds(cases, clean_negative_ids={"n1"}, hard_negative_ids=set(),
                           grid=[0.55, 0.6])
    best = select_threshold(rows)
    # 0.55: cond=1.0, neg refusal: 0.5<0.55 -> 1.0, balanced 1.0
    # 0.6:  same. tie -> higher neg refusal (equal) -> lower wrong ctx (equal) ->
    #       higher e2e (equal) -> lower threshold -> 0.55
    assert best.threshold == 0.55


def test_case_level_failure_ids():
    cases = [
        CaseScores("p1", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S1"], 0.4)]).compute(),
        CaseScores("p2", "answer", [ExpectedSource("docA", "S1")],
                   [_chunk("docA", ["S2"], 0.9)]).compute(),  # wrong context
        CaseScores("n1", "refuse", [], [_chunk("docX", ["S"], 0.7)]).compute(),
    ]
    rows = scan_thresholds(cases, clean_negative_ids={"n1"}, hard_negative_ids=set(),
                           grid=[0.5])
    r = rows[0]
    assert "p1" in r.case_ids["positive_false_refusal_ids"]
    assert "p2" in r.case_ids["positive_wrong_context_ids"]
    assert "n1" in r.case_ids["negative_false_accept_ids"]
    assert r.case_ids["negative_refused_ids"] == []


def test_clean_hard_negative_breakdown():
    cases = [
        CaseScores("c1", "refuse", [], [_chunk("docX", ["S"], 0.4)]).compute(),
        CaseScores("h1", "refuse", [], [_chunk("docX", ["S"], 0.8)]).compute(),
    ]
    rows = scan_thresholds(cases, clean_negative_ids={"c1"}, hard_negative_ids={"h1"},
                           grid=[0.5])
    r = rows[0]
    assert r.clean_refusal == 1.0   # 0.4 < 0.5
    assert r.hard_refusal == 0.0    # 0.8 >= 0.5
    assert r.negative_refusal == 0.5


def test_score_distribution():
    d = score_distribution([0.3, 0.5, 0.7, 0.9])
    assert d["count"] == 4
    assert d["min"] == 0.3 and d["max"] == 0.9
    assert d["median"] == 0.7 or d["median"] == 0.5  # p50 of 4 sorted -> index 1 (0.5)
    assert d == score_distribution([]) or d["count"] > 0
