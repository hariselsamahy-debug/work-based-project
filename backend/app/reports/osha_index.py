"""Keyword (BM25) search over the OSHA regulation files in data/osha/ (PDF or .txt).

BM25 is enough for regulation text, where section numbers and terms match literally.
Swap in an embedding index here later without touching the rest of the report code.
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

log = logging.getLogger(__name__)

CHUNK_CHARS = 1500
CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class Chunk:
    source: str
    page: int
    text: str


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)*", text.lower())


def _split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    step = CHUNK_CHARS - CHUNK_OVERLAP
    return [text[i:i + CHUNK_CHARS] for i in range(0, max(len(text), 1), step) if text[i:i + CHUNK_CHARS].strip()]


def _read_pages(path: Path) -> list[str]:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return [page.extract_text() or "" for page in PdfReader(path).pages]
    return [path.read_text(encoding="utf-8", errors="ignore")]


class OshaIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self._bm25 = BM25Okapi([_tokenize(c.text) for c in chunks]) if chunks else None

    @classmethod
    def from_dir(cls, directory: Path) -> "OshaIndex":
        chunks = []
        files = sorted(p for p in directory.glob("*") if p.suffix.lower() in {".pdf", ".txt"})
        for path in files:
            try:
                for page_no, page in enumerate(_read_pages(path), start=1):
                    chunks.extend(Chunk(path.name, page_no, part) for part in _split(page))
            except Exception:
                log.exception("Could not read OSHA file %s", path)
        log.info("OSHA index: %d chunks from %d files", len(chunks), len(files))
        return cls(chunks)

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.chunks[i] for i in ranked[:k] if scores[i] > 0]
