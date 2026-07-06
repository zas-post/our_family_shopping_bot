from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class ShoppingItem(Base):
    __tablename__ = "shopping_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_text: Mapped[str] = mapped_column(String(255))
    amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bought: Mapped[int] = mapped_column(default=0)
    add_date: Mapped[str] = mapped_column(String(50))
    user_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Проверь эту строчку


class ChatSetting(Base):
    __tablename__ = "chat_settings"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_list_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_store_notification: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
