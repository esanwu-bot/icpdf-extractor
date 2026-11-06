"""PDF loader: identity, page geometry and fail-closed validation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pymupdf as fitz

from icpdf import PARSER_VERSION
from icpdf.domain import Document, DocumentType
from icpdf.parser.coords import PageGeometry


class PDFLoadError(RuntimeError):
    """Raised when a PDF cannot be used as evidence."""


class PDFEncryptedError(PDFLoadError):
    """Raised when the PDF needs a password; encrypted data is not evidence."""


@dataclass(frozen=True)
class LoadedPDF:
    path: Path
    sha256: str
    document: Document
    geometries: tuple[PageGeometry, ...]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pdf(path: str | Path, *, dpi: float = 150.0,
             document_type: DocumentType = DocumentType.DATASHEET,
             document_id: str | None = None) -> LoadedPDF:
    path = Path(path)
    if not path.is_file():
        raise PDFLoadError(f"PDF not found: {path}")
    sha = file_sha256(path)
    try:
        with fitz.open(str(path)) as doc:
            if doc.needs_pass or doc.is_encrypted:
                raise PDFEncryptedError(f"encrypted PDF cannot be used: {path.name}")
            if doc.page_count < 1:
                raise PDFLoadError(f"PDF has no pages: {path.name}")
            geometries = tuple(
                PageGeometry.from_page(page, dpi=dpi, page_number=i + 1)
                for i, page in enumerate(doc)
            )
            document = Document(
                document_id=document_id or f"doc-{sha[:12]}",
                filename=path.name,
                sha256=sha,
                page_count=doc.page_count,
                manufacturer=doc.metadata.get("author") or None,
                document_title=doc.metadata.get("title") or None,
                document_type=document_type,
                parser_version=PARSER_VERSION,
                created_at=datetime.now(timezone.utc),
                page_sizes=[(g.rect[2] - g.rect[0], g.rect[3] - g.rect[1])
                            for g in geometries],
                page_rotations=[g.rotation for g in geometries],
            )
    except PDFLoadError:
        raise
    except Exception as exc:                                   # noqa: BLE001
        raise PDFLoadError(f"cannot open PDF {path.name}: {type(exc).__name__}: {exc}") from exc
    return LoadedPDF(path=path, sha256=sha, document=document, geometries=geometries)
