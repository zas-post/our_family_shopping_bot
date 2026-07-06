from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from datetime import datetime, timedelta

from db.base import async_session
from db.models import ChatSetting
from handlers.shopping import get_chat_settings

router = Router()


async def save_store_notification_time(chat_id: int, time_str: str):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                sqlite_insert(ChatSetting)
                .values(chat_id=chat_id, last_store_notification=time_str)
                .on_conflict_do_update(
                    index_elements=[ChatSetting.chat_id],
                    set_={ChatSetting.last_store_notification: time_str},
                )
            )
            await session.execute(stmt)


@router.callback_query(F.data == "db_at_store")
async def user_at_store_notification(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_name = callback.from_user.first_name
    now = datetime.now()

    settings = await get_chat_settings(chat_id)
    if settings and settings.last_store_notification:
        try:
            last_time = datetime.strptime(
                settings.last_store_notification, "%Y-%m-%d %H:%M:%S"
            )
            if now - last_time < timedelta(minutes=15):
                await callback.answer(
                    "Уведомление уже отправлено недавно! Не паникуйте.", show_alert=True
                )
                return
        except ValueError:
            pass

    await save_store_notification_time(chat_id, now.strftime("%Y-%m-%d %H:%M:%S"))

    await callback.message.answer(
        f"🚨 **ВНИМАНИЕ ВСЕМ ДОМА!** 🚨\n\n"
        f"🏃‍♂️ **{user_name}** уже зашел в магазин!\n"
        f"⏳ Если нужно что-то добавить — **срочно пишите через 'п+' прямо сейчас!**\n"
        f"Через 5 минут список будет заморожен."
    )
    await callback.answer("Уведомление отправлено!")
