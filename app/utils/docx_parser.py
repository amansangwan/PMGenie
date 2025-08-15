from docx import Document
from io import BytesIO

def parse_docx_bytes(data: bytes) -> str:
    """Extracts plain text from DOCX file bytes."""
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
