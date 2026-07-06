from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from db.base import async_session
from db.models import ShoppingItem, ChatSetting

class ShoppingRepository:
    @staticmethod
    async def add_item(chat_id: int, text: str, amount: str | None, date_str: str, user_name: str):
        async with async_session() as session:
            async with session.begin():
                new_item = ShoppingItem(
                    chat_id=chat_id,
                    product_text=text[:100],  # Валидация: ограничиваем длину до 100 символов
                    amount=amount,
                    add_date=date_str,
                    user_name=user_name
                )
                session.add(new_item)

    @staticmethod
    async def get_items(chat_id: int) -> list[ShoppingItem]:
        async with async_session() as session:
            result = await session.execute(select(ShoppingItem).where(ShoppingItem.chat_id == chat_id))
            return list(result.scalars().all())

    @staticmethod
    async def toggle_item_status(product_id: int):
        async with async_session() as session:
            async with session.begin():
                item = await session.get(ShoppingItem, product_id)
                if item:
                    item.bought = 1 if item.bought == 0 else 0

    @staticmethod
    async def delete_item(product_id: int):
        async with async_session() as session:
            async with session.begin():
                item = await session.get(ShoppingItem, product_id)
                if item:
                    await session.delete(item)

    @staticmethod
    async def clear_bought_items(chat_id: int) -> int:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    delete(ShoppingItem).where(ShoppingItem.chat_id == chat_id, ShoppingItem.bought == 1)
                )
                return result.rowcount

    @staticmethod
    async def get_chat_settings(chat_id: int) -> ChatSetting | None:
        async with async_session() as session:
            result = await session.execute(select(ChatSetting).where(ChatSetting.chat_id == chat_id))
            return result.scalar_one_or_none()

    @staticmethod
    async def save_last_message_id(chat_id: int, message_id: int | None):
        async with async_session() as session:
            async with session.begin():
                stmt = sqlite_insert(ChatSetting).values(
                    chat_id=chat_id, last_list_message_id=message_id
                ).on_conflict_do_update(
                    index_elements=[ChatSetting.chat_id],
                    set_={ChatSetting.last_list_message_id: message_id}
                )
                await session.execute(stmt)

    @staticmethod
    async def save_store_notification_time(chat_id: int, time_str: str):
        async with async_session() as session:
            async with session.begin():
                stmt = sqlite_insert(ChatSetting).values(
                    chat_id=chat_id, last_store_notification=time_str
                ).on_conflict_do_update(
                    index_elements=[ChatSetting.chat_id],
                    set_={ChatSetting.last_store_notification: time_str}
                )
                await session.execute(stmt)
