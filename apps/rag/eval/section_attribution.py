"""Section attribution for the retrieval benchmark.

Maps retrieved chunks (document + chunk_index + content) back to the real
headings (sections) of the source Markdown, using exactly the same
tokenization as the production chunker (apps/rag/app/chunking.py).

The production chunker normalizes all whitespace runs to single spaces and
splits on whitespace. This module mirrors that behaviour so the benchmark and
production pipelines agree on token ranges. Chunk parameter changes (Phase 2B)
only affect this layer; the Gold dataset (document + section) is unaffected.

Design decisions (Phase 2A-3a / 3b):
- Gold sections are H2 headings; H3+ headings exist in the corpus but are
  never Gold expected_sources. Attribution still records heading_path so
  exact section identity is never lost.
- Attribution rule (candidate, versioned in constants):
      section_coverage >= SECTION_COVERAGE_THRESHOLD
      OR overlap_tokens >= MIN_OVERLAP_TOKENS
  Both constants are explicit and unit-tested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Versioned attribution rule constants (do not scatter magic numbers)
# ---------------------------------------------------------------------------

SECTION_COVERAGE_THRESHOLD = 0.5
MIN_OVERLAP_TOKENS = 30
ATTRIBUTION_RULE = (
    f"section_coverage>={SECTION_COVERAGE_THRESHOLD} "
    f"OR overlap_tokens>={MIN_OVERLAP_TOKENS}"
)


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    token_start: int  # token index where the heading text begins
    token_end: int  # token index just past the heading text
    line_no: int  # 1-based line in the source file


@dataclass(frozen=True)
class Section:
    title: str  # exact heading title (Gold identity)
    heading_level: int
    token_start: int  # inclusive
    token_end: int  # exclusive
    heading_path: tuple[str, ...]  # (H1, H2, ...) ancestors + self title


@dataclass(frozen=True)
class ChunkRange:
    index: int
    token_start: int
    token_end: int


@dataclass(frozen=True)
class ChunkSectionOverlap:
    chunk_index: int
    section_title: str
    section_heading_level: int
    heading_path: tuple[str, ...]
    overlap_tokens: int
    section_token_count: int
    chunk_token_count: int

    @property
    def section_coverage(self) -> float:
        if self.section_token_count == 0:
            return 0.0
        return self.overlap_tokens / self.section_token_count

    @property
    def chunk_coverage(self) -> float:
        if self.chunk_token_count == 0:
            return 0.0
        return self.overlap_tokens / self.chunk_token_count

    @property
    def attributed(self) -> bool:
        return (
            self.section_coverage >= SECTION_COVERAGE_THRESHOLD
            or self.overlap_tokens >= MIN_OVERLAP_TOKENS
        )


@dataclass(frozen=True)
class AttributionResult:
    """Attribution for one retrieved chunk."""

    chunk_index: int
    token_start: int
    token_end: int
    sections: list[Section] = field(default_factory=list)
    overlaps: list[ChunkSectionOverlap] = field(default_factory=list)

    @property
    def attributed_sections(self) -> list[str]:
        return [
            o.section_title for o in self.overlaps if o.attributed
        ]


# ---------------------------------------------------------------------------
# Tokenization (mirrors production chunker exactly)
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> list[str]:
    return normalize_text(text).split()


def chunk_ranges(token_count: int, chunk_size: int, overlap: int) -> list[ChunkRange]:
    """Reproduce production chunk_text window stepping exactly.

    Equivalent to apps/rag/app/chunking.py: start=0; end=min(start+size, n);
    if end==n break; start=end-overlap.
    """
    ranges: list[ChunkRange] = []
    start = 0
    while start < token_count:
        end = min(start + chunk_size, token_count)
        ranges.append(ChunkRange(index=len(ranges), token_start=start, token_end=end))
        if end == token_count:
            break
        start = end - overlap
    return ranges


def reconstruct_chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Reconstruct chunk texts exactly as production chunk_text would.

    Used by the consistency test: benchmark reconstruction == production output.
    """
    tokens = tokenize(text)
    return [
        " ".join(tokens[r.token_start:r.token_end])
        for r in chunk_ranges(len(tokens), chunk_size, overlap)
    ]


# ---------------------------------------------------------------------------
# Heading / section extraction
# ---------------------------------------------------------------------------


