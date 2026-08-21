"""Retrieval-only benchmark runner (Baseline V1 measurement).

Pipeline (no generation, no Langfuse):

    Question
      -> provider.embed()
      -> repository.search()          (raw TopK)
      -> section attribution          (chunk -> sections, computed offline)
      -> min_score filter             (filtered hits)
      -> metrics                      (raw ranking + threshold)

Corpus ingestion reuses the production path (RagService.ingest) so parse /
chunk / embed / replace_document_chunks behave identically to production.

Privacy: never calls provider.generate(); never initializes Langfuse. Real
question/context stays on local machine. LANGFUSE_TRACING_ENABLED must be
false (asserted at startup).

Usage (from apps/rag):
    LANGFUSE_TRACING_ENABLED=false \
    .venv/bin/python -m eval.retrieval_benchmark \
        --vault-root /path/to/obsidian/vault \
        --gold ../docs/phase2/gold-v1.1.json \
        --corpus ../docs/phase2/corpus-v1.json \
        --out .runtime/eval/retrieval-baseline-v1.json

    (use `python -m` — never the broken .venv/bin/uvicorn shebang)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path

# Allow running as `python -m eval.retrieval_benchmark` from apps/rag
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings, get_settings  # noqa: E402
from app.providers import create_provider  # noqa: E402
from app.repository import RagRepository  # noqa: E402
from app.schemas import IngestRequest  # noqa: E402
from app.service import RagService  # noqa: E402

from eval import section_attribution as attr  # noqa: E402
from eval.metrics import build_case_metrics, aggregate_metrics  # noqa: E402

# ---------------------------------------------------------------------------
# Deterministic IDs (corpus_version + relative_path -> stable UUID v5)
# ---------------------------------------------------------------------------

EVAL_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
EVAL_KB_NAME = "mykb-eval-corpus-v1"


def eval_kb_id(chunk_size: int | None = None, chunk_overlap: int | None = None) -> str:
    """Deterministic eval KB id. Config-aware when chunk params are given so
    different chunk strategies never read each other's chunks."""
    if chunk_size is None or chunk_overlap is None:
        return str(uuid.uuid5(EVAL_NAMESPACE, EVAL_KB_NAME))
    return str(
        uuid.uuid5(
            EVAL_NAMESPACE,
            f"{EVAL_KB_NAME}-chunk-{chunk_size}-{chunk_overlap}",
        )
    )


