import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.models.document import Document
from app.services.pdf_service import PDFService
from app.db.vector_store import VectorStore
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

async def process_pdf(document_id: int, file_path: str):
    db = SessionLocal()
    pdf_service = PDFService()
    vector_store = VectorStore()
    
    try:
        # 1. Extract Text with Layout Awareness
        pages_content = pdf_service.extract_text_with_layout(file_path)
        
        # 2. Hierarchical Chunking (Parent-Child)
        chunks = pdf_service.chunk_hierarchical(pages_content)
        
        # 3. Batch Embedding (20 texts per API call with rate limiting)
        texts = [chunk["content"] for chunk in chunks]
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = vector_store.generate_embeddings_batch(texts)

        # 4. Store all chunks in a single DB connection
        prepared_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            prepared_chunks.append({
                "content": chunk["content"],
                "embedding": embedding,
                "metadata": chunk["metadata"]
            })
        
        vector_store.store_chunks_batch(document_id, prepared_chunks)
        
        # 4. Save full joined content to Document model
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            # Reconstruct full text from elements per page
            page_texts = []
            for p in pages_content:
                parts = [elem[2] for elem in p["elements"]]
                page_texts.append("\n\n".join(parts))
            db_doc.content = "\n\n---\n\n".join(page_texts)
            db.commit()
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise e # Re-raise to ensure the endpoint can handle the error
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save to temp file for processing
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Create Document record
        db_doc = Document(
            filename=file.filename
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        # 2. Wait for processing (synchronous/awaited)
        await process_pdf(db_doc.id, temp_file_path)

        return {
            "document_id": db_doc.id,
            "filename": file.filename,
            "message": "Upload and indexing complete."
        }
    except Exception as e:
        # If processing fails, we might want to clean up the DB record
        # but for now we just return the error
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.delete("/{document_id}")
async def delete_file(
    document_id: int,
    db: Session = Depends(get_db)
):
    # 1. Delete from Vector Store
    vector_store = VectorStore()
    vector_store.delete_document_chunks(document_id)

    # 2. Delete from DB
    db_doc = db.query(Document).filter(Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(db_doc)
    db.commit()

    return {"message": "Document and its chunks deleted successfully"}
