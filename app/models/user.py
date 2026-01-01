from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20))  # admin | manager | employee
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
