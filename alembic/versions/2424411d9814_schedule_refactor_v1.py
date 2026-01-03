"""schedule refactor v1

Revision ID: 2424411d9814
Revises: 19197c8421dc
Create Date: 2026-01-02 04:21:09.815974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2424411d9814"
down_revision: Union[str, Sequence[str], None] = "19197c8421dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Create weeks
    op.create_table(
        "weeks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_start"),
    )

    # 2) Create schedules (IMPORTANT: unique constraint name must NOT be uq_store_week)
    op.create_table(
        "schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("store_id", sa.UUID(), nullable=False),
        sa.Column("week_id", sa.UUID(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "week_id", name="uq_schedules_store_week"),
    )

    # 3) Create shift_assignments
    op.create_table(
        "shift_assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("shift_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4) Update shifts table safely (defaults are critical if rows already exist)
    op.add_column("shifts", sa.Column("headcount_required", sa.Integer(), nullable=False, server_default=sa.text("1")))
    op.add_column("shifts", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # 5) Drop FK from shifts -> week_schedules FIRST (dependency blocker)
    op.execute("ALTER TABLE shifts DROP CONSTRAINT IF EXISTS shifts_schedule_id_fkey;")
    op.execute("ALTER TABLE shifts DROP CONSTRAINT IF EXISTS shifts_store_id_fkey;")
    op.execute("ALTER TABLE shifts DROP CONSTRAINT IF EXISTS shifts_user_id_fkey;")

    # 6) Drop UNIQUE constraint on week_schedules (this also removes the index behind it)
    op.execute("ALTER TABLE week_schedules DROP CONSTRAINT IF EXISTS uq_store_week;")

    # 7) Now it is safe to drop old week_schedules table
    op.execute("DROP TABLE IF EXISTS week_schedules;")

    # 8) Recreate FK shifts.schedule_id -> schedules.id
    # (Your shifts.schedule_id column stays the same name, just points to schedules now)
    op.create_foreign_key(
        "shifts_schedule_id_fkey",
        "shifts",
        "schedules",
        ["schedule_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 9) Remove old shift columns (if they exist)
    # Use raw SQL with IF EXISTS to avoid crashing if already removed
    op.execute("ALTER TABLE shifts DROP COLUMN IF EXISTS status;")
    op.execute("ALTER TABLE shifts DROP COLUMN IF EXISTS user_id;")
    op.execute("ALTER TABLE shifts DROP COLUMN IF EXISTS store_id;")

    # 10) Remove server defaults we added (optional but cleaner)
    op.alter_column("shifts", "headcount_required", server_default=None)
    op.alter_column("shifts", "created_at", server_default=None)


def downgrade() -> None:
    # Downgrade is messy for this refactor; keep it minimal/safe.

    # Re-add old columns on shifts
    op.add_column("shifts", sa.Column("store_id", sa.UUID(), nullable=True))
    op.add_column("shifts", sa.Column("user_id", sa.UUID(), nullable=True))
    op.add_column("shifts", sa.Column("status", sa.VARCHAR(length=20), nullable=True))

    # Drop new FK shifts -> schedules
    op.execute("ALTER TABLE shifts DROP CONSTRAINT IF EXISTS shifts_schedule_id_fkey;")

    # Recreate week_schedules
    op.create_table(
        "week_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("store_id", sa.UUID(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.VARCHAR(length=20), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("locked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "week_start", name="uq_store_week"),
    )

    # Drop new tables
    op.drop_table("shift_assignments")
    op.drop_table("schedules")
    op.drop_table("weeks")

    # Drop added shift columns
    op.execute("ALTER TABLE shifts DROP COLUMN IF EXISTS headcount_required;")
    op.execute("ALTER TABLE shifts DROP COLUMN IF EXISTS created_at;")
