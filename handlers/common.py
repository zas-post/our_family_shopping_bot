from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я Твой Семейный список покупок. 🛒\n\n"
        "<b>Как мной пользоваться:</b>\n"
        "• Добавить товары: `п+ Название 2шт`\n"
        "• Показать и закрепить список заново: /list или /pin\n\n"
        "Под списком есть кнопка `🏃‍♂️ Я в магазине!`, нажмите её, чтобы предупредить семью!"
    )
