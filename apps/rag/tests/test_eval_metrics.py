"""Tests for eval.metrics (pure functions)."""

from eval.metrics import (
    CaseMetrics,
    ExpectedSource,
    aggregate_metrics,
    build_case_metrics,
)

SRC_D05_TX = ExpectedSource(
    document="Vault/.../Spring ， Spring Boot 八股文.md",
    section="9. @Transactional",
)
SRC_D07_MVCC = ExpectedSource(
    document="Vault/.../MySQL 八股文.md",
    section="3. MVCC",
)


def _chunk(document, secs, score, rank=1):
    return {
        "rank": rank,
        "document": document,
        "chunk_index": 0,
        "score": score,
        "attributed_sections": secs,
    }


def test_section_hit_requires_document_and_section_match():
    cm = CaseMetrics(
        case_id="q-001",
        expected_behavior="answer",
        expected_sources=[SRC_D05_TX],
        raw_top=[
            _chunk("Vault/.../Spring ， Spring Boot 八股文.md", ["3. AOP"], 0.7, 1),
            _chunk("Vault/.../MySQL 八股文.md", ["9. @Transactional"], 0.6, 2),
        ],
        filtered_hits=[],
    ).compute(min_score=0.35)
    # rank1: right doc but wrong section -> not a section hit
    # rank2: wrong doc (but section title matches) -> not a section hit
    assert cm.document_hit_at[1] is True
    assert cm.section_hit_at[1] is False
    assert cm.section_hit_at[3] is False


def test_multi_source_any_semantics():
    # either source counts as a hit (source_match=any)
    cm = CaseMetrics(
        case_id="q-001",
        expected_behavior="answer",
        expected_sources=[SRC_D05_TX, SRC_D07_MVCC],
        raw_top=[
            _chunk("Vault/.../MySQL 八股文.md", ["3. MVCC"], 0.65, 1),
        ],
        filtered_hits=[],
    ).compute(min_score=0.35)
    assert cm.section_hit_at[1] is True
    assert cm.first_relevant_rank == 1


def test_chunk_rank_semantics_no_dedup():
    # same document occupying rank1/rank2 consumes both positions
    doc = "Vault/.../MySQL 八股文.md"
    cm = CaseMetrics(
        case_id="q-001",
        expected_behavior="answer",
        expected_sources=[SRC_D07_MVCC],
        raw_top=[
            _chunk(doc, ["2. 事务"], 0.8, 1),
            _chunk(doc, ["3. MVCC"], 0.7, 2),
            _chunk(doc, ["1. 索引"], 0.6, 3),
        ],
        filtered_hits=[],
    ).compute(min_score=0.35)
    assert cm.document_hit_at[1] is True  # right document already at rank1
    assert cm.section_hit_at[1] is False  # but wrong section
    assert cm.section_hit_at[3] is True  # MVCC at rank2 -> within top3
    assert cm.first_relevant_rank == 2
    assert cm.max_score == 0.8


def test_mrr_first_relevant():
    cm = CaseMetrics(
        case_id="q-001",
        expected_behavior="answer",
        expected_sources=[SRC_D07_MVCC],
        raw_top=[
            _chunk("doc-a", ["x"], 0.9, 1),
            _chunk("doc-b", ["x"], 0.8, 2),
            _chunk("Vault/.../MySQL 八股文.md", ["3. MVCC"], 0.7, 3),
        ],
        filtered_hits=[],
    ).compute(min_score=0.35)
    assert cm.first_relevant_rank == 3
    assert cm.section_hit_at[5] is True


