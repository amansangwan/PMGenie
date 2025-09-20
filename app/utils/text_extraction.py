import fitz  # PyMuPDF
import docx
import re
from typing import List, Generator


# -----------------------------
# PDF Parser (stream-safe)
# -----------------------------
def parse_pdf_file(filepath: str) -> str:
    """
    Extract text from a PDF file page by page.
    Avoids inflating memory by processing incrementally.
    """
    text_parts = []
    with fitz.open(filepath) as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


# -----------------------------
# DOCX Parser
# -----------------------------
def parse_docx_file(filepath: str) -> str:
    """
    Extract text from a DOCX file paragraph by paragraph.
    """
    text_parts = []
    doc = docx.Document(filepath)
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())
    return "\n".join(text_parts)


# -----------------------------
# Text Chunker
# -----------------------------
def chunk_text(
    text: str,
    max_chars: int = 1000,
    overlap: int = 100,
) -> Generator[str, None, None]:
    """
    Split text into overlapping chunks.
    Each chunk has max_chars, with overlap to preserve context.
    """
    if not text:
        return []

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        yield chunk
        start += max_chars - overlap
