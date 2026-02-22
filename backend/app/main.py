from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

from app.db.database import db
from app.routes import chat, upload, sample

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    try:
        print("🚀 Connecting to database...")
        await db.connect()
        print("✅ Database connected successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise e
    yield
    # Disconnect from database
    await db.disconnect()
    print("💤 Database disconnected")

app = FastAPI(title="RAG AI Assistant Backend", lifespan=lifespan)

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
