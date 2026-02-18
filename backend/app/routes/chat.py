from fastapi import APIRouter

router = APIRouter()

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    # Dummy response
    return {"response": f"You said: {request.message}"}
