from fastapi import APIRouter

from tc.api.v1.admin import router as admin_router
from tc.api.v1.audit import router as audit_router
from tc.api.v1.auth import router as auth_router
from tc.api.v1.health import router as health_router
from tc.api.v1.tasks import router as tasks_router
from tc.api.v1.timeline import router as timeline_router
from tc.api.v1.transactions import router as transactions_router

router = APIRouter()

# Public
router.include_router(health_router)
router.include_router(auth_router)

# Protected (auth enforced per-endpoint or at router level)
router.include_router(transactions_router)
router.include_router(tasks_router)
router.include_router(timeline_router)
router.include_router(audit_router)
router.include_router(admin_router)
