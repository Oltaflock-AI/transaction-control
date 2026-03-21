from fastapi import APIRouter, Depends

from tc.core.security import require_user

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_user)])
