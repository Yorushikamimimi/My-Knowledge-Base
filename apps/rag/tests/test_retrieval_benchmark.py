"""Safety tests for the retrieval benchmark runner (no generation, no Langfuse)."""

import inspect
import subprocess
import sys
from pathlib import Path

import pytest

from eval import retrieval_benchmark as rb

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_benchmark_module_has_no_generate_call_path():
    """Structural guarantee: the benchmark module never calls provider.generate.

    Uses AST to inspect actual call sites — docstring text is ignored.
    """
    import ast

    tree = ast.parse(inspect.getsource(rb))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                calls.append(func.attr)
            elif isinstance(func, ast.Name):
                calls.append(func.id)
    assert "generate" not in calls
    assert "query" not in calls  # RagService.query / service.query never used
    assert "ingest" in calls  # production ingestion path is used


def test_privacy_gate_rejects_langfuse_enabled(monkeypatch, capsys):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "true")
    rc = rb.main(["--vault-root", "/nonexistent"])
    assert rc == 2
    out = capsys.readouterr().err
    assert "LANGFUSE_TRACING_ENABLED must be false" in out


def test_no_hardcoded_vault_abs_path():
    src = inspect.getsource(rb)
    # no absolute user paths in code (docstring usage example uses placeholder)
    assert "Users/yang" not in src
    assert "Vaults/main-vault" not in src
    # paths are injected at runtime via --vault-root / env
    assert "--vault-root" in src


def test_runner_never_truncates_embedding_input():
    """Truncation capability must be fully removed — runner is always
    production-faithful; no CLI/debug flag can enable truncation."""
    src = inspect.getsource(rb)
    assert "--non-production-debug-truncate" not in src
    assert "--embed-max-chars" not in src
    assert "truncate" not in src.lower()
    assert "embed_max_chars" not in src
    assert "baseline_compatible" not in src
    # fixed contract markers remain, but only as fixed truth
    assert "production_faithful" in src
    assert "embedding_truncation" in src


def test_ingest_document_passes_full_chunk_to_provider(monkeypatch):
    """ingest_document must call RagService.ingest (production full-chunk path)
    unconditionally — no truncation branch exists."""
    src = inspect.getsource(rb.ingest_document)
    assert "service.ingest" in src
    # no slicing of the embed input anywhere in the function
    assert "[:embed" not in src and "[:2000" not in src
    # production path reads the full file
    try:
        rb.ingest_document(
            type("S", (), {"settings": None})(),
            "kb",
            {"path": "Vault/not/used.md"},
            Path("/nonexistent"),
        )
        assert False, "expected FileNotFoundError from production read path"
    except FileNotFoundError:
        pass  # production-faithful path reads the full file (no truncation)


def test_ingestion_failure_is_surfaced_not_hidden(monkeypatch):
    """A failing document must be recorded as INGESTION_FAILED, never masked."""
    import eval.retrieval_benchmark as rb_mod

    src = inspect.getsource(rb_mod.main)
    assert "INGESTION_FAILED" in src
    assert "status" in src


def test_gold_default_is_v11():
    """Official experiments must default to Gold V1.1 (custom --gold still works)."""
    src = inspect.getsource(rb)
    assert 'gold-v1.1.json' in src
    assert '--gold' in src  # custom gold file support retained


def test_runtime_output_ignored_by_git():
    """Result outputs under .runtime/eval must never enter the repo."""
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".runtime/eval/" in gitignore


def test_eval_kb_id_deterministic():
    a = rb.eval_kb_id()
    b = rb.eval_kb_id()
    assert a == b
    assert len(a) == 36


def test_document_id_deterministic_and_stable():
    a = rb.document_id_for("v1", "Vault/x.md")
    b = rb.document_id_for("v1", "Vault/x.md")
    assert a == b
    c = rb.document_id_for("v1", "Vault/y.md")
    assert a != c
    d = rb.document_id_for("v2", "Vault/x.md")
    assert a != d


def test_git_commit_returns_short_hash():
    commit = rb.git_commit()
    assert commit != "unknown"
    assert len(commit) == 7 or len(commit) == 40


def test_corpus_json_is_machine_readable():
    corpus = rb.load_corpus(REPO_ROOT / "docs" / "phase2" / "corpus-v1.json")
    assert len(corpus) == 12
    ids = [d["id"] for d in corpus]
    assert ids == [f"D{i:02d}" for i in range(1, 13)]
    for d in corpus:
        assert d["path"].startswith("Vault/")


def test_gold_json_loads_30():
    # both V1 and V1.1 keep 30 cases / 22 positive / 8 negative
    for name in ("gold-v1.json", "gold-v1.1.json"):
        gold = rb.load_gold(REPO_ROOT / "docs" / "phase2" / name)
        assert len(gold) == 30, name
        assert sum(1 for q in gold if q["category"] == "positive") == 22, name
        assert sum(1 for q in gold if q["category"] == "negative") == 8, name


def test_gold_v11_q001_has_three_sources():
    gold = rb.load_gold(REPO_ROOT / "docs" / "phase2" / "gold-v1.1.json")
    q001 = next(q for q in gold if q["id"] == "q-001")
    assert len(q001["expected_sources"]) == 3
    sections = [s["section"] for s in q001["expected_sources"]]
    assert "9. @Transactional" in sections
    assert "3. AOP" in sections
    assert "5. 声明式事务 @Transactional" in sections
    assert q001["source_match"] == "any"


