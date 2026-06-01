from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Nova conversa")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_id: Mapped[int]  = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="conversations")
    chats: Mapped[list["Chat"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Chat.created_at")