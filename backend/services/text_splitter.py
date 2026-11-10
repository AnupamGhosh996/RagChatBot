import uuid
from typing import List, Dict, Any

class DocumentChunk:
    """Represents a discrete text chunk with associated page & document metadata."""
    def __init__(
        self,
        chunk_id: str,
        text: str,
        document_id: str,
        document_name: str,
        page_number: int,
        chunk_index: int,
        start_char: int = 0,
        end_char: int = 0
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.document_id = document_id
        self.document_name = document_name
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.start_char = start_char
        self.end_char = end_char

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        return cls(
            chunk_id=data["chunk_id"],
            text=data["text"],
            document_id=data["document_id"],
            document_name=data["document_name"],
            page_number=data["page_number"],
            chunk_index=data.get("chunk_index", 0),
            start_char=data.get("start_char", 0),
            end_char=data.get("end_char", 0)
        )


class TextSplitterService:
    """
    Splits document page texts into overlapping chunks using
    LangChain's RecursiveCharacterTextSplitter (with built-in fallback).
    Guarantees page number preservation for citations.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = self._init_splitter()

    def _init_splitter(self):
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""],
                length_function=len,
                is_separator_regex=False
            )
        except ImportError:
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                return RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""],
                    length_function=len
                )
            except ImportError:
                return None

    def _fallback_split_text(self, text: str) -> List[str]:
        """Custom pure-Python recursive text splitter if LangChain is unavailable."""
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", " "]
        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                chunks = []
                current_chunk = ""
                for part in parts:
                    candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
                    if len(candidate) <= self.chunk_size:
                        current_chunk = candidate
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        # Overlap: keep the tail of the current chunk
                        tail = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                        current_chunk = f"{tail}{sep}{part}" if tail else part
                if current_chunk:
                    chunks.append(current_chunk)
                return chunks

        # Fallback to hard character slicing if no separator found
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def split_document(
        self,
        document_id: str,
        document_name: str,
        pages: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Processes each page independently so that chunks strictly retain their
        originating page number and document metadata.
        """
        all_chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"].strip()
            if not page_text:
                continue

            if self._splitter is not None:
                text_splits = self._splitter.split_text(page_text)
            else:
                text_splits = self._fallback_split_text(page_text)

            char_offset = 0
            for idx, split in enumerate(text_splits):
                cleaned_split = split.strip()
                if not cleaned_split:
                    continue

                chunk_id = f"{document_id}_p{page_num}_c{idx}"
                start_char = page_text.find(cleaned_split, char_offset)
                if start_char == -1:
                    start_char = char_offset
                end_char = start_char + len(cleaned_split)
                char_offset = max(start_char, 0)

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    text=cleaned_split,
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page_num,
                    chunk_index=global_chunk_idx,
                    start_char=start_char,
                    end_char=end_char
                )
                all_chunks.append(chunk)
                global_chunk_idx += 1

        return all_chunks

text_splitter_service = TextSplitterService()
