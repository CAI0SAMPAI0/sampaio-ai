from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from core.database import get_db
from core.security import decode_token
from models import User

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(401, "Token inválido ou expirado.")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(401, "Usuário não encontrado.")

    return user