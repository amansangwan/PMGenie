# ai_reasoning_engine/memory_manager.py
import os
import uuid
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

load_dotenv("creds.env")

class MemoryManager:
    def __init__(self, collection_name="ai_memory"):
        self.collection_name = collection_name

        # OpenAI client (explicit)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Qdrant client
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.client_qdrant = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

        self._init_collection()

    def _init_collection(self):
        existing = [c.name for c in self.client_qdrant.get_collections().collections]
        if self.collection_name not in existing:
            self.client_qdrant.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )

        # Indexes for filtering by project/chat
        for field in ["projectId", "chatSessionId", "tags"]:
            try:
                self.client_qdrant.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema="keyword",
                )
            except Exception as e:
                if "already exists" not in str(e):
                    raise

    def get_embedding(self, text: str):
        resp = self.client.embeddings.create(model="text-embedding-3-small", input=text)
        return resp.data[0].embedding

    def add_memory(self, user_input, ai_response, project_name=None, session_id=None, tags=None):
        text = f"User: {user_input}\nAI: {ai_response}"
        embedding = self.get_embedding(text)

        payload = {
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(),
            "projectId": project_name,         # aligned key
            "chatSessionId": session_id,       # aligned key
            "tags": tags or []
        }

        self.client_qdrant.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": payload
            }]
        )

    def query_memory(self, query_text, top_k=3, project_name=None, session_id=None, tags=None):
        embedding = self.get_embedding(query_text)

        must = []
        if project_name:
            must.append(FieldCondition(key="projectId", match=MatchValue(value=project_name)))
        if session_id:
            must.append(FieldCondition(key="chatSessionId", match=MatchValue(value=session_id)))
        if tags:
            must.append(FieldCondition(key="tags", match=MatchValue(value=tags)))

        qfilter = Filter(must=must) if must else None

        hits = self.client_qdrant.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=top_k,
            query_filter=qfilter,
        )
        return [hit.payload.get("text") for hit in hits]

    def clear_memory(self):
        self.client_qdrant.delete_collection(self.collection_name)
        self._init_collection()
