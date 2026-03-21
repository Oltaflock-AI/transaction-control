from fastapi import APIRouter, Depends

from tc.core.security import require_role

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("admin"))],
)
