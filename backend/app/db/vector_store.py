import os
import psycopg2
from google import genai
from google.genai import types
from app.core.config import get_settings
from typing import List, Dict, Optional
import json

settings = get_settings()

class VectorStore:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.database_url = settings.DATABASE_URL
        self.embedding_dim = 768

    def _get_connection(self):
        return psycopg2.connect(self.database_url)

    def generate_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
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
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                cur.execute("""
                    ALTER TABLE document_chunks 
                    ADD COLUMN IF NOT EXISTS embedding vector(%s);
                """, (self.embedding_dim,))
                
                cur.execute("""
                    INSERT INTO document_chunks (document_id, content, embedding, metadata_json)
                    VALUES (%s, %s, %s, %s)
                """, (document_id, content, embedding, json.dumps(metadata)))
                conn.commit()
        finally:
            conn.close()

    def delete_document_chunks(self, document_id: int):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
                conn.commit()
        finally:
            conn.close()

    def similarity_search(
        self,
        query_embedding: List[float],
        document_id: Optional[int] = None,
        limit: int = 5
    ):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = """
                    SELECT content, metadata_json, 1 - (embedding <=> %s::vector) as similarity
                    FROM document_chunks
                """
                params = [query_embedding]
                
                if document_id:
                    sql += " WHERE document_id = %s"
                    params.append(document_id)
                
                sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.extend([query_embedding, limit])
                
                cur.execute(sql, tuple(params))
                results = []
                for row in cur.fetchall():
                    results.append({
                        "content": row[0],
                        "metadata": json.loads(row[1]) if row[1] else {},
                        "similarity": row[2]
                    })
                return results
        finally:
            conn.close()
