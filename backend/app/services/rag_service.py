from google import genai
from app.db.vector_store import VectorStore
from app.core.config import get_settings
from typing import Dict, List
import re

settings = get_settings()


class RAGService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.vector_store = VectorStore()

    async def get_answer(self, query: str, document_id: int = None) -> Dict:
        """
        RAG Flow:
        1. Embed query
        2. Retrieve similar chunks
        3. Build context
        4. Generate answer
        """

        # 1. Query embedding
        query_embedding = self.vector_store.generate_embedding(
            query,
            task_type="RETRIEVAL_QUERY"
        )

        # 2. Similarity search
        relevant_chunks = self.vector_store.similarity_search(
            query_embedding,
            document_id=document_id,
            limit=5
        )

        # 3. Build context + raw citations
        context_parts: List[str] = []
        raw_citations: List[Dict] = []

        for i, chunk in enumerate(relevant_chunks):
            content = chunk["content"]
            metadata = chunk.get("metadata", {}) or {}
            page_number = metadata.get("page_number", "unknown")

            context_parts.append(f"CHUNK [{i}]: (Page {page_number})\n{content}")

            raw_citations.append({
                "index": i,
                "page_number": page_number,
                "snippet": content[:200] + "..."
            })

        context_text = "\n\n".join(context_parts)

        # 4. Prompt
        system_instruction = (
            "You are a helpful AI assistant.\n"
            "Answer the question using ONLY the provided context.\n"
            "If the answer is not in the context, say:\n"
            "'I don't know based on the document.'\n"
            "Always include page numbers in your text when possible.\n\n"
            "IMPORTANT: At the very end of your response, list the chunk indices you actually used in this exact format: SOURCES: [0, 2]"
        )

        prompt = f"""
{system_instruction}

Context:
{context_text}

Question: {query}
"""

        # 5. Generate response
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text if response.text else "No response generated."

        # 6. Parse Citations
        source_match = re.search(r"SOURCES:\s*\[(.*?)\]", answer)
        final_citations = []
        
        if source_match:
            try:
                indices_str = source_match.group(1)
                if indices_str.strip():
                    cited_indices = [int(i.strip()) for i in indices_str.split(",")]
                    
                    # Filter and de-duplicate by page number
                    seen_pages = set()
                    for idx in cited_indices:
                        for chunk_cite in raw_citations:
                            if chunk_cite["index"] == idx:
                                page = chunk_cite["page_number"]
                                if page not in seen_pages:
                                    final_citations.append({
                                        "page_number": page,
                                        "snippet": chunk_cite["snippet"]
                                    })
                                    seen_pages.add(page)
                
                # Clean up answer by removing the internal tag
                answer = re.sub(r"SOURCES:\s*\[.*?\]", "", answer).strip()
            except Exception as e:
                print(f"Error parsing citations: {e}")
                final_citations = []
        else:
            final_citations = []

        return {
            "answer": answer,
            "citations": final_citations
        }