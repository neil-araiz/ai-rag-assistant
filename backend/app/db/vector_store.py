import os
import psycopg2
import time
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

    def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 20
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        Processes `batch_size` texts per API call with rate limiting.
        Automatically retries on 429 (quota exceeded) errors.
        """
        all_embeddings = []
        total_batches = (len(texts) - 1) // batch_size + 1

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")

            # Retry loop for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                        config=types.EmbedContentConfig(
                            task_type=task_type,
                            output_dimensionality=self.embedding_dim
                        )
                    )
                    for emb in result.embeddings:
                        all_embeddings.append(emb.values)
                    break  # Success — exit retry loop
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        # Extract retry delay from error or default to 60s
                        import re
                        delay_match = re.search(r"retryDelay.*?(\d+)", error_str)
                        wait_time = int(delay_match.group(1)) + 5 if delay_match else 60
                        print(f"  Rate limited! Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        raise  # Non-rate-limit error, propagate

            # Small delay between successful batches to stay under quota
            if i + batch_size < len(texts):
                time.sleep(2)

        return all_embeddings

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

    def store_chunks_batch(
        self,
        document_id: int,
        chunks: List[Dict]
    ):
        """
        Store multiple chunks using a SINGLE database connection.
        Each chunk dict must have: content, embedding, metadata.
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute("""
                    ALTER TABLE document_chunks 
                    ADD COLUMN IF NOT EXISTS embedding vector(%s);
                """, (self.embedding_dim,))

                for chunk in chunks:
                    cur.execute("""
                        INSERT INTO document_chunks (document_id, content, embedding, metadata_json)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        document_id,
                        chunk["content"],
                        chunk["embedding"],
                        json.dumps(chunk["metadata"])
                    ))
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
