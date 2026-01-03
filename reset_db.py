from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    conn.commit()

print("✅ Dropped + recreated public schema (clean slate)")
