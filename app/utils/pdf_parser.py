import fitz  # PyMuPDF

def parse_pdf_bytes(data: bytes) -> str:
    with fitz.open(stream=data, filetype="pdf") as doc:
        texts = []
        for page in doc:
            texts.append(page.get_text())
        return "\n".join(texts)
