import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool  # <-- For transaction pooler
from dotenv import load_dotenv

# -------------------------
# Setup logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()
USER = os.getenv("USER") or os.getenv("user")
PASSWORD = os.getenv("PASSWORD") or os.getenv("password")
HOST = os.getenv("HOST") or os.getenv("host")
PORT = os.getenv("PORT") or os.getenv("port")
DBNAME = os.getenv("DBNAME") or os.getenv("dbname")

if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
    raise ValueError("One or more database environment variables are missing in .env")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
try:
    engine = create_engine(DATABASE_URL, poolclass=NullPool, pool_pre_ping=True)
    with engine.connect() as conn:
        logger.info("✅ Database connection successful")
except OperationalError as e:
    logger.error(f"❌ Database connection failed: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# -------------------------
def get_db():
    """
    Provides a SQLAlchemy session to FastAPI routes.
    Use with Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