def parse_headings(text: str) -> list[Heading]:
    """Locate each Markdown heading in the normalized token stream.

    Uses cursor-based sequential search of '#<level> <title>' inside the
    normalized text, then maps the character offset to a token index. The
    cursor prevents a later heading title from matching an earlier occurrence
    of the same words in body text.
    """
    normalized = normalize_text(text)
    tokens = tokenize(text)
    boundaries: list[tuple[int, int]] = []
    pos = 0
    for tok in tokens:
        idx = normalized.find(tok, pos)
        if idx < 0:  # pragma: no cover - defensive; tokens come from the text
            idx = pos
        boundaries.append((idx, idx + len(tok)))
        pos = idx + len(tok)

    headings: list[Heading] = []
    cursor = 0
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.*)$", raw_line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if not title:
            continue
        pattern = "#" * level + " " + title
        idx = normalized.find(pattern, cursor)
        if idx < 0:
            # Fallback: search from 0 (tolerates markdown variations)
            idx = normalized.find(pattern)
            if idx < 0:  # pragma: no cover - cannot happen for real corpus
                continue
        cursor = idx + len(pattern)
        token_start = sum(1 for b in boundaries if b[0] <= idx)
        token_end = sum(1 for b in boundaries if b[0] < idx + len(pattern))
        headings.append(
            Heading(
                level=level,
                title=title,
                token_start=token_start,
                token_end=token_end,
                line_no=line_no,
            )
        )
    return headings


def build_section_ranges(
    headings: list[Heading], token_count: int, target_levels: set[int] | None = None
) -> list[Section]:
    """Build section ranges for headings at target levels.

    A section spans [heading.token_start, next heading.token_start) where
    "next" is the next heading at the same or a shallower (smaller) level.
    heading_path records (H1 title, H2 title, ..., self title) so exact
    section identity is preserved even when Gold later references H3.
    """
    if target_levels is None:
        target_levels = {h.level for h in headings}
    sections: list[Section] = []
    h2_ancestor: str | None = None
    h1_ancestor: str | None = None

    for i, h in enumerate(headings):
        if h.level == 1:
            h1_ancestor = h.title
            h2_ancestor = None
        elif h.level == 2:
            h2_ancestor = h.title

        if h.level not in target_levels:
            continue

        # section end: next heading with level <= h.level
        end = token_count
        for j in range(i + 1, len(headings)):
            if headings[j].level <= h.level:
                end = headings[j].token_start
                break
        path: list[str] = []
        if h.level >= 2 and h1_ancestor:
            path.append(h1_ancestor)
        if h.level >= 3 and h2_ancestor:
            path.append(h2_ancestor)
        path.append(h.title)
        sections.append(
            Section(
                title=h.title,
                heading_level=h.level,
                token_start=h.token_start,
                token_end=end,
                heading_path=tuple(path),
            )
        )
    return sections


def attribute_sections(
    text: str, chunk_size: int, overlap: int, target_levels: set[int] | None = None
) -> tuple[list[Section], list[ChunkRange], list[ChunkSectionOverlap]]:
    """Attribute every chunk (under the given chunk params) to sections.

    Returns (sections, chunk_ranges, all chunk x section overlaps with their
    token counts and coverage ratios). Attribution decision is on each
    ChunkSectionOverlap.attributed.
    """
    tokens = tokenize(text)
    token_count = len(tokens)
    headings = parse_headings(text)
    sections = build_section_ranges(headings, token_count, target_levels)
    ranges = chunk_ranges(token_count, chunk_size, overlap)

    overlaps: list[ChunkSectionOverlap] = []
    for cr in ranges:
        for sec in sections:
            ov = min(cr.token_end, sec.token_end) - max(cr.token_start, sec.token_start)
            if ov > 0:
                overlaps.append(
                    ChunkSectionOverlap(
                        chunk_index=cr.index,
                        section_title=sec.title,
                        section_heading_level=sec.heading_level,
                        heading_path=sec.heading_path,
                        overlap_tokens=ov,
                        section_token_count=sec.token_end - sec.token_start,
                        chunk_token_count=cr.token_end - cr.token_start,
                    )
                )
    return sections, ranges, overlaps


def attribution_diagnostics(
    sections: list[Section],
    ranges: list[ChunkRange],
    overlaps: list[ChunkSectionOverlap],
) -> dict:
    """Aggregate diagnostics for one document (see benchmark report schema)."""
    per_chunk_count: dict[int, int] = {}
    for o in overlaps:
        if o.attributed:
            per_chunk_count[o.chunk_index] = per_chunk_count.get(o.chunk_index, 0) + 1
    counts = list(per_chunk_count.values())
    total_chunks = len(ranges)
    return {
        "total_chunks": total_chunks,
        "zero_section_chunks": total_chunks - len(counts),
        "single_section_chunks": sum(1 for c in counts if c == 1),
        "two_section_chunks": sum(1 for c in counts if c == 2),
        "three_plus_section_chunks": sum(1 for c in counts if c >= 3),
        "avg_sections_per_chunk": round(sum(counts) / total_chunks, 4) if total_chunks else 0.0,
        "max_sections_per_chunk": max(counts) if counts else 0,
        "sections_total": len(sections),
    }
