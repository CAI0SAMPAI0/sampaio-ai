from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from core.database import get_db
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from models import User, UserProfile
from schemas import (
    RegisterIn, TokenOut, RefreshIn,
    ProfileOut, ProfileUpdateOut, ChangePasswordIn,
)
from .deps import get_current_user
import base64, uuid

router = APIRouter()


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    """_summary_

    Args:
        body (RegisterIn): _description_
        db (AsyncSession, optional): _description_. Defaults to Depends(get_db).
    """
    exists = await db.scalar(select(User).where(User.username == body.username))
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=body.username,
        password_hash=hash_password(body.password)
    )
    db.add(user)
    await db.flush()

    db.add(UserProfile(user_id=user.id))
    await db.commit()

    return TokenOut(
        access=create_access_token(user.id),
        refresh=create_refresh_token(user.id),
    )


@router.post("/login")
async def login(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    """_summary_

    Args:
        body (RegisterIn): _description_
        db (AsyncSession, optional): _description_. Defaults to Depends(get_db).
    """
    user = await db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return TokenOut(
        access=create_access_token(user.id),
        refresh=create_refresh_token(user.id),
    )

@router.post("/refresh/")
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        user_id = decode_token(body.refresh)
    except JWTError:
        raise HTTPException(401, "Token inválido ou expirado.")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(401, "Usuário não encontrado.")

    return {"access": create_access_token(user.id)}


@router.post("/logout/")
async def logout(body: RefreshIn):
    # stateless JWT — apenas confirma recebimento
    # para blacklist real, adicione redis futuramente
    return JSONResponse(status_code=205, content={"message": "Logout successful."})


@router.get("/me/", response_model=ProfileOut)
async def profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.refresh(current_user, ["profile"])
    profile = current_user.profile

    return ProfileOut(
        id=current_user.id,
        username=current_user.username,
        avatar=profile.avatar if profile else None,
    )


@router.patch("/me/update/")
async def update_profile(
    username: str | None = None,
    avatar: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.refresh(current_user, ["profile"])

    if username:
        conflict = await db.scalar(
            select(User).where(User.username == username, User.id != current_user.id)
        )
        if conflict:
            raise HTTPException(400, "Username já em uso.")
        current_user.username = username

    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if avatar:
        content = await avatar.read()
        # guarda como data URL — sem depender de storage externo
        mime = avatar.content_type or "image/jpeg"
        b64 = base64.b64encode(content).decode()
        profile.avatar = f"data:{mime};base64,{b64}"

    await db.commit()
    await db.refresh(current_user)

    return ProfileUpdateOut(
        username=current_user.username,
        avatar=profile.avatar,
    )


@router.post("/me/password/")
async def change_password(
    body: ChangePasswordIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(400, "Senha atual incorreta.")
    if len(body.new_password) < 6:
        raise HTTPException(400, "Nova senha muito curta.")

    current_user.password = hash_password(body.new_password)
    await db.commit()

    return {"message": "Senha alterada com sucesso."}