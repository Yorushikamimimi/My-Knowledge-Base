from app.chunking import chunk_text


def test_chunk_text_keeps_overlap_between_chunks():
    text = " ".join(f"token{i}" for i in range(30))

    chunks = chunk_text(text, chunk_size=12, overlap=3)

    assert [chunk.index for chunk in chunks] == [0, 1, 2]
    assert chunks[0].text.split()[-3:] == chunks[1].text.split()[:3]
    assert chunks[1].text.split()[-3:] == chunks[2].text.split()[:3]


def test_chunk_text_normalizes_whitespace_and_skips_empty_input():
    assert chunk_text(" \n\t ") == []

    chunks = chunk_text("alpha\n\n beta\tgamma", chunk_size=10, overlap=2)

    assert len(chunks) == 1
    assert chunks[0].text == "alpha beta gamma"
