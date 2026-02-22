from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from app.db.database import get_db

router = APIRouter()

@router.get("/docs-count")
async def docs_count(db: Prisma = Depends(get_db)):
    try:
        count = await db.document.count()
        return {"documents_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/db-check")
async def db_check(db: Prisma = Depends(get_db)):
    try:
        # Prisma doesn't have a direct 'execute text' like this for simple checks, 
        # but we can try to query a table or just check connection.
        # Alternatively, use db.query_raw if needed.
        await db.query_raw('SELECT 1')
        return {"status": "success", "message": "Database connection is working"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
