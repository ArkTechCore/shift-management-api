from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, stores, schedules, weeks, timeclock
from app.api.api_v1.endpoints import manager_timeentries, payroll, availability, leave_request, memberships, ai_schedule
from app.api.api_v1.endpoints import developer  # NEW

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])

api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(weeks.router, prefix="/weeks", tags=["weeks"])

api_router.include_router(timeclock.router, prefix="/timeclock", tags=["timeclock"])
api_router.include_router(manager_timeentries.router, prefix="/manager/timeentries", tags=["manager-timeentries"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["payroll"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(leave_request.router, prefix="/leave-request", tags=["leave-request"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(ai_schedule.router, prefix="/ai", tags=["ai-schedule"])

# Developer routes (no tenant sensitive data; only tenant/plan toggles)
api_router.include_router(developer.router, prefix="/developer", tags=["developer"])
