from typing import List, Tuple
import hashlib

from pypdf import PdfReader
from docx import Document as DocxDocument
import tiktoken

from ..config import get_settings


class DocumentProcessor:
    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def extract_text(self, file_path: str, file_type: str) -> str:
        lowered = file_type.lower()
        if lowered == "pdf":
            return self._extract_pdf(file_path)
        if lowered in ("doc", "docx"):
            return self._extract_docx(file_path)
        if lowered == "txt":
            return self._extract_txt(file_path)
        raise ValueError("Unsupported file type")

    def _extract_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        pieces: List[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pieces.append(text)
        return "\n".join(pieces)

    def _extract_docx(self, file_path: str) -> str:
        doc = DocxDocument(file_path)
        lines: List[str] = []
        for para in doc.paragraphs:
            lines.append(para.text)
        return "\n".join(lines)

    def _extract_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as handle:
            return handle.read()

    def chunk_text(self, text: str) -> List[str]:
        tokens = self.tokenizer.encode(text)
        chunks: List[str] = []
        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            segment = tokens[start:end]
            chunks.append(self.tokenizer.decode(segment))
            start = max(end - self.chunk_overlap, end)
        return chunks

    def get_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as handle:
            for block in iter(lambda: handle.read(4096), b""):
                hasher.update(block)
        return hasher.hexdigest()

    def process_document(self, file_path: str, file_type: str) -> Tuple[List[str], str]:
        text = self.extract_text(file_path, file_type)
        chunks = self.chunk_text(text)
        digest = self.get_file_hash(file_path)
        return chunks, digest


document_processor = DocumentProcessor()
