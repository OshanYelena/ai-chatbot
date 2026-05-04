from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException


def check_db_connection(db: Session) -> None:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Database connection failed") from exc