def test_gold_split_completeness_and_disjoint():
    """DEV ∪ TEST = 30, DEV ∩ TEST = ∅, ratio 15/5 and 7/3."""
    split = rb.load_split(REPO_ROOT / "docs" / "phase2" / "gold-split-v1.1.json")
    gold = rb.load_gold(REPO_ROOT / "docs" / "phase2" / "gold-v1.1.json")
    all_ids = {q["id"] for q in gold}
    dev, test = split["dev"], split["test"]
    assert len(dev) == 20
    assert len(test) == 10
    assert dev & test == set()
    assert dev | test == all_ids
    # ratio: DEV 15 pos/5 neg, TEST 7 pos/3 neg
    by_cat = {"dev_pos": 0, "dev_neg": 0, "test_pos": 0, "test_neg": 0}
    for q in gold:
        if q["id"] in dev:
            by_cat["dev_pos" if q["category"] == "positive" else "dev_neg"] += 1
        if q["id"] in test:
            by_cat["test_pos" if q["category"] == "positive" else "test_neg"] += 1
    assert by_cat == {"dev_pos": 15, "dev_neg": 5, "test_pos": 7, "test_neg": 3}


def test_split_filter():
    gold = rb.load_gold(REPO_ROOT / "docs" / "phase2" / "gold-v1.1.json")
    split = rb.load_split(REPO_ROOT / "docs" / "phase2" / "gold-split-v1.1.json")
    dev = rb.filter_gold_by_split(gold, "dev", split)
    test = rb.filter_gold_by_split(gold, "test", split)
    allg = rb.filter_gold_by_split(gold, "all", split)
    assert len(dev) == 20 and len(test) == 10 and len(allg) == 30
    assert {q["id"] for q in dev} == split["dev"]
    assert {q["id"] for q in test} == split["test"]
    # TEST positive covers all 6 clusters + 1 non-cluster backend basic
    test_pos = [q for q in test if q["category"] == "positive"]
    clusters = {q.get("cluster") or "none" for q in test_pos}
    assert {"A", "B", "C", "D", "E", "F", "none"} <= clusters
    # q-023 Kafka is in DEV (known regression, not a fresh TEST signal)
    assert "q-023" in split["dev"]
    # TEST negative = 1 clean + 2 hard
    test_neg = [q for q in test if q["category"] == "negative"]
    clean = sum(1 for q in test_neg if "out-of-corpus" in q.get("notes", ""))
    hard = sum(1 for q in test_neg if "hard negative" in q.get("notes", ""))
    assert clean == 1 and hard == 2


def test_chunk_override_does_not_modify_production_defaults():
    from app.config import get_settings

    before = get_settings()
    # run main? no — assert the override mechanism is a model_copy on a local copy
    src = inspect.getsource(rb.main)
    assert "--chunk-size" in src and "--chunk-overlap" in src
    assert "model_copy" in src  # benchmark-only copy, production defaults untouched
    after = get_settings()
    assert before.chunk_size == after.chunk_size == 450
    assert before.chunk_overlap == after.chunk_overlap == 80


def test_config_aware_kb_and_document_ids():
    """Different chunk configs must use different KB/doc UUIDs."""
    kb_450 = rb.eval_kb_id(450, 80)
    kb_300 = rb.eval_kb_id(300, 50)
    assert kb_450 != kb_300
    assert rb.eval_kb_id(450, 80) == kb_450  # deterministic
    doc_450 = rb.document_id_for("v1", "Vault/x.md", 450, 80)
    doc_300 = rb.document_id_for("v1", "Vault/x.md", 300, 50)
    assert doc_450 != doc_300
    assert rb.document_id_for("v1", "Vault/x.md", 450, 80) == doc_450


def test_test_split_requires_allow_test_flag(monkeypatch, capsys):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")
    rc = rb.main(["--vault-root", "/nonexistent", "--run-split", "test"])
    assert rc == 2
    out = capsys.readouterr().err
    assert "--allow-test" in out


def test_gold_record_normalizes_document_to_basename():
    """DB stores only basename in document_name; gold documents must be
    normalized to basename so document/section matching works end-to-end."""
    from eval.metrics import build_case_metrics

    q = {
        "id": "q-001",
        "expected_behavior": "answer",
        "expected_sources": [
            {
                "document": "Vault/Personal_Archive/10-Knowledge/backend/八股/Spring ， Spring Boot 八股文.md",
                "section": "9. @Transactional",
            }
        ],
    }
    # simulate runner normalization: full path -> basename + document_path
    q_record = dict(q)
    q_record["expected_sources"] = [
        {
            "document": Path(s["document"]).name,
            "document_path": s["document"],
            "section": s["section"],
        }
        for s in q["expected_sources"]
    ]
    cm = build_case_metrics(
        q_record,
        raw_top=[
            {
                "rank": 1,
                "document": "Spring ， Spring Boot 八股文.md",
                "chunk_index": 0,
                "score": 0.64,
                "attributed_sections": ["9. @Transactional"],
            }
        ],
        filtered_hits=[
            {
                "rank": 1,
                "document": "Spring ， Spring Boot 八股文.md",
                "chunk_index": 0,
                "score": 0.64,
                "attributed_sections": ["9. @Transactional"],
            }
        ],
        min_score=0.35,
    )
    assert cm.section_hit_at[1] is True
    assert cm.first_relevant_rank == 1
    assert cm.relevant_survived_filter is True
