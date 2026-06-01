from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
import io, pypdf

from core.database import get_db
from core.config import settings
from models import User, Conversation, Chat
from schemas import MessageOut
from .deps import get_current_user

from langchain_groq import ChatGroq

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_text(content: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            return "\n".join(p.extract_text() or "" for p in reader.pages)[:3000]
        except Exception:
            return ""
    try:
        return content.decode("utf-8")[:3000]
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")[:3000]


async def _collect_file_context(files: list[UploadFile]) -> str:
    parts: list[str] = []
    for f in files:
        if not f.filename:
            continue
        content = await f.read()
        text = _extract_text(content, f.filename)
        if text:
            parts.append(f"--- {f.filename} ---\n{text}")
    return "\n\n".join(parts)


def _build_system_prompt(file_context: str) -> str:
    base = (
        "Você é um assistente de IA sênior responsável por tirar dúvidas sobre programação, "
        "especialmente Python, Django, DRF, FastAPI, JavaScript, TypeScript, HTML, CSS, Tailwind CSS. "
        "Use sempre a versão mais recente das bibliotecas e frameworks. "
        "Responda em formato markdown. Responda em português. "
        "Seja amigável e paciente. Ajude com atividades e estudos da faculdade."
    )
    if file_context:
        base += f"\n\nARQUIVOS ENVIADOS PELO USUÁRIO:\n{file_context}"
    return base


async def _generate_title(message: str) -> str:
    model = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.groq_api_key)
    response = await model.ainvoke([
        ("system", "Gere um título curto (máximo 5 palavras) para uma conversa. Responda APENAS o título, sem aspas."),
        ("human", message),
    ])
    return str(response.content).strip()[:100]


async def _ask_ai(message: str, file_context: str, history: list) -> str:
    model = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.groq_api_key)
    messages = [("system", _build_system_prompt(file_context))] + history + [("human", message)]
    response = await model.ainvoke(messages)
    return str(response.content)


# ── routes ───────────────────────────────────────────────────────────────────

@router.get("/{conv_id}/messages/")
async def list_messages(
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

    result = await db.execute(
        select(Chat)
        .where(Chat.conversation_id == conv_id)
        .order_by(Chat.created_at)
    )
    chats = result.scalars().all()

    return [
        {"id": c.id, "message": c.message, "response": c.response, "created_at": c.created_at}
        for c in chats
    ]


@router.post("/{conv_id}/messages/", response_model=MessageOut)
async def send_message(
    conv_id: int,
    message: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()] = [],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not message.strip():
        raise HTTPException(400, "Mensagem vazia.")

    conv = await db.scalar(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    if not conv:
        raise HTTPException(404, "Conversa não encontrada.")

    # histórico recente (últimas 3 trocas = 6 mensagens)
    result = await db.execute(
        select(Chat)
        .where(Chat.conversation_id == conv_id)
        .order_by(Chat.created_at)
    )
    previous = result.scalars().all()

    history = []
    for c in previous[-3:]:
        history.append(("human", c.message))
        history.append(("ai", c.response))

    file_context = await _collect_file_context(files)
    response_text = await _ask_ai(message, file_context, history)

    is_first = len(previous) == 0
    if is_first:
        conv.title = await _generate_title(message)
        await db.flush()

    db.add(Chat(
        user_id=current_user.id,
        conversation_id=conv.id,
        message=message,
        response=response_text,
    ))
    await db.commit()

    return MessageOut(
        message=message,
        response=response_text,
        conversation_title=conv.title if is_first else None,
    )