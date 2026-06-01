from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models import User, Conversation
from schemas import ConversationOut
from .deps import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ConversationOut, status_code=201)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(user_id=current_user.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.delete("/{conv_id}/")
async def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.scalar(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    if not conv:
        raise HTTPException(404, "Conversa não encontrada.")

    await db.delete(conv)
    await db.commit()

    return {"message": "Conversa deletada."}