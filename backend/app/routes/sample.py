from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.db.database import get_db
from app.models.document import Document

router = APIRouter()

@router.get("/docs-count")
def docs_count(db: Session = Depends(get_db)):
    try:
        count = db.query(Document).count()
        return {"documents_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database connection is working"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
