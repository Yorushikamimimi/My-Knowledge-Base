"""Tests for eval.section_attribution (pure functions)."""

from app.chunking import chunk_text

from eval import section_attribution as attr


SAMPLE = """# MySQL

## 1. 索引

帮助快速查找。

### 为什么用 B+Tree

层数低。

## 2. 事务

ACID 定义。

## 3. MVCC

一致性快照。
"""


def test_reconstruct_chunk_text_matches_production():
    # benchmark reconstruction must equal production chunk_text output exactly
    for size, overlap in [(450, 80), (300, 50), (200, 40), (120, 24)]:
        chunks = chunk_text(SAMPLE, size, overlap)
        recon = attr.reconstruct_chunk_text(SAMPLE, size, overlap)
        assert [c.text for c in chunks] == recon


def test_parse_headings_finds_all_levels():
    heads = attr.parse_headings(SAMPLE)
    titles = [(h.level, h.title) for h in heads]
    assert (1, "MySQL") in titles
    assert (2, "1. 索引") in titles
    assert (3, "为什么用 B+Tree") in titles
    assert (2, "2. 事务") in titles
    assert (2, "3. MVCC") in titles


def test_parse_headings_cursor_avoids_body_false_match():
    # "覆盖索引" appears as an H3; body text also mentions it earlier? craft:
    text = (
        "# D\n\n"
        "正文提到覆盖索引一次。\n\n"
        "### 覆盖索引\n\n"
        "叶子存主键。\n"
    )
    heads = attr.parse_headings(text)
    h3 = [h for h in heads if h.level == 3]
    assert len(h3) == 1
    assert h3[0].title == "覆盖索引"
    # its token position must come after the body text tokens
    assert h3[0].token_start >= 4


def test_build_section_ranges_h2_only():
    heads = attr.parse_headings(SAMPLE)
    secs = attr.build_section_ranges(heads, token_count=50, target_levels={2})
    titles = [s.title for s in secs]
    assert titles == ["1. 索引", "2. 事务", "3. MVCC"]
    # H2 sections include their H3 content: 1. 索引 ends where 2. 事务 begins
    assert secs[0].token_end == secs[1].token_start
    # heading path: H1 ancestor + self title
    assert secs[0].heading_path == ("MySQL", "1. 索引")
    assert secs[1].heading_level == 2


def test_build_section_ranges_h3_keeps_exact_identity():
    heads = attr.parse_headings(SAMPLE)
    secs = attr.build_section_ranges(heads, token_count=50, target_levels={3})
    h3 = [s for s in secs if s.title == "为什么用 B+Tree"]
    assert len(h3) == 1
    assert h3[0].heading_level == 3
    assert h3[0].heading_path == ("MySQL", "1. 索引", "为什么用 B+Tree")


def test_chunk_ranges_matches_production_stepping():
    # token count 1000, chunk 450/overlap 80 -> chunks at 0, 370, 740, 920(?) verify via production
    tokens = ["t" + str(i) for i in range(1000)]
    text = " ".join(tokens)
    chunks = chunk_text(text, 450, 80)
    ranges = attr.chunk_ranges(1000, 450, 80)
    assert len(ranges) == len(chunks)
    for r, c in zip(ranges, chunks):
        assert " ".join(tokens[r.token_start:r.token_end]) == c.text


def test_attribute_sections_multisection_chunk():
    # small chunk params force a chunk to span multiple H2 sections
    sections, ranges, overlaps = attr.attribute_sections(
        SAMPLE, chunk_size=8, overlap=2, target_levels={2}
    )
    multisection = [o for o in overlaps if o.attributed]
    # at least one chunk overlaps more than one section (small window)
    chunk_secs: dict[int, int] = {}
    for o in multisection:
        chunk_secs[o.chunk_index] = chunk_secs.get(o.chunk_index, 0) + 1
    assert any(v >= 2 for v in chunk_secs.values()), f"expected a multi-section chunk, got {chunk_secs}"


def test_attribution_rule_constants():
    assert attr.SECTION_COVERAGE_THRESHOLD == 0.5
    assert attr.MIN_OVERLAP_TOKENS == 30
    assert "0.5" in attr.ATTRIBUTION_RULE
    assert "30" in attr.ATTRIBUTION_RULE


def test_overlap_math_and_attribution_flag():
    o = attr.ChunkSectionOverlap(
        chunk_index=0,
        section_title="A",
        section_heading_level=2,
        heading_path=("H1", "A"),
        overlap_tokens=40,
        section_token_count=80,
        chunk_token_count=450,
    )
    assert o.section_coverage == 0.5  # 40/80
    assert abs(o.chunk_coverage - 40 / 450) < 1e-9
    assert o.attributed is True  # coverage >= 0.5

    o2 = attr.ChunkSectionOverlap(
        chunk_index=0,
        section_title="B",
        section_heading_level=2,
        heading_path=("H1", "B"),
        overlap_tokens=10,
        section_token_count=100,
        chunk_token_count=450,
    )
    assert o2.attributed is False  # 0.1 coverage, 10 tokens < 30

    o3 = attr.ChunkSectionOverlap(
        chunk_index=0,
        section_title="C",
        section_heading_level=2,
        heading_path=("H1", "C"),
        overlap_tokens=35,
        section_token_count=500,
        chunk_token_count=450,
    )
    assert o3.attributed is True  # coverage 0.07 but overlap 35 >= 30


def test_chunk_param_change_keeps_gold_identity():
    # section titles (Gold identity) must be identical across chunk params
    for size, overlap in [(450, 80), (300, 50), (200, 40), (120, 24)]:
        sections, _, _ = attr.attribute_sections(SAMPLE, size, overlap, target_levels={2})
        assert [s.title for s in sections] == ["1. 索引", "2. 事务", "3. MVCC"]