def document_id_for(
    corpus_version: str,
    relative_path: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> str:
    if chunk_size is None or chunk_overlap is None:
        return str(uuid.uuid5(EVAL_NAMESPACE, f"{corpus_version}:{relative_path}"))
    return str(
        uuid.uuid5(
            EVAL_NAMESPACE,
            f"{corpus_version}:{chunk_size}:{chunk_overlap}:{relative_path}",
        )
    )


# ---------------------------------------------------------------------------
# Corpus definition
# ---------------------------------------------------------------------------


def load_corpus(corpus_file: Path) -> list[dict]:
    data = json.loads(corpus_file.read_text(encoding="utf-8"))
    return data["documents"]


def load_gold(gold_file: Path) -> list[dict]:
    data = json.loads(gold_file.read_text(encoding="utf-8"))
    return data["questions"]


def _gold_version_from(gold_file: Path) -> str:
    """Read gold version from file meta if present, else fall back to filename."""
    try:
        data = json.loads(gold_file.read_text(encoding="utf-8"))
        meta = data.get("meta") or {}
        if meta.get("version"):
            return str(meta["version"])
    except Exception:  # pragma: no cover
        pass
    return gold_file.stem.replace("gold-", "")


def load_split(split_file: Path) -> dict:
    """Load the DEV/TEST split (see docs/phase2/gold-split-v1.1.json)."""
    data = json.loads(split_file.read_text(encoding="utf-8"))
    return {
        "dev": set(data["dev"]["question_ids"]),
        "test": set(data["test"]["question_ids"]),
    }


def filter_gold_by_split(gold: list[dict], split: str, split_map: dict) -> list[dict]:
    """Filter gold questions to a split. 'all' returns everything."""
    if split == "all":
        return list(gold)
    allowed = split_map[split]
    return [q for q in gold if q["id"] in allowed]


# ---------------------------------------------------------------------------
# Ingestion (reuses production logic)
# ---------------------------------------------------------------------------


def ingest_document(
    service: RagService,
    kb_id: str,
    doc: dict,
    vault_root: Path,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """Ingest one corpus document through RagService.ingest (production path).

    Production-faithful by contract: the FULL production chunk text is embedded
    exactly as the running service would. The runner never modifies the
    embedding input. If the embedding provider rejects the input (context
    overflow), the failure propagates to the caller and is recorded as
    INGESTION_FAILED — the benchmark never fakes success.
    """
    abs_path = vault_root / doc["path"]
    raw = abs_path.read_bytes()

    request = IngestRequest(
        knowledgeBaseId=kb_id,
        documentId=document_id_for("v1", doc["path"], chunk_size, chunk_overlap),
        documentName=Path(doc["path"]).name,
        contentType="text/markdown",
        contentBase64=base64.b64encode(raw).decode("ascii"),
    )
    response = service.ingest(request)
    return response.chunkCount


# ---------------------------------------------------------------------------
# Section attribution for all corpus documents (computed once per run)
# ---------------------------------------------------------------------------


def build_attribution_map(
    vault_root: Path, docs: list[dict], chunk_size: int, overlap: int
) -> dict[str, dict]:
    """document relative path -> {chunk_index: [section_titles...]} plus diagnostics."""
    result: dict[str, dict] = {}
    for doc in docs:
        text = (vault_root / doc["path"]).read_text(encoding="utf-8")
        sections, ranges, overlaps = attr.attribute_sections(
            text, chunk_size, overlap, target_levels={2}
        )
        by_chunk: dict[int, list[str]] = {}
        for o in overlaps:
            if o.attributed:
                by_chunk.setdefault(o.chunk_index, []).append(o.section_title)
        result[doc["path"]] = {
            "sections": [
                {
                    "title": s.title,
                    "heading_level": s.heading_level,
                    "heading_path": list(s.heading_path),
                }
                for s in sections
            ],
            "chunk_sections": {str(k): v for k, v in sorted(by_chunk.items())},
            "diagnostics": attr.attribution_diagnostics(sections, ranges, overlaps),
        }
    return result


# ---------------------------------------------------------------------------
# Per-case retrieval
# ---------------------------------------------------------------------------


def retrieve_case(
    service: RagService,
    kb_id: str,
    question: str,
    top_k: int,
    min_score: float,
    attribution: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    """Embed question, search raw TopK, attribute sections, filter by min_score."""
    query_embedding = service.provider.embed(question)
    retrieved = service.repository.search(kb_id, query_embedding, top_k)

    raw_top: list[dict] = []
    for rank, chunk in enumerate(retrieved, start=1):
        doc_path = _doc_path_for_name(chunk.document_name)
        secs = _attributed_sections_for(attribution, doc_path, chunk.chunk_index)
        raw_top.append(
            {
                "rank": rank,
                "document": chunk.document_name,
                "chunk_index": chunk.chunk_index,
                "score": round(chunk.score, 4),
                "attributed_sections": secs,
            }
        )

    filtered = [r for r in raw_top if r["score"] >= min_score]
    return raw_top, filtered


def _doc_path_for_name(document_name: str) -> str | None:
    """Best-effort reverse lookup: chunk stores only document_name (basename).

    The repository does not persist relative path, only document_name
    (basename). The benchmark therefore resolves the basename against the
    corpus definition to recover the relative path used for attribution.
    """
    # resolved at build time and injected via module-level map set by caller
    return _NAME_TO_PATH.get(document_name)


_NAME_TO_PATH: dict[str, str] = {}


def _attributed_sections_for(
    attribution: dict[str, dict], doc_path: str | None, chunk_index: int
) -> list[str]:
    if doc_path is None:
        return []
    entry = attribution.get(doc_path)
    if entry is None:
        return []
    return entry["chunk_sections"].get(str(chunk_index), [])


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def git_commit() -> str:
    try:
        import subprocess

        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).resolve().parents[3]),
            )
            .stdout.strip()
            .splitlines()[0]
        )
    except Exception:  # pragma: no cover
        return "unknown"


