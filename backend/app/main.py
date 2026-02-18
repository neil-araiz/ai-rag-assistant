from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your routes
from app.routes import chat, upload

app = FastAPI(title="RAG AI Assistant Backend")

# Allow frontend to access backend
origins = ["http://localhost:3000"]  # your Next.js frontend URL

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}
