import os
import unittest
from backend.document_processor import DocumentProcessor
from backend.rag_engine import RAGEngine
from backend.auth import hash_password, verify_password, create_access_token, decode_access_token

class TestDocumentQA(unittest.TestCase):
    def test_password_hashing(self):
        pwd = "SecretPassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token(self):
        payload = {"sub": "user_123", "username": "alex"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user_123")
        self.assertEqual(decoded["username"], "alex")

    def test_recursive_split_text(self):
        text = "This is sentence one. " * 50
        chunks = DocumentProcessor.recursive_split_text(text, chunk_size=200, chunk_overlap=50)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 250)

    def test_rag_pipeline(self):
        # Create temporary test text file
        test_file = "test_sample.txt"
        test_content = (
            "Retrieval-Augmented Generation (RAG) is an AI framework for retrieving facts from an external knowledge base. "
            "It enriches the context for large language models to generate accurate answers with verifiable citations. "
            "ChromaDB is an open-source embedding database designed to store vector embeddings for fast nearest neighbor search."
        )
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        try:
            chunks = DocumentProcessor.process_document(
                file_path=test_file,
                filename="test_sample.txt",
                document_id="doc_test_1",
                chunk_size=150,
                chunk_overlap=30
            )
            self.assertGreater(len(chunks), 0)
            self.assertEqual(chunks[0].metadata["document_id"], "doc_test_1")

            test_rag = RAGEngine(persist_directory="./test_chroma_db")
            added = test_rag.add_document_chunks(chunks)
            self.assertEqual(added, len(chunks))

            # Query
            results = test_rag.query_similar_chunks(query="What is ChromaDB?", n_results=2)
            self.assertGreater(len(results), 0)
            self.assertIn("ChromaDB", results[0]["text"])

            # Clean up
            test_rag.delete_document_chunks("doc_test_1")
            remaining = test_rag.get_document_chunks("doc_test_1")
            self.assertEqual(len(remaining), 0)

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
            import shutil
            if os.path.exists("./test_chroma_db"):
                shutil.rmtree("./test_chroma_db", ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
