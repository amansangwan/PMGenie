from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import openai
import os
import uuid
import datetime

load_dotenv("creds.env")

class MemoryManager:
    def __init__(self, collection_name="ai_memory"):
        self.collection_name = collection_name

        # Load credentials
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        # Qdrant client
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
        )

        self._init_collection()

    def _init_collection(self):
        existing_collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name not in existing_collections:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # OpenAI vector size
            )

        # Ensure required payload indexes exist for filtering
        for field in ["project", "session_id", "tags"]:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema="keyword"
                )
            except Exception as e:
                if "already exists" not in str(e):
                    raise

    def get_embedding(self, text):
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def add_memory(self, user_input, ai_response, project_name=None, session_id=None, tags=None):
        text = f"User: {user_input}\nAI: {ai_response}"
        embedding = self.get_embedding(text)

        payload = {
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(),
            "project": project_name,
            "session_id": session_id,
            "tags": tags or []
        }

        self.client.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": payload
            }]
        )

    def query_memory(self, query_text, top_k=3, project_name=None, session_id=None, tags=None):
        embedding = self.get_embedding(query_text)

        conditions = []
        if project_name:
            conditions.append(FieldCondition(key="project", match=MatchValue(value=project_name)))
        if session_id:
            conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
        if tags:
            conditions.append(FieldCondition(key="tags", match=MatchValue(value=tags)))

        query_filter = Filter(must=conditions) if conditions else None

        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=top_k,
            query_filter=query_filter
        )

        return [hit.payload["text"] for hit in hits]

    def clear_memory(self):
        self.client.delete_collection(self.collection_name)
        self._init_collection()
