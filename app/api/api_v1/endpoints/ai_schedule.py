from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.access import require_store_access
from app.models.user import User
from app.schemas.ai_schedule import AiGapFillRequest, AiGapFillResponse, AiGapSuggestion
from app.services.ai_gap_fill_service import build_gap_suggestions

router = APIRouter()


@router.post("/gap-fill", response_model=AiGapFillResponse)
async def gap_fill_suggestions(
    data: AiGapFillRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Managers/Admin only")

    require_store_access(db, user, str(data.store_id))

    suggestions, notes = await build_gap_suggestions(
        db,
        store_id=data.store_id,
        week_id=data.week_id,
        role_filter=data.role,
        max_suggestions_per_shift=data.max_suggestions_per_shift,
        use_groq=data.use_groq,
    )

    return AiGapFillResponse(
        store_id=data.store_id,
        week_id=data.week_id,
        generated_at=datetime.now(timezone.utc),
        suggestions=[AiGapSuggestion(**s) for s in suggestions],
        notes=notes,
    )
