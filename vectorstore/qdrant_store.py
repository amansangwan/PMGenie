# vectorstore/qdrant_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "ai_memory"

def init_qdrant(vector_size=384):  # MiniLM has 384 dimensions
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

def add_memory_to_qdrant(id, vector, payload):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=id, vector=vector, payload=payload)]
    )

def query_qdrant(query_vector, top_k=3, filters=None):
    return client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        query_filter=filters
    )
