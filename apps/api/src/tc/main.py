from fastapi import FastAPI

from tc.api.v1.router import router as v1_router
from tc.core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(v1_router, prefix="/api/v1")
