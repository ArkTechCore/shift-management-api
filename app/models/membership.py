import uuid
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StoreMembership(Base):
    __tablename__ = "store_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )

    # membership role inside that store: "manager" or "employee"
    store_role: Mapped[str] = mapped_column(String(20), nullable=False, default="employee")

    # store-specific pay rate (because same employee can work multiple stores)
    pay_rate: Mapped[str] = mapped_column(String(20), nullable=False, default="0")

    # disable membership without deleting history
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
