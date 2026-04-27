from sqlalchemy import text

from sqlalchemy.orm import Session

def check_db_connection(db: Session) -> bool:

    db.execute(text("SELECT 1"))

    return True