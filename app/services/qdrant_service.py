import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from dotenv import load_dotenv
load_dotenv("creds.env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "ai_memory")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def ensure_collection(vector_size: int = 1536):
    exists = False
    try:
        client.get_collection(QDRANT_COLLECTION)
        exists = True
    except Exception:
        exists = False
    if not exists:
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

from typing import List, Dict, Any

def upsert_points(points: List[Dict[str, Any]]):
    ensure_collection()
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)


def search(query_vector: List[float], limit: int = 10, filters: Dict[str, Any] | None = None):
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    qfilter = None
    if filters:
        must = []
        for k, v in filters.items():
            must.append(FieldCondition(key=k, match=MatchValue(value=v)))
        qfilter = Filter(must=must)
    return client.search(collection_name=QDRANT_COLLECTION, query_vector=query_vector, limit=limit, query_filter=qfilter)
