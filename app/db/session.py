from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# If DATABASE_URL is empty, we still let the app boot (API health works).
# DB features will be disabled until you set DATABASE_URL.
engine = None
SessionLocal = None

if settings.DATABASE_URL:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if SessionLocal is None:
        # DB not configured yet
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
