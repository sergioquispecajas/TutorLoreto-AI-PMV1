import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError("Falta DATABASE_URL en .env")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine
