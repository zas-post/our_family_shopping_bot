import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

from db.repository import ShoppingRepository
from utils.parser import parse_item_and_amount

router = Router()
logger = logging.getLogger("ShoppingBot.Shopping")

# === КЛАВИАТУРА И ОБНОВЛЕНИЕ СПИСКА ===


async def get_shopping_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    products = await ShoppingRepository.get_items(chat_id)
    keyboard_rows = []

    for item in products:
        status_icon = "✅" if item.bought else "⬜️"
        amount_part = f" ({item.amount})" if item.amount else ""
        author_part = item.user_name if item.user_name else "Семья"

        btn_text = f"{status_icon} {item.product_text}{amount_part} — 🗓 {item.add_date} 👤 {author_part}"
        toggle_button = InlineKeyboardButton(
            text=btn_text, callback_data=f"db_toggle_{item.id}"
        )
        keyboard_rows.append([toggle_button])

        if item.bought:
            delete_button = InlineKeyboardButton(
                text=f"🗑 Удалить навсегда: {item.product_text}",
                callback_data=f"db_delete_{item.id}",
            )
            keyboard_rows.append([delete_button])

    if products:
        clear_btn = InlineKeyboardButton(
            text="🗑 Очистить все купленные", callback_data="db_clear_bought"
        )
        store_btn = InlineKeyboardButton(
            text="🏃‍♂️ Я в магазине!", callback_data="db_at_store"
        )
        keyboard_rows.append([clear_btn, store_btn])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


async def send_or_update_list(chat_id: int, bot, target_message: Message = None):
    products = await ShoppingRepository.get_items(chat_id)
    settings = await ShoppingRepository.get_chat_settings(chat_id)
    last_msg_id = settings.last_list_message_id if settings else None

    if not products:
        if last_msg_id:
            try:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=last_msg_id)
            except TelegramBadRequest:
                pass
            try:
                await bot.edit_message_text(
                    "🛒 Все покупки сделаны! Список пуст.",
                    chat_id=chat_id,
                    message_id=last_msg_id,
                )
                await ShoppingRepository.save_last_message_id(chat_id, None)
                return
            except TelegramBadRequest:
                pass

        if target_message:
            await target_message.answer("Список покупок пуст!")
        else:
            await bot.send_message(chat_id, "Список покупок пуст!")
        await ShoppingRepository.save_last_message_id(chat_id, None)
        return

    keyboard = await get_shopping_keyboard(chat_id)
    text_content = "🛒 Текущий список покупок:"

    if last_msg_id:
        try:
            await bot.edit_message_text(
                text_content,
                chat_id=chat_id,
                message_id=last_msg_id,
                reply_markup=keyboard,
            )
            return
        except TelegramBadRequest:
            pass

    new_msg = await bot.send_message(chat_id, text_content, reply_markup=keyboard)
    await ShoppingRepository.save_last_message_id(chat_id, new_msg.message_id)

    try:
        await bot.pin_chat_message(
            chat_id=chat_id, message_id=new_msg.message_id, disable_notification=True
        )
    except TelegramBadRequest:
        pass


# === ХЭНДЛЕРЫ РОУТЕРА ===


@router.message(Command("list", "pin"))
async def cmd_list(message: Message, bot):
    logger.info(
        f"📋 Пользователь {message.from_user.first_name} запросил перевывод списка покупок в чате {message.chat.id}"
    )
    settings = await ShoppingRepository.get_chat_settings(message.chat.id)
    old_msg_id = settings.last_list_message_id if settings else None
    if old_msg_id:
        try:
            await bot.unpin_chat_message(chat_id=message.chat.id, message_id=old_msg_id)
        except TelegramBadRequest:
            pass

    await ShoppingRepository.save_last_message_id(message.chat.id, None)
    await send_or_update_list(message.chat.id, bot, target_message=message)


@router.message(F.text & ~F.text.startswith("/"))
async def add_products(message: Message, bot):
    chat_id = message.chat.id
    text = message.text.strip()

    if not text.lower().startswith("п+"):
        return

    clean_text = text[2:].strip()
    if not clean_text:
        return

    incoming_items = [item.strip() for item in clean_text.split(",") if item.strip()]
    current_time = datetime.now().strftime("%d.%m %H:%M")
    user_name = message.from_user.first_name if message.from_user else "Семья"

    for raw_item in incoming_items:
        product_name, amount = parse_item_and_amount(raw_item)
        if product_name:
            await ShoppingRepository.add_item(
                chat_id, product_name, amount, current_time, user_name
            )
            # 🌟 Красивый лог добавления товара
            logger.info(
                f"🛒 ДОБАВЛЕН: '{product_name}' (кол-во: {amount or 'не указано'}) "
                f"пользователем {user_name} в чате {chat_id}"
            )

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    await send_or_update_list(chat_id, bot)


@router.callback_query(F.data.startswith("db_toggle_"))
async def toggle_product_status(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    product_id = int(callback.data.split("_")[2])
    user_name = callback.from_user.first_name

    await ShoppingRepository.toggle_item_status(product_id)

    # 🌟 Логируем факт переключения статуса
    logger.info(
        f"🔄 ИЗМЕНЕН СТАТУС: Товар ID {product_id} переключен пользователем {user_name} в чате {chat_id}"
    )

    try:
        await callback.message.edit_reply_markup(
            reply_markup=await get_shopping_keyboard(chat_id)
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("db_delete_"))
async def delete_product(callback: CallbackQuery, bot):
    chat_id = callback.message.chat.id
    product_id = int(callback.data.split("_")[2])
    user_name = callback.from_user.first_name

    await ShoppingRepository.delete_item(product_id)

    # 🌟 Логируем удаление
    logger.info(
        f"🗑 УДАЛЕН НАВСЕГДА: Товар ID {product_id} удален пользователем {user_name} в чате {chat_id}"
    )

    await send_or_update_list(chat_id, bot)
    await callback.answer("Товар удален")


@router.callback_query(F.data == "db_clear_bought")
async def clear_bought_items(callback: CallbackQuery, bot):
    chat_id = callback.message.chat.id
    user_name = callback.from_user.first_name

    deleted_rows = await ShoppingRepository.clear_bought_items(chat_id)

    if deleted_rows == 0:
        await callback.answer("Нет купленных товаров для удаления!", show_alert=True)
        return

    # 🌟 Логируем очистку списка
    logger.info(
        f"🧹 ОЧИСТКА: Пользователь {user_name} удалил все купленные товары ({deleted_rows} шт.) в чате {chat_id}"
    )

    await send_or_update_list(chat_id, bot)
    await callback.answer("Купленные товары удалены")
