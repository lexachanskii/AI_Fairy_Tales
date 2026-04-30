from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, JSON, ForeignKey
from app.db.base import Base


class Tale(Base):
    __tablename__ = "tales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    genre: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    hero: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    moral: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    size: Mapped[int] = mapped_column(Integer)
    content: Mapped[list] = mapped_column(JSON)

    # nullable=True — сказка «открепляется» от пользователя в двух сценариях:
    #   1. create_tale: старая сказка получает user_id=None перед созданием новой
    #   2. complete_tale: завершённая сказка отвязывается от пользователя
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="tale")
