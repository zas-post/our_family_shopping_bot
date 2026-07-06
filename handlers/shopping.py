from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from datetime import datetime

from db.base import async_session
from db.models import ShoppingItem, ChatSetting
from utils.parser import parse_item_and_amount

router = Router()

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ БАЗЫ ДАННЫХ ===


# Добавили параметр user_name в функцию сохранения
async def add_to_db(
    chat_id: int, text: str, amount: str | None, date_str: str, user_name: str
):
    async with async_session() as session:
        async with session.begin():
            new_item = ShoppingItem(
                chat_id=chat_id,
                product_text=text,
                amount=amount,
                add_date=date_str,
                user_name=user_name,  # Сохраняем имя
            )
            session.add(new_item)


async def get_from_db(chat_id: int) -> list[ShoppingItem]:
    async with async_session() as session:
        result = await session.execute(
            select(ShoppingItem).where(ShoppingItem.chat_id == chat_id)
        )
        return list(result.scalars().all())


async def toggle_in_db(product_id: int):
    async with async_session() as session:
        async with session.begin():
            item = await session.get(ShoppingItem, product_id)
            if item:
                item.bought = 1 if item.bought == 0 else 0


async def delete_from_db(product_id: int):
    async with async_session() as session:
        async with session.begin():
            item = await session.get(ShoppingItem, product_id)
            if item:
                await session.delete(item)


async def clear_bought_from_db(chat_id: int) -> int:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                delete(ShoppingItem).where(
                    ShoppingItem.chat_id == chat_id, ShoppingItem.bought == 1
                )
            )
            return result.rowcount


async def get_chat_settings(chat_id: int) -> ChatSetting | None:
    async with async_session() as session:
        result = await session.execute(
            select(ChatSetting).where(ChatSetting.chat_id == chat_id)
        )
        return result.scalar_one_or_none()


async def save_last_message_id(chat_id: int, message_id: int | None):
    async with async_session() as session:
        async with session.begin():
            stmt = (
                sqlite_insert(ChatSetting)
                .values(chat_id=chat_id, last_list_message_id=message_id)
                .on_conflict_do_update(
                    index_elements=[ChatSetting.chat_id],
                    set_={ChatSetting.last_list_message_id: message_id},
                )
            )
            await session.execute(stmt)


# === КЛАВИАТУРА И ОБНОВЛЕНИЕ СПИСКА ===


async def get_shopping_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    products = await get_from_db(chat_id)
    keyboard_rows = []

    for item in products:
        status_icon = "✅" if item.bought else "⬜️"
        amount_part = f" ({item.amount})" if item.amount else ""
        author_part = item.user_name if item.user_name else "Семья"

        # Собираем красивую информативную строку без всяких \n
        # Теперь места вагон, всё влезет в одну строку на любом экране!
        btn_text = f"{status_icon} {item.product_text}{amount_part} — 🗓 {item.add_date} 👤 {author_part}"

        # Кнопка переключения статуса (купил/не купил) на всю ширину
        toggle_button = InlineKeyboardButton(
            text=btn_text, callback_data=f"db_toggle_{item.id}"
        )
        keyboard_rows.append([toggle_button])

        # Если товар ПОМЕЧЕН КАК КУПЛЕННЫЙ (✅), добавляем под него маленькую кнопку окончательного удаления
        if item.bought:
            delete_button = InlineKeyboardButton(
                text=f"🗑 Удалить навсегда: {item.product_text}",
                callback_data=f"db_delete_{item.id}",
            )
            keyboard_rows.append([delete_button])

    # Нижняя панель управления
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
    products = await get_from_db(chat_id)
    settings = await get_chat_settings(chat_id)
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
                await save_last_message_id(chat_id, None)
                return
            except TelegramBadRequest:
                pass

        if target_message:
            await target_message.answer("Список покупок пуст!")
        else:
            await bot.send_message(chat_id, "Список покупок пуст!")
        await save_last_message_id(chat_id, None)
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
    await save_last_message_id(chat_id, new_msg.message_id)

    try:
        await bot.pin_chat_message(
            chat_id=chat_id, message_id=new_msg.message_id, disable_notification=True
        )
    except TelegramBadRequest:
        print("[Warning] Не удалось закрепить сообщение.")


# === ХЭНДЛЕРЫ РОУТЕРА ===


@router.message(Command("list", "pin"))
async def cmd_list(message: Message, bot):
    settings = await get_chat_settings(message.chat.id)
    old_msg_id = settings.last_list_message_id if settings else None
    if old_msg_id:
        try:
            await bot.unpin_chat_message(chat_id=message.chat.id, message_id=old_msg_id)
        except TelegramBadRequest:
            pass

    await save_last_message_id(message.chat.id, None)
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

    # Извлекаем имя пользователя, который отправил сообщение
    user_name = message.from_user.first_name or "Инкогнито"

    for raw_item in incoming_items:
        product_name, amount = parse_item_and_amount(raw_item)
        if product_name:
            # Передаем имя в базу данных
            await add_to_db(chat_id, product_name, amount, current_time, user_name)

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    await send_or_update_list(chat_id, bot)


@router.callback_query(F.data.startswith("db_toggle_"))
async def toggle_product_status(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    await toggle_in_db(product_id)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=await get_shopping_keyboard(callback.message.chat.id)
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("db_delete_"))
async def delete_product(callback: CallbackQuery, bot):
    chat_id = callback.message.chat.id
    product_id = int(callback.data.split("_")[2])

    await delete_from_db(product_id)
    await send_or_update_list(chat_id, bot)
    await callback.answer("Товар удален")


@router.callback_query(F.data == "db_clear_bought")
async def clear_bought_items(callback: CallbackQuery, bot):
    chat_id = callback.message.chat.id
    deleted_rows = await clear_bought_from_db(chat_id)

    if deleted_rows == 0:
        await callback.answer("Нет купленных товаров для удаления!", show_alert=True)
        return

    await send_or_update_list(chat_id, bot)
    await callback.answer("Купленные товары удалены")
