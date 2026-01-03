from sqlalchemy import create_engine, text
from app.core.config import settings

TARGET = "19197c8421dc"  # your current head (you showed this)

engine = create_engine(settings.DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("UPDATE alembic_version SET version_num = :v"), {"v": TARGET})

print(f"alembic_version fixed -> {TARGET}")
