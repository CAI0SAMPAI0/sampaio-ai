from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.access_token_expire_days
    )
    return jwt.encode(
        {'sub': str(subject), 'exp': expire},
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_refresh_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(
        {'sub': str(subject), 'exp': expire},
        settings.secret_key,
        algorithm=settings.algorithm
    )


def decode_token(token: str) -> str | int:
    """Retorna o subject do token decodificado ou None se o token for inválido ou expirado."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    sub: str | None = payload.get('sub')
    if sub is None:
        raise JWTError('Token inválido: subject ausente')
    return sub