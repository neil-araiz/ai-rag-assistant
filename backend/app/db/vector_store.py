from google import genai
from google.genai import types
from supabase import create_client, Client
from app.core.config import get_settings
from typing import List, Dict, Optional

settings = get_settings()


class VectorStore:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

        self.supabase_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

        self.embedding_dim = 768

    def generate_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding using Gemini.

        task_type:
        - RETRIEVAL_DOCUMENT (for chunks)
        - RETRIEVAL_QUERY (for search queries)
        """
        result = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self.embedding_dim
            )
        )

        return result.embeddings[0].values

    def store_chunk(
        self,
        document_id: int,
        content: str,
        embedding: List[float],
        metadata: Dict
    ):
        data = {
            "document_id": document_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }

        response = self.supabase_client.table("document_chunks").insert(data).execute()
        return response.data

    def delete_document_chunks(self, document_id: int):
        """
        Delete all chunks associated with a document_id.
        """
        response = self.supabase_client.table("document_chunks") \
            .delete() \
            .eq("document_id", document_id) \
            .execute()
        return response.data

    def similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[int] = None,
        limit: int = 5
    ):
        """
        Calls Postgres RPC: match_document_chunks
        """
        params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.6,
            "match_count": limit,
        }

        if document_id:
            params["filter_document_id"] = document_id

        response = self.supabase_client.rpc(
            "match_document_chunks",
            params
        ).execute()

        return response.data