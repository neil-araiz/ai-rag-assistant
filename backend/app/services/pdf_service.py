import fitz  # PyMuPDF
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def extract_text_with_pages(self, file_path: str) -> List[Dict]:
        """
        Extracts text from a PDF file and returns a list of dictionaries
        containing page number and text content.
        """
        doc = fitz.open(file_path)
        pages_content = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            pages_content.append({
                "page_number": page_num + 1,
                "content": text
            })
        doc.close()
        return pages_content

    def chunk_content(self, pages_content: List[Dict]) -> List[Dict]:
        """
        Chunks the extracted text while preserving page numbers.
        """
        chunks = []
        for page in pages_content:
            page_text = page["content"]
            page_number = page["page_number"]
            
            # Split page text into chunks
            page_chunks = self.text_splitter.split_text(page_text)
            
            for i, chunk_text in enumerate(page_chunks):
                chunks.append({
                    "content": chunk_text,
                    "metadata": {
                        "page_number": page_number,
                        "chunk_index": i
                    }
                })
        return chunks
