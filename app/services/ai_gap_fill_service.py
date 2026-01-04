from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session, selectinload

from app.models.schedule import Schedule, Shift
from app.models.membership import StoreMembership
from app.models.availability import Availability
from app.models.leave_request import LeaveRequest
from app.models.week import Week
from app.services.groq_client import GroqClient


@dataclass
class Gap:
    shift_id: uuid.UUID
    needed: int


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _dt_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def build_gap_suggestions(
    db: Session,
    *,
    store_id: uuid.UUID,
    week_id: uuid.UUID,
    role_filter: str | None,
    max_suggestions_per_shift: int,
    use_groq: bool,
) -> Tuple[List[Dict], str]:
    wk = db.query(Week).filter(Week.id == week_id).first()
    if not wk:
        raise ValueError("Week not found")

    sched = (
        db.query(Schedule)
        .options(selectinload(Schedule.shifts).selectinload(Shift.assignments))
        .filter(Schedule.store_id == store_id, Schedule.week_id == week_id)
        .first()
    )

    if not sched:
        return ([], "No schedule exists yet. Create schedule first, then run gap-fill.")

    shifts: List[Shift] = list(sched.shifts or [])

    if role_filter:
        rf = role_filter.strip().lower()
        shifts = [s for s in shifts if (s.role or "").strip().lower() == rf]

    gaps: List[Gap] = []
    for sh in shifts:
        current = len(sh.assignments or [])
        needed = max(0, int(sh.headcount_required or 0) - current)
        if needed > 0:
            gaps.append(Gap(shift_id=sh.id, needed=needed))

    if not gaps:
        return ([], "No gaps found. All shifts are already filled.")

    # Eligible employees in this store (employee memberships only)
    emp_rows = (
        db.query(StoreMembership)
        .filter(
            StoreMembership.store_id == store_id,
            StoreMembership.is_active == True,
            StoreMembership.store_role == "employee",
        )
        .all()
    )
    employee_ids = [r.user_id for r in emp_rows]
    if not employee_ids:
        return ([], "No employees assigned to this store.")

    # Availability for that store+week (STRICT: must exist AND cover shift)
    av_rows = (
        db.query(Availability)
        .filter(
            Availability.store_id == store_id,
            Availability.week_id == week_id,
            Availability.employee_id.in_(employee_ids),
        )
        .all()
    )

    availability_map: Dict[uuid.UUID, List[Tuple[datetime, datetime]]] = {}
    for a in av_rows:
        if not a.available_start_at or not a.available_end_at:
            continue
        s = _dt_utc(a.available_start_at)
        e = _dt_utc(a.available_end_at)
        if e <= s:
            continue
        availability_map.setdefault(a.employee_id, []).append((s, e))

    # ✅ STRICT RULE: If employee has NO availability rows, they are NOT eligible
    eligible_with_availability = set(availability_map.keys())
    if not eligible_with_availability:
        return ([], "No employees have submitted availability for this store/week.")

    # Approved leave overlapping week dates
    leave_rows = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.store_id == store_id,
            LeaveRequest.employee_id.in_(list(eligible_with_availability)),
            LeaveRequest.status == "approved",
            LeaveRequest.start_date <= wk.week_end,
            LeaveRequest.end_date >= wk.week_start,
        )
        .all()
    )

    leave_map: Dict[uuid.UUID, List[Tuple]] = {}
    for lr in leave_rows:
        leave_map.setdefault(lr.employee_id, []).append((lr.start_date, lr.end_date))

    # Existing assignments per employee (avoid overlap)
    assigned_map: Dict[uuid.UUID, List[Tuple[datetime, datetime]]] = {}
    for sh in shifts:
        sh_start = _dt_utc(sh.start_at)
        sh_end = _dt_utc(sh.end_at)
        for a in (sh.assignments or []):
            assigned_map.setdefault(a.employee_id, []).append((sh_start, sh_end))

    def on_approved_leave(emp_id: uuid.UUID, shift_start: datetime, shift_end: datetime) -> bool:
        if emp_id not in leave_map:
            return False
        d1 = shift_start.date()
        d2 = shift_end.date()
        for (s, e) in leave_map[emp_id]:
            if s <= d1 <= e or s <= d2 <= e:
                return True
        return False

    def is_available(emp_id: uuid.UUID, shift_start: datetime, shift_end: datetime) -> bool:
        windows = availability_map.get(emp_id, [])
        for (a_s, a_e) in windows:
            if shift_start >= a_s and shift_end <= a_e:
                return True
        return False

    def conflicts(emp_id: uuid.UUID, shift_start: datetime, shift_end: datetime) -> bool:
        for (b_s, b_e) in assigned_map.get(emp_id, []):
            if _overlaps(shift_start, shift_end, b_s, b_e):
                return True
        return False

    assignment_count: Dict[uuid.UUID, int] = {eid: 0 for eid in eligible_with_availability}
    for eid, windows in assigned_map.items():
        if eid in assignment_count:
            assignment_count[eid] = len(windows)

    suggestions_out: List[Dict] = []

    groq = GroqClient()
    can_groq = use_groq and groq.is_configured()

    for sh in shifts:
        gap = next((g for g in gaps if g.shift_id == sh.id), None)
        if not gap:
            continue

        sh_start = _dt_utc(sh.start_at)
        sh_end = _dt_utc(sh.end_at)

        candidates: List[uuid.UUID] = []
        for eid in eligible_with_availability:
            if on_approved_leave(eid, sh_start, sh_end):
                continue
            if conflicts(eid, sh_start, sh_end):
                continue
            if not is_available(eid, sh_start, sh_end):
                continue
            candidates.append(eid)

        candidates.sort(key=lambda x: assignment_count.get(x, 0))
        top = candidates[: max_suggestions_per_shift]

        # Optional: Groq rerank only (small + cheap)
        if can_groq and top:
            payload = {
                "shift_start": sh_start.isoformat(),
                "shift_end": sh_end.isoformat(),
                "shift_role": sh.role,
                "candidates": [str(x) for x in top],
                "assignment_counts": {str(k): assignment_count.get(k, 0) for k in top},
                "instruction": "Return ONLY a JSON array of UUID strings reordered best-first.",
            }

            try:
                txt = await groq.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "Reorder candidates to fill a work shift. Output only JSON array of UUID strings.",
                        },
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                    temperature=0.0,
                    max_tokens=200,
                )
                arr = json.loads(txt)
                reranked = []
                for v in arr:
                    reranked.append(uuid.UUID(str(v)))
                top_set = set(top)
                top = [x for x in reranked if x in top_set]
                if not top:
                    top = candidates[: max_suggestions_per_shift]
            except Exception:
                top = candidates[: max_suggestions_per_shift]

        suggestions_out.append(
            {
                "shift_id": sh.id,
                "needed_slots": gap.needed,
                "suggested_employee_ids": top,
            }
        )

    note = (
        "STRICT mode: employees with NO availability rows are excluded. "
        "Rules used: approved leave + availability must cover shift + no overlap + fairness (fewer existing assignments)."
    )
    if use_groq:
        note += " Groq rerank used only when GROQ_API_KEY is set."

    return suggestions_out, note
