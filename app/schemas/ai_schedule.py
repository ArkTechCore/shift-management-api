from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AiGapFillRequest(BaseModel):
    store_id: uuid.UUID
    week_id: uuid.UUID

    # default: NO Groq call (cheap)
    use_groq: bool = False

    # cap output
    max_suggestions_per_shift: int = Field(default=3, ge=1, le=10)

    # optional filter (ex: "cashier", "cook")
    role: str | None = None


class AiGapSuggestion(BaseModel):
    shift_id: uuid.UUID
    needed_slots: int
    suggested_employee_ids: list[uuid.UUID] = []


class AiGapFillResponse(BaseModel):
    store_id: uuid.UUID
    week_id: uuid.UUID
    generated_at: datetime
    suggestions: list[AiGapSuggestion]
    notes: str = ""
