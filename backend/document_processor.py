import re
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument

class DocumentChunk:
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def to_dict(self):
        return {
            "text": self.text,
            "metadata": self.metadata
        }

class DocumentProcessor:
    @staticmethod
    def extract_text_from_file(file_path: str, filename: str) -> List[Dict[str, Any]]:
        """
        Extracts pages/sections with text from PDF, DOCX, TXT, or MD files.
        Returns list of dicts: [{"page": int, "text": str}]
        """
        ext = Path(filename).suffix.lower()
        pages = []

        if ext == ".pdf":
            try:
                reader = PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    extracted = page.extract_text() or ""
                    clean_text = extracted.strip()
                    if clean_text:
                        pages.append({"page": idx + 1, "text": clean_text})
            except Exception as e:
                raise ValueError(f"Failed to parse PDF document '{filename}': {str(e)}")

        elif ext in [".docx", ".doc"]:
            try:
                doc = DocxDocument(file_path)
                full_text_list = []
                for p in doc.paragraphs:
                    if p.text.strip():
                        full_text_list.append(p.text.strip())
                # Group paragraphs into page-like chunks (~500 words per section)
                section_text = "\n\n".join(full_text_list)
                pages.append({"page": 1, "text": section_text})
            except Exception as e:
                raise ValueError(f"Failed to parse DOCX document '{filename}': {str(e)}")

        elif ext in [".txt", ".md", ".csv", ".json", ".log"]:
            try:
                encodings = ["utf-8", "latin-1", "cp1252"]
                content = ""
                for enc in encodings:
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                if content.strip():
                    pages.append({"page": 1, "text": content.strip()})
            except Exception as e:
                raise ValueError(f"Failed to read text file '{filename}': {str(e)}")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: PDF, DOCX, TXT, MD, CSV, JSON")

        if not pages:
            raise ValueError(f"Document '{filename}' appears to be empty or contains no extractable text.")

        return pages

    @staticmethod
    def recursive_split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Splits text recursively using paragraphs, sentences, and words.
        """
        if len(text) <= chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]

        def _split_text(text_to_split: str, sep_idx: int) -> List[str]:
            if len(text_to_split) <= chunk_size or sep_idx >= len(separators):
                if len(text_to_split) > chunk_size:
                    step = max(1, chunk_size - chunk_overlap)
                    return [text_to_split[i:i + chunk_size] for i in range(0, len(text_to_split), step)]
                return [text_to_split]

            sep = separators[sep_idx]
            splits = text_to_split.split(sep) if sep != "" else list(text_to_split)

            if len(splits) <= 1:
                return _split_text(text_to_split, sep_idx + 1)

            chunks = []
            current_chunk = []
            current_len = 0

            for piece in splits:
                piece_len = len(piece) + (len(sep) if current_chunk else 0)
                if current_len + piece_len > chunk_size and current_chunk:
                    joined = sep.join(current_chunk).strip()
                    if joined:
                        chunks.append(joined)

                    overlap_items = []
                    overlap_len = 0
                    for prev in reversed(current_chunk):
                        p_len = len(prev) + len(sep)
                        if overlap_len + p_len <= chunk_overlap:
                            overlap_items.insert(0, prev)
                            overlap_len += p_len
                        else:
                            break
                    current_chunk = overlap_items
                    current_len = overlap_len

                current_chunk.append(piece)
                current_len += len(piece) + (len(sep) if len(current_chunk) > 1 else 0)

            if current_chunk:
                joined = sep.join(current_chunk).strip()
                if joined:
                    chunks.append(joined)

            final_chunks = []
            for ch in chunks:
                if len(ch) > chunk_size and sep_idx + 1 < len(separators):
                    final_chunks.extend(_split_text(ch, sep_idx + 1))
                else:
                    final_chunks.append(ch)

            return final_chunks

        return _split_text(text, 0)

    @classmethod
    def process_document(
        cls,
        file_path: str,
        filename: str,
        document_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[DocumentChunk]:
        """
        Processes document into chunks with complete RAG metadata.
        """
        pages = cls.extract_text_from_file(file_path, filename)
        all_chunks: List[DocumentChunk] = []
        chunk_counter = 0

        for p in pages:
            page_num = p["page"]
            page_text = p["text"]
            text_splits = cls.recursive_split_text(page_text, chunk_size, chunk_overlap)

            for split_idx, split_text in enumerate(text_splits):
                cleaned = split_text.strip()
                if not cleaned:
                    continue
                
                chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                chunk_metadata = {
                    "document_id": str(document_id),
                    "filename": str(filename),
                    "page_number": int(page_num),
                    "chunk_index": int(chunk_counter),
                    "chunk_id": chunk_id,
                    "char_count": len(cleaned),
                    "file_ext": Path(filename).suffix.lower()
                }
                all_chunks.append(DocumentChunk(text=cleaned, metadata=chunk_metadata))
                chunk_counter += 1

        return all_chunks
