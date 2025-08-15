import os
import time
from openai import OpenAI
from app.utils.pdf_parser import parse_pdf_bytes
from app.utils.docx_parser import parse_docx_bytes
from app.utils.text_chunker import chunk_text
from app.services.qdrant_service import upsert_points
from dotenv import load_dotenv
load_dotenv("creds.env")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def save_file_and_process(data: bytes, filename: str, projectId: str, chatSessionId: str,
                          fileId: int, is_kb: bool = False):
    """Parses file, chunks text, embeds chunks, and stores in Qdrant."""
    text = ""
    if filename.lower().endswith(".pdf"):
        text = parse_pdf_bytes(data)
    elif filename.lower().endswith(".docx"):
        text = parse_docx_bytes(data)
    else:
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    chunks = chunk_text(text)
    for ch in chunks:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=ch
        ).data[0].embedding

        upsert_points([{
            "id": int(time.time() * 1000),
            "vector": emb,
            "payload": {
                "type": "file_chunk",
                "projectId": projectId or "",
                "chatSessionId": chatSessionId or "",
                "filename": filename,
                "fileId": fileId,
                "is_kb": is_kb
            },
        }])
