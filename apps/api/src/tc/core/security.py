from datetime import datetime, timedelta
from jose import jwt
from tc.core.config import settings


def create_access_token(subject: str) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
