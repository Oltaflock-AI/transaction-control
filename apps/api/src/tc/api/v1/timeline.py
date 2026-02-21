from fastapi import APIRouter, Depends

from tc.core.security import require_user

router = APIRouter(prefix="/timeline", tags=["timeline"], dependencies=[Depends(require_user)])
