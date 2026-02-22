from fastapi import APIRouter

router = APIRouter()

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

class ChatRequest(BaseModel):
    message: str
    document_id: Optional[int] = None

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    try:
        result = await rag_service.get_answer(request.message, document_id=request.document_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
