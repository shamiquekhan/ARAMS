from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class DocumentChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_document(self, text: str, metadata: dict) -> List[Document]:
        chunks = self.splitter.split_text(text)
        return [
            Document(page_content=c, metadata={**metadata, "chunk_index": i})
            for i, c in enumerate(chunks)
        ]
