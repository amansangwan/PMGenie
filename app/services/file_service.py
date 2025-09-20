import os
import time
import tempfile
import logging
from openai import OpenAI
from app.services.s3_service import download_fileobj
from app.services.qdrant_service import upsert_points
from app.utils.text_extraction import parse_pdf_file, parse_docx_file, chunk_text

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CHUNKS_PER_FILE = 1000
CHUNK_MAX_CHARS = 3500
BATCH_UPSERT_SIZE = 64


def save_file_and_process_from_s3(
    s3_key: str,
    filename: str,
    projectId: str,
    chatSessionId: str,
    fileId: int,
    is_kb: bool = False,
):
    """Download file from S3 to temp file, parse safely, embed chunks, upsert to Qdrant."""
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        download_fileobj(s3_key, tmp)

        text = ""
        ext = filename.lower().split(".")[-1]
        if ext == "pdf":
            text = parse_pdf_file(tmp.name)
        elif ext in ("docx", "doc"):
            text = parse_docx_file(tmp.name)
        elif ext in ("png", "jpg", "jpeg", "bmp", "gif"):
            logger.info("Image upload detected: skipping text extraction.")
            text = ""
        else:
            tmp.seek(0)
            try:
                text = tmp.read().decode("utf-8", errors="ignore")
            except Exception:
                text = ""

        chunks = list(chunk_text(text)) if text else []
        if len(chunks) > MAX_CHUNKS_PER_FILE:
            chunks = chunks[:MAX_CHUNKS_PER_FILE]

        points_batch = []
        for i, ch in enumerate(chunks):
            if len(ch) > CHUNK_MAX_CHARS:
                ch = ch[:CHUNK_MAX_CHARS]

            resp = openai_client.embeddings.create(
                model="text-embedding-3-small", input=ch
            )
            emb = resp.data[0].embedding

            points_batch.append(
                {
                    "id": int(time.time() * 1000) + i,
                    "vector": emb,
                    "payload": {
                        "type": "file_chunk",
                        "projectId": projectId or "",
                        "chatSessionId": chatSessionId or "",
                        "filename": filename,
                        "fileId": fileId,
                        "is_kb": is_kb,
                    },
                }
            )

            if len(points_batch) >= BATCH_UPSERT_SIZE:
                upsert_points(points_batch)
                points_batch = []

        if points_batch:
            upsert_points(points_batch)

        logger.info(
            "Completed file processing: fileId=%s, chunks=%d", fileId, len(chunks)
        )
