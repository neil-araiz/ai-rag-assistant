from fastapi import APIRouter, UploadFile, File

router = APIRouter()

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

async def process_pdf_background(document_id: int, file_path: str):
    db = SessionLocal()
    pdf_service = PDFService()
    vector_store = VectorStore()
    
    try:
        # 1. Extract Text
        pages_content = pdf_service.extract_text_with_pages(file_path)
        
        # 2. Chunking
        chunks = pdf_service.chunk_content(pages_content)
        
        # 3. Embedding and Storage
        for chunk in chunks:
            embedding = vector_store.generate_embedding(chunk["content"])
            vector_store.store_chunk(
                document_id=document_id,
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk["metadata"]
            )
        
        # 4. Save full content
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db_doc.content = "\n".join([p["content"] for p in pages_content])
            db.commit()
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
    finally:
        db.close() # Always close the session
        # Optionally delete temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save to temp file for processing
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Create Document record
    db_doc = Document(
        filename=file.filename
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 2. Trigger background processing
    background_tasks.add_task(process_pdf_background, db_doc.id, temp_file_path)

    return {
        "document_id": db_doc.id,
        "filename": file.filename,
        "message": "Upload successful, processing started."
    }

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
