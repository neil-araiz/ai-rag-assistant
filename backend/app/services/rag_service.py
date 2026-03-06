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
        Upgraded RAG Flow:
        1. Embed query
        2. Retrieve similar CHILD chunks
        3. Fetch unique PARENT contexts
        4. RE-RANK parents using LLM
        5. Generate final grounded answer
        """

        # 1. Query embedding
        query_embedding = self.vector_store.generate_embedding(
            query,
            task_type="RETRIEVAL_QUERY"
        )

        # 2. Similarity search for CHILD chunks (get more for re-ranking)
        relevant_children = self.vector_store.similarity_search(
            query_embedding,
            document_id=document_id,
            limit=15 # Get more candidates for re-ranking
        )

        if not relevant_children:
            return {"answer": "I don't know based on the document.", "citations": []}

        # 3. Map to Parent Contexts
        parents_map = {} # parent_id -> metadata
        for child in relevant_children:
            meta = child.get("metadata", {}) or {}
            parent_id = meta.get("parent_id")
            parent_content = meta.get("parent_content")
            
            if parent_id and parent_id not in parents_map:
                parents_map[parent_id] = {
                    "content": parent_content,
                    "page_number": meta.get("page_number", "unknown"),
                    "similarity": child["similarity"]
                }

        # 4. Re-ranking Step
        ranked_parents = await self.re_rank_chunks(query, list(parents_map.values()))
        
        # Take top 5 after re-ranking
        top_contexts = ranked_parents[:5]

        # 5. Build context for final prompt
        context_parts = []
        raw_citations = []
        for i, ctx in enumerate(top_contexts):
            context_parts.append(f"CONTEXT [{i}]: (Page {ctx['page_number']})\n{ctx['content']}")
            raw_citations.append({
                "index": i,
                "page_number": ctx["page_number"],
                "snippet": ctx["content"][:200] + "..."
            })

        context_text = "\n\n".join(context_parts)

        # 6. Final Prompt
        system_instruction = (
            "You are a helpful AI assistant.\n"
            "Answer the question using ONLY the provided context.\n"
            "If the answer is not in the context, say:\n"
            "'I don't know based on the document.'\n"
            "Always include page numbers in your text when possible.\n\n"
            "IMPORTANT: At the very end, list the context indices used: SOURCES: [0, 2]"
        )

        prompt = f"{system_instruction}\n\nContext:\n{context_text}\n\nQuestion: {query}"

        # 7. Generate final response
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text if response.text else "No response generated."

        # 8. Parse Citations (existing logic)
        source_match = re.search(r"SOURCES:\s*\[(.*?)\]", answer)
        final_citations = []
        
        if source_match:
            try:
                indices_str = source_match.group(1)
                if indices_str.strip():
                    cited_indices = [int(i.strip()) for i in indices_str.split(",")]
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
                answer = re.sub(r"SOURCES:\s*\[.*?\]", "", answer).strip()
            except:
                pass

        return {"answer": answer, "citations": final_citations}

    async def re_rank_chunks(self, query: str, chunks: List[Dict]) -> List[Dict]:
        """
        Uses Gemini to score chunks by relevance to the query.
        """
        if len(chunks) <= 1:
            return chunks

        # Prepare ranking prompt
        chunks_text = ""
        for i, c in enumerate(chunks):
            chunks_text += f"---\nID: {i}\n{c['content'][:500]}\n"

        ranking_prompt = f"""
Evaluate the relevance of the following document chunks to the user query.
Query: "{query}"

For each ID, provide a relevance score from 0 to 10 (10 being most relevant).
Format: [ID]: [SCORE]

{chunks_text}
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=ranking_prompt
            )
            
            # Simple parsing of scores
            scores = {}
            for line in response.text.split("\n"):
                match = re.search(r"\[(\d+)\]:\s*([\d\.]+)", line)
                if match:
                    idx = int(match.group(1))
                    score = float(match.group(2))
                    scores[idx] = score

            # Sort chunks by scored relevance
            scored_chunks = []
            for i, chunk in enumerate(chunks):
                # Fallback to vector similarity if scoring failed for a chunk
                score = scores.get(i, chunk.get("similarity", 0) * 10)
                chunk["relevance_score"] = score
                scored_chunks.append(chunk)

            return sorted(scored_chunks, key=lambda x: x["relevance_score"], reverse=True)
        except Exception as e:
            print(f"Re-ranking failed: {e}")
            return chunks # Fallback to original order
