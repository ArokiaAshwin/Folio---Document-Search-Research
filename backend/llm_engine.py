import os
import logging
from typing import List, Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a knowledgeable research and document analysis assistant.
Your job is to provide clear, direct, and factual answers based strictly on the uploaded documents provided to you.

Style and tone:
- Professional, objective, and concise. Avoid fluff, filler phrases, or robotic boilerplate.
- Cite specific document references naturally inline, e.g., (source: filename.pdf, p. 3).
- If the documents do not contain the answer, simply state that the information isn't available in the provided files.
- Format responses cleanly with readable paragraphs, bullet points when listing items, and code/tables where appropriate.
"""

def build_context_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    context_sections = []
    for idx, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        fname = meta.get("filename", "Document")
        page = meta.get("page_number", 1)
        text = chunk.get("text", "").strip()
        context_sections.append(f"[{idx}] Source: {fname} (Page {page})\n{text}")

    context_str = "\n\n".join(context_sections)
    return f"""Context from uploaded files:
{context_str}

User Question:
{query}

Please answer the question accurately using the context above. Cite sources with [1], [2], etc., or inline references."""

class LLMEngine:
    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {
                "answer": "No relevant passages were found in your uploaded files matching this query.",
                "provider": "local",
                "model": "search",
                "citations": []
            }

        citations = []
        for c in retrieved_chunks:
            meta = c.get("metadata", {})
            citations.append({
                "chunk_id": c.get("chunk_id"),
                "filename": meta.get("filename"),
                "page_number": meta.get("page_number"),
                "similarity_score": c.get("similarity_score"),
                "snippet": c.get("text", "")[:280] + ("..." if len(c.get("text", "")) > 280 else "")
            })

        active_provider = provider or settings.get("DEFAULT_LLM_PROVIDER", "gemini")
        user_key = api_key or (settings.get("GEMINI_API_KEY") if active_provider == "gemini" else settings.get("OPENAI_API_KEY"))

        # 1. Google Gemini
        if active_provider == "gemini" and user_key:
            try:
                from google import genai
                client = genai.Client(api_key=user_key)
                selected_model = model_name or settings.get("DEFAULT_MODEL", "gemini-2.0-flash")
                
                full_prompt = f"{SYSTEM_PROMPT}\n\n{build_context_prompt(query, retrieved_chunks)}"
                response = client.models.generate_content(
                    model=selected_model,
                    contents=full_prompt
                )
                return {
                    "answer": response.text,
                    "provider": "gemini",
                    "model": selected_model,
                    "citations": citations
                }
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Using local synthesis.")

        # 2. OpenAI
        if active_provider == "openai" and user_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=user_key)
                selected_model = model_name or "gpt-4o-mini"
                
                prompt = build_context_prompt(query, retrieved_chunks)
                completion = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                return {
                    "answer": completion.choices[0].message.content,
                    "provider": "openai",
                    "model": selected_model,
                    "citations": citations
                }
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Using local synthesis.")

        # 3. Clean Natural Local Extraction
        return self._format_local_response(retrieved_chunks, citations)

    def _format_local_response(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Formats retrieved passages into clean, human-readable findings without AI cliché banners.
        """
        top_chunks = retrieved_chunks[:3]
        lines = ["Here is what was found in the indexed documents regarding your question:\n"]

        for i, chunk in enumerate(top_chunks, 1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("filename", "Document")
            page_num = meta.get("page_number", 1)
            text = chunk.get("text", "").strip()

            lines.append(f"**From `{doc_name}` (Page {page_num}):**")
            lines.append(f"> {text}\n")

        lines.append(
            "*Note: To generate fully written conversational summaries, connect a Gemini or OpenAI API key in Settings.*"
        )

        return {
            "answer": "\n".join(lines),
            "provider": "local",
            "model": "vector-search",
            "citations": citations
        }

llm_engine = LLMEngine()
