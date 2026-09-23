import base64
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfWriter

from app.parsers import DocumentParseError
from app.schemas import IngestRequest
from app.service import RagService


def _request(filename: str, content_type: str, data: bytes) -> IngestRequest:
    return IngestRequest(
        knowledgeBaseId="kb-test",
        documentId="doc-test",
        documentName=filename,
        contentType=content_type,
        contentBase64=base64.b64encode(data).decode("ascii"),
    )


def _service() -> tuple[RagService, Mock, Mock]:
    provider = Mock()
    provider.name = "stub"
    provider.embed.return_value = [0.1, 0.2]
    repository = Mock()
    settings = SimpleNamespace(chunk_size=20, chunk_overlap=2)
    return RagService(settings, provider, repository), provider, repository


def test_ingest_rejects_pdf_without_extractable_text_before_embedding_or_storage():
    pdf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)
    service, provider, repository = _service()

    with pytest.raises(DocumentParseError) as pdf_error:
        service.ingest(_request("scan.pdf", "application/pdf", pdf.getvalue()))

    assert "No indexable text" in str(pdf_error.value)
    assert "Scanned PDFs may require OCR" in str(pdf_error.value)
    provider.embed.assert_not_called()
    repository.replace_document_chunks.assert_not_called()

    text_service, text_provider, text_repository = _service()
    with pytest.raises(DocumentParseError) as text_error:
        text_service.ingest(_request("empty.md", "text/markdown", b"\n   \n"))

    assert "No indexable text" in str(text_error.value)
    assert "OCR" not in str(text_error.value)
    text_provider.embed.assert_not_called()
    text_repository.replace_document_chunks.assert_not_called()


def test_ingest_stores_chunks_when_text_is_extractable():
    service, provider, repository = _service()
    text = "The synthetic routing marker is cedar-731. " * 12

    response = service.ingest(_request("notes.txt", "text/plain", text.encode()))

    assert response.chunkCount > 0
    assert response.provider == "stub"
    provider.embed.assert_called()
    repository.replace_document_chunks.assert_called_once()
