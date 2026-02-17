from fastapi import FastAPI
from tc.core.config import settings
from tc.api.v1.router import router as v1_router

app = FastAPI(title=settings.APP_NAME)

app.include_router(v1_router, prefix="/api/v1")
