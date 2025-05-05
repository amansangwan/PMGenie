# memory_manager/memory_manager.py

from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import datetime

class MemoryManager:
    def __init__(self, persist_directory="./vector_db"):
        self.client = Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection(name="ai_memory")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def add_memory(self, user_input, ai_response, project_name=None, session_id=None, tags=None):
        """
        Save AI memory with rich metadata for future retrieval
        """
        text = f"User: {user_input}\nAI: {ai_response}"
        embedding = self.embedder.encode([text])[0].tolist()

        metadata = {
            "timestamp": datetime.datetime.now().isoformat()
        }

        if project_name:
            metadata["project"] = project_name
        if session_id:
            metadata["session_id"] = session_id
        if tags:
            metadata["tags"] = tags  # List of strings, e.g., ['summary', 'jira']

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def query_memory(self, query_text, top_k=1, project_name=None, session_id=None, tags=None):
        """
        Retrieve relevant memories based on input and metadata filters
        """
        embedding = self.embedder.encode([query_text])[0].tolist()

        metadata_filter = {}
        if project_name:
            metadata_filter["project"] = project_name
        if session_id:
            metadata_filter["session_id"] = session_id
        if tags:
            metadata_filter["tags"] = tags

        query_args = {
            "query_embeddings": [embedding],
            "n_results": top_k
        }

        if metadata_filter:
            if len(metadata_filter) == 1:
                # Single field: safe to pass directly
                query_args["where"] = metadata_filter
            else:
                # Multiple fields: combine under $and
                # e.g. { "$and": [ {"project": "X"}, {"session_id": "Y"} ] }
                query_args["where"] = {
                    "$and": [{k: v} for k, v in metadata_filter.items()]
                }

        results = self.collection.query(**query_args)
        return results["documents"]

    def clear_memory(self):
        self.collection.delete()