def test_positive_threshold_metrics():
    cases = [
        # relevant survived
        CaseMetrics(
            case_id="p1", expected_behavior="answer", expected_sources=[SRC_D05_TX],
            raw_top=[_chunk(SRC_D05_TX.document, ["9. @Transactional"], 0.6)],
            filtered_hits=[_chunk(SRC_D05_TX.document, ["9. @Transactional"], 0.6)],
        ).compute(min_score=0.35),
        # refused (filtered empty)
        CaseMetrics(
            case_id="p2", expected_behavior="answer", expected_sources=[SRC_D05_TX],
            raw_top=[_chunk("doc", ["9. @Transactional"], 0.2)],
            filtered_hits=[],
        ).compute(min_score=0.35),
        # wrong-context accepted
        CaseMetrics(
            case_id="p3", expected_behavior="answer", expected_sources=[SRC_D05_TX],
            raw_top=[_chunk("doc", ["3. AOP"], 0.6)],
            filtered_hits=[_chunk("doc", ["3. AOP"], 0.6)],
        ).compute(min_score=0.35),
    ]
    agg = aggregate_metrics(cases, min_score=0.35)
    pt = agg["positive_threshold"]
    assert abs(pt["positive_false_refusal_rate"] - 1 / 3) < 0.001
    assert abs(pt["positive_relevant_survival_rate"] - 1 / 3) < 0.001
    assert abs(pt["positive_wrong_context_acceptance_rate"] - 1 / 3) < 0.001


def test_negative_threshold_metrics_with_groups():
    cases = [
        CaseMetrics(
            case_id="q-023", expected_behavior="refuse", expected_sources=[],
            raw_top=[_chunk("doc", ["x"], 0.5)],
            filtered_hits=[_chunk("doc", ["x"], 0.5)],
        ).compute(min_score=0.35),
        CaseMetrics(
            case_id="q-024", expected_behavior="refuse", expected_sources=[],
            raw_top=[_chunk("doc", ["x"], 0.2)],
            filtered_hits=[],
        ).compute(min_score=0.35),
        CaseMetrics(
            case_id="q-027", expected_behavior="refuse", expected_sources=[],
            raw_top=[_chunk("doc", ["x"], 0.4)],
            filtered_hits=[_chunk("doc", ["x"], 0.4)],
        ).compute(min_score=0.35),
    ]
    agg = aggregate_metrics(
        cases, min_score=0.35,
        out_of_corpus_ids={"q-023", "q-024"},
        hard_negative_ids={"q-027"},
    )
    nt = agg["negative_threshold"]
    assert abs(nt["refusal_accuracy"] - 1 / 3) < 0.001
    assert abs(nt["false_acceptance_rate"] - 2 / 3) < 0.001
    assert abs(nt["clean_out_of_corpus_refusal_accuracy"] - 0.5) < 0.001
    assert nt["hard_negative_refusal_accuracy"] == 0.0


def test_negative_diagnostics_captured():
    cm = CaseMetrics(
        case_id="q-023", expected_behavior="refuse", expected_sources=[],
        raw_top=[_chunk("doc-kafka", ["x"], 0.5)],
        filtered_hits=[_chunk("doc-kafka", ["x"], 0.5)],
    ).compute(min_score=0.35)
    assert cm.highest_false_positive_score == 0.5
    assert cm.likely_false_positive_document == "doc-kafka"


def test_build_case_metrics_from_gold_dict():
    case = {
        "id": "q-001",
        "expected_behavior": "answer",
        "expected_sources": [
            {"document": "Vault/.../MySQL 八股文.md", "section": "3. MVCC"}
        ],
    }
    cm = build_case_metrics(
        case,
        raw_top=[_chunk("Vault/.../MySQL 八股文.md", ["3. MVCC"], 0.7)],
        filtered_hits=[_chunk("Vault/.../MySQL 八股文.md", ["3. MVCC"], 0.7)],
        min_score=0.35,
    )
    assert cm.section_hit_at[1] is True
    assert cm.relevant_survived_filter is True
    assert cm.wrong_context_acceptance is False


def test_aggregate_returns_all_sections():
    cases = [
        CaseMetrics(
            case_id="q-001", expected_behavior="answer", expected_sources=[SRC_D05_TX],
            raw_top=[_chunk("doc", ["9. @Transactional"], 0.7)],
            filtered_hits=[_chunk("doc", ["9. @Transactional"], 0.7)],
        ).compute(min_score=0.35)
    ]
    agg = aggregate_metrics(cases, min_score=0.35)
    assert set(agg.keys()) == {"raw_ranking", "positive_threshold", "negative_threshold"}
    assert set(agg["raw_ranking"].keys()) == {
        "document_hit@1", "document_hit@3", "document_hit@5",
        "section_hit@1", "section_hit@3", "section_hit@5", "section_mrr",
    }