def write_outputs(out_path: Path, payload: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # CSV: one row per case with headline fields
    import csv

    csv_path = out_path.with_suffix(".csv")
    rows = []
    for c in payload["per_case"]:
        rows.append(
            {
                "id": c["id"],
                "expected_behavior": c["expected_behavior"],
                "refused": c["refused"],
                "first_relevant_rank": c["first_relevant_rank"] or "",
                "document_hit@1": c["document_hit_at_1"],
                "section_hit@1": c["section_hit_at_1"],
                "section_hit@3": c["section_hit_at_3"],
                "max_score": c["max_score"] or "",
                "highest_false_positive_score": c.get("highest_false_positive_score") or "",
            }
        )
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Production-faithful retrieval-only benchmark (Gold V1.1, DEV/TEST split)"
    )
    parser.add_argument("--vault-root", required=True, help="Obsidian vault root path")
    parser.add_argument("--gold", default=None, type=Path,
                        help="path to gold JSON (default: repo docs/phase2/gold-v1.1.json)")
    parser.add_argument("--corpus", default=None, type=Path,
                        help="path to corpus-v1.json (default: repo docs/phase2/corpus-v1.json)")
    parser.add_argument("--split", default=None, type=Path,
                        help="path to gold-split JSON (default: repo docs/phase2/gold-split-v1.1.json)")
    parser.add_argument("--run-split", choices=["dev", "test", "all"], default="all",
                        help="which split to run (dev/test/all); default all")
    parser.add_argument("--allow-test", action="store_true",
                        help="explicitly allow running TEST split (guard against accidental TEST use)")
    parser.add_argument("--out", default=".runtime/eval/retrieval-baseline-v1.json", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=None, help="defaults to settings.min_score")
    parser.add_argument("--skip-ingest", action="store_true", help="reuse existing eval KB chunks")
    parser.add_argument("--chunk-size", type=int, default=None,
                        help="benchmark-only chunk_size override (production defaults untouched)")
    parser.add_argument("--chunk-overlap", type=int, default=None,
                        help="benchmark-only chunk_overlap override (production defaults untouched)")
    args = parser.parse_args(argv)

    # Privacy gate: never send real data to Langfuse.
    if os.environ.get("LANGFUSE_TRACING_ENABLED", "false").lower() != "false":
        print("ERROR: LANGFUSE_TRACING_ENABLED must be false for benchmark", file=sys.stderr)
        return 2

    # TEST split guard: never run held-out TEST without explicit --allow-test.
    if args.run_split == "test" and not args.allow_test:
        print(
            "ERROR: TEST split requires --allow-test (held-out until selection freeze)",
            file=sys.stderr,
        )
        return 2

    base_settings: Settings = get_settings()
    min_score = args.min_score if args.min_score is not None else base_settings.min_score

    # Benchmark-only chunk override: copy settings, never mutate production defaults.
    settings = base_settings.model_copy(
        update={
            "chunk_size": args.chunk_size if args.chunk_size is not None else base_settings.chunk_size,
            "chunk_overlap": (
                args.chunk_overlap if args.chunk_overlap is not None else base_settings.chunk_overlap
            ),
        }
    )
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap

    vault_root = Path(args.vault_root).expanduser().resolve()
    if not vault_root.exists():
        print(f"ERROR: vault root not found: {vault_root}", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[3]  # My-Knowledge-Base/
    args.gold = args.gold or (repo_root / "docs" / "phase2" / "gold-v1.1.json")
    args.corpus = args.corpus or (repo_root / "docs" / "phase2" / "corpus-v1.json")
    args.split = args.split or (repo_root / "docs" / "phase2" / "gold-split-v1.1.json")
    if not args.out.is_absolute():
        args.out = repo_root / args.out

    docs = load_corpus(args.corpus)
    gold = load_gold(args.gold)
    gold_version = _gold_version_from(args.gold)
    split_map = load_split(args.split)
    gold = filter_gold_by_split(gold, args.run_split, split_map)
    kb_id = eval_kb_id(chunk_size, overlap)

    global _NAME_TO_PATH
    _NAME_TO_PATH = {Path(d["path"]).name: d["path"] for d in docs}

    provider = create_provider(settings)
    repository = RagRepository(settings)
    service = RagService(settings, provider, repository)

    # --- ingest (unless reuse) ---
    # Production-faithful by contract: full production chunk is embedded;
    # overflow surfaces as INGESTION_FAILED and is never masked.
    ingest_summary: dict = {
        "documents": 0, "chunks": 0, "failed": [], "complete": True,
        "production_faithful": True,
        "embedding_truncation": False,
    }
    if not args.skip_ingest:
        for doc in docs:
            try:
                n = ingest_document(service, kb_id, doc, vault_root, chunk_size, overlap)
                ingest_summary["documents"] += 1
                ingest_summary["chunks"] += n
            except Exception as exc:  # surface as INGESTION_FAILED; do not hide
                ingest_summary["failed"].append(
                    {
                        "id": doc["id"],
                        "path": doc["path"],
                        "status": "INGESTION_FAILED",
                        "error": str(exc)[:200],
                    }
                )
                ingest_summary["complete"] = False
    else:
        # count existing chunks from DB
        import psycopg

        with psycopg.connect(repository.settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select count(*) from rag_document_chunks where knowledge_base_id = %s",
                    (kb_id,),
                )
                ingest_summary["chunks"] = cur.fetchone()[0]
        ingest_summary["documents"] = len(docs)

    # --- attribution (static, from source markdown + current chunk params) ---
    attribution = build_attribution_map(vault_root, docs, chunk_size, overlap)

    # --- per-case retrieval ---
    per_case: list[dict] = []
    case_metrics = []
    out_ids = {q["id"] for q in gold if "out-of-corpus" in q.get("notes", "")}
    hard_ids = {q["id"] for q in gold if "hard negative" in q.get("notes", "")}

    # DB stores only basename in document_name; normalize gold documents to
    # basename so matching works, keep full path for humans.
    def _gold_record(q: dict) -> dict:
        record = dict(q)
        sources = []
        for s in q.get("expected_sources", []):
            sources.append(
                {
                    "document": Path(s["document"]).name,
                    "document_path": s["document"],
                    "section": s["section"],
                }
            )
        record["expected_sources"] = sources
        return record

    for q in gold:
        q_record = _gold_record(q)
        raw_top, filtered = retrieve_case(
            service, kb_id, q["question"], args.top_k, min_score, attribution
        )
        metrics = build_case_metrics(q_record, raw_top, filtered, min_score)
        case_metrics.append(metrics)

        record: dict = {
            "id": q["id"],
            "question": q["question"],
            "expected_behavior": q["expected_behavior"],
            "expected_sources": q_record["expected_sources"],
            "raw_top5": raw_top,
            "filtered_hits": filtered,
            "first_relevant_rank": metrics.first_relevant_rank,
            "document_hit_at_1": metrics.document_hit_at[1],
            "document_hit_at_3": metrics.document_hit_at[3],
            "document_hit_at_5": metrics.document_hit_at[5],
            "section_hit_at_1": metrics.section_hit_at[1],
            "section_hit_at_3": metrics.section_hit_at[3],
            "section_hit_at_5": metrics.section_hit_at[5],
            "refused": metrics.refused,
            "relevant_survived_filter": metrics.relevant_survived_filter,
            "wrong_context_acceptance": metrics.wrong_context_acceptance,
            "max_score": metrics.max_score,
            "diagnostic_reason": "",
        }
        if q["expected_behavior"] == "refuse":
            record["highest_false_positive_score"] = metrics.highest_false_positive_score
            record["likely_false_positive_document"] = metrics.likely_false_positive_document
            record["likely_false_positive_section"] = metrics.likely_false_positive_section
        per_case.append(record)

    aggregate = aggregate_metrics(
        case_metrics,
        min_score,
        out_of_corpus_ids=out_ids,
        hard_negative_ids=hard_ids,
    )

    # --- attribution diagnostics across corpus ---
    diag = {"total_chunks": 0, "zero_section_chunks": 0, "single_section_chunks": 0,
            "two_section_chunks": 0, "three_plus_section_chunks": 0,
            "avg_sections_per_chunk": 0.0, "max_sections_per_chunk": 0,
            "single_chunk_documents": 0, "multi_chunk_documents": 0}
    all_d = []
    for doc in docs:
        d = attribution[doc["path"]]["diagnostics"]
        diag["total_chunks"] += d["total_chunks"]
        diag["zero_section_chunks"] += d["zero_section_chunks"]
        diag["single_section_chunks"] += d["single_section_chunks"]
        diag["two_section_chunks"] += d["two_section_chunks"]
        diag["three_plus_section_chunks"] += d["three_plus_section_chunks"]
        diag["max_sections_per_chunk"] = max(diag["max_sections_per_chunk"], d["max_sections_per_chunk"])
        if d["total_chunks"] == 1:
            diag["single_chunk_documents"] += 1
        else:
            diag["multi_chunk_documents"] += 1
        all_d.append(d["avg_sections_per_chunk"])
    diag["avg_sections_per_chunk"] = round(sum(all_d) / len(all_d), 4) if all_d else 0.0
    # degeneracy: many single-chunk docs + chunks attributed to many sections
    diag["section_metric_degenerate"] = (
        diag["single_chunk_documents"] >= 10
        and diag["max_sections_per_chunk"] >= 5
    )

    payload = {
        "benchmark_version": "retrieval-baseline-v1",
        "corpus_version": "v1",
        "gold_version": gold_version,
        "split": args.run_split,
        "split_file": str(args.split.name),
        "git_commit": git_commit(),
        "embedding_model": settings.embedding_model,
        "embedding_dimension": 768,
        "chunk_size": chunk_size,
        "chunk_overlap": overlap,
        "raw_top_k": args.top_k,
        "min_score": min_score,
        "section_attribution_rule": attr.ATTRIBUTION_RULE,
        "knowledge_base_id": kb_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "generation_called": False,
        "langfuse_tracing": False,
        "production_faithful": True,
        "embedding_truncation": False,
        "ingest": ingest_summary,
        "attribution_diagnostics": diag,
        "metrics": aggregate,
        "per_case": per_case,
    }

    write_outputs(args.out, payload)
    print(f"wrote {args.out}")
    print(json.dumps({k: v for k, v in payload.items() if k != "per_case"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
