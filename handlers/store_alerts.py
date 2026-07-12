import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

from db.repository import ShoppingRepository

router = Router()
logger = logging.getLogger("ShoppingBot.StoreAlerts")


@router.callback_query(F.data == "db_at_store")
async def user_at_store_notification(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_name = callback.from_user.first_name
    now = datetime.now()

    settings = await ShoppingRepository.get_chat_settings(chat_id)
    if settings and settings.last_store_notification:
        try:
            last_time = datetime.strptime(
                settings.last_store_notification, "%Y-%m-%d %H:%M:%S"
            )
            if now - last_time < timedelta(minutes=15):
                logger.warning(
                    f"⚠️ Флуд-контроль: {user_name} нажал 'Я в магазине' в чате {chat_id} повторно (прошло менее 15 мин)"
                )
                await callback.answer(
                    "Уведомление уже отправлено недавно! Не паникуйте.", show_alert=True
                )
                return
        except ValueError:
            pass

    await ShoppingRepository.save_store_notification_time(
        chat_id, now.strftime("%Y-%m-%d %H:%M:%S")
    )

    # Логируем отправку важного алерта всей семье
    logger.info(
        f"🚨 АЛЕРТ: Пользователь {user_name} сообщил, что он в магазине! Чат: {chat_id}"
    )

    await callback.message.answer(
        f"🚨 **ВНИМАНИЕ ВСЕМ ДОМА!** 🚨\n\n"
        f"🏃‍♂️ **{user_name}** уже в магазине!\n"
        f"⏳ Если нужно что-то добавить — **срочно пишите через 'п+' прямо сейчас!**\n"
        f"Через 5 минут список будет заморожен."
    )
    await callback.answer("Уведомление отправлено!")
