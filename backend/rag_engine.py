import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings
from backend.document_processor import DocumentChunk

class RAGEngine:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = "qa_document_embeddings"
        self._init_collection()

    def _init_collection(self):
        # By default, Chroma uses all-MiniLM-L6-v2 ONNX embedding function locally
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AI Document Q&A Document Chunks and Embeddings"}
        )

    def add_document_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Adds parsed document chunks into ChromaDB collection.
        """
        if not chunks:
            return 0

        ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Batch upsert into ChromaDB in batches of 100
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            self.collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
        return len(chunks)

    def query_similar_chunks(
        self,
        query: str,
        n_results: int = 4,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the top-k most relevant chunks using semantic similarity search.
        """
        where_clause = None
        if document_id:
            where_clause = {"document_id": document_id}

        total_count = self.collection.count()
        if total_count == 0:
            return []

        actual_n = min(n_results, total_count)

        query_args = {
            "query_texts": [query],
            "n_results": actual_n
        }
        if where_clause:
            query_args["where"] = where_clause

        results = self.collection.query(**query_args)
        
        retrieved = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc_text, meta, dist, chunk_id in zip(docs, metas, distances, ids):
                # Calculate normalized similarity score from cosine/L2 distance
                similarity_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                retrieved.append({
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "metadata": meta,
                    "distance": float(dist),
                    "similarity_score": round(similarity_score, 4)
                })

        # Sort by highest similarity score
        retrieved.sort(key=lambda x: x["similarity_score"], reverse=True)
        return retrieved

    def delete_document_chunks(self, document_id: str) -> int:
        """
        Deletes all chunks belonging to a specific document ID.
        """
        try:
            self.collection.delete(where={"document_id": document_id})
            return 1
        except Exception:
            return 0

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Gets all stored chunks for a given document.
        """
        results = self.collection.get(where={"document_id": document_id})
        chunks = []
        if results and results.get("documents"):
            for doc_text, meta, chunk_id in zip(
                results["documents"], results["metadatas"], results["ids"]
            ):
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": doc_text,
                    "metadata": meta
                })
        chunks.sort(key=lambda x: x["metadata"].get("chunk_index", 0))
        return chunks

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns collection stats.
        """
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }

rag_engine = RAGEngine()
