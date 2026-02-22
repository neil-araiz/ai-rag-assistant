from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.db.database import engine, Base
from app.models.document import Document

# Initialize database schema
Base.metadata.create_all(bind=engine)

from app.routes import chat, upload, sample

app = FastAPI(title="RAG AI Assistant Backend")

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(sample.router, prefix="/sample", tags=["sample"])

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}
