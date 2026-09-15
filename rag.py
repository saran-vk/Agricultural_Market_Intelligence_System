"""PDF retrieval with page citations and local Ollama analysis."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import faiss
import pymupdf
import httpx
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
REPORTS_DIR, UPLOADS_DIR, INDEX_DIR = ROOT / "data" / "reports", ROOT / "data" / "uploads", ROOT / "data" / "index"
METADATA_FILE, FAISS_FILE = INDEX_DIR / "chunks.json", INDEX_DIR / "reports.faiss"

@dataclass(frozen=True)
class Chunk:
    id: str
    document_name: str
    document_path: str
    page_number: int
    text: str
    source_url: str | None = None
    @property
    def citation(self) -> str: return f"{self.document_name} — p. {self.page_number}"

def _chunks(text: str, size: int = 900, overlap: int = 160) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 80: return []
    result, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary > start + size // 2: end = boundary + 1
        result.append(text[start:end].strip())
        if end == len(text): break
        start = max(end - overlap, start + 1)
    return result

def extract_pdf(pdf_path: Path, source_url: str | None = None) -> tuple[list[Chunk], list[int]]:
    document, chunks, blank = pymupdf.open(pdf_path), [], []
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()[:12]
    for page_i, page in enumerate(document):
        page_chunks = _chunks(page.get_text("text"))
        if not page_chunks: blank.append(page_i + 1)
        chunks.extend(Chunk(f"{digest}-{page_i + 1}-{offset}", pdf_path.name, str(pdf_path), page_i + 1, text, source_url) for offset, text in enumerate(page_chunks))
    document.close()
    return chunks, blank

class ReportIndex:
    def __init__(self, embedding_model: str | None = None) -> None:
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self._model: SentenceTransformer | None = None
        self.chunks: list[Chunk] = []
        self.index: faiss.Index | None = None
    @property
    def model(self) -> SentenceTransformer:
        if self._model is None: self._model = SentenceTransformer(self.embedding_model)
        return self._model
    def load(self) -> bool:
        if not (METADATA_FILE.exists() and FAISS_FILE.exists()): return False
        self.chunks = [Chunk(**item) for item in json.loads(METADATA_FILE.read_text())]
        self.index = faiss.read_index(str(FAISS_FILE))
        return bool(self.chunks)
    def build(self, pdf_paths: list[Path]) -> dict[str, Any]:
        all_chunks, unreadable = [], {}
        for path in pdf_paths:
            chunks, blank = extract_pdf(path)
            all_chunks.extend(chunks)
            if blank: unreadable[path.name] = blank
        if not all_chunks: raise ValueError("No searchable text was found in the selected PDFs.")
        vectors = np.asarray(self.model.encode([chunk.text for chunk in all_chunks], normalize_embeddings=True, show_progress_bar=False), dtype="float32")
        index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_FILE.write_text(json.dumps([asdict(chunk) for chunk in all_chunks], ensure_ascii=False))
        faiss.write_index(index, str(FAISS_FILE)); self.chunks, self.index = all_chunks, index
        return {"documents": len(pdf_paths), "chunks": len(all_chunks), "unreadable_pages": unreadable}
    def retrieve(self, question: str, limit: int = 5) -> list[Chunk]:
        if not question.strip() or (self.index is None and not self.load()): return []
        assert self.index is not None
        vector = np.asarray(self.model.encode([question], normalize_embeddings=True), dtype="float32")
        _, positions = self.index.search(vector, min(limit, len(self.chunks)))
        return [self.chunks[position] for position in positions[0] if position >= 0]

def analyze(question: str, chunks: list[Chunk]) -> dict[str, Any]:
    if not chunks: return {"message": "No relevant evidence is indexed yet.", "sections": {}, "sources": []}
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if not model: return {"message": "Set OLLAMA_MODEL after installing a local Ollama model to generate analysis. Retrieved evidence is shown below.", "sections": {}, "sources": chunks}
    labels = {f"S{i + 1}": chunk for i, chunk in enumerate(chunks)}
    context = "\n\n".join(f"[{key}] {chunk.citation}\n{chunk.text}" for key, chunk in labels.items())
    prompt = f'''Use ONLY the evidence below. Do not invent facts, prices, dates, or definitions. Return JSON only: {{"insight":{{"text":"...","citations":["S1"]}},"market_trend":{{"text":"...","citations":["S1"]}},"historical_observation":{{"text":"...","citations":["S1"]}},"terminology":{{"text":"...","citations":["S1"]}}}}. Unsupported sections must say "Not established by the retrieved evidence."\nQuestion: {question}\nEvidence:\n{context}'''
    try:
        response = httpx.post(f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')}/api/chat", json={"model": model, "stream": False, "format": "json", "messages": [{"role": "user", "content": prompt}]}, timeout=90)
        response.raise_for_status(); payload = json.loads(response.json()["message"]["content"])
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as error:
        return {"message": f"Ollama analysis is unavailable: {error}", "sections": {}, "sources": chunks}
    sections, used = {}, []
    for key in ("insight", "market_trend", "historical_observation", "terminology"):
        item = payload.get(key, {}) if isinstance(payload, dict) else {}
        cited = [labels[label] for label in item.get("citations", []) if label in labels]
        sections[key] = {"text": str(item.get("text", "Not established by the retrieved evidence.")), "sources": cited}; used.extend(cited)
    return {"message": "", "sections": sections, "sources": list(dict.fromkeys(used)) or chunks}

def find_year_values(chunks: list[Chunk]) -> list[tuple[int, float]]:
    values: dict[int, float] = {}
    for chunk in chunks:
        for year, value in re.findall(r"\b(20\d{2})\s*(?:[:—-])\s*([\d,.]+)\b", chunk.text): values[int(year)] = float(value.replace(",", ""))
    return sorted(values.items()) if len(values) >= 2 else []
