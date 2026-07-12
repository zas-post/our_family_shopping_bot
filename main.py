import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from os import getenv

# Настройка живых логов для Dozzle
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ShoppingBot")

# Загружаем токен из окружения
BOT_TOKEN = getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.critical("Бот не запущен: Переменная BOT_TOKEN не найдена!")
    sys.exit(1)

# ТУТ ИСПРАВЛЕНО: parse_mode вместо parseMode
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# Хендлер на команду /start
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_name} (ID: {user_id}) запустил бота через /start")
    await message.answer(
        f"Привет, {html.bold(user_name)}! Я готов к работе. Напиши, что нужно купить."
    )


# Хендлер на любое текстовое сообщение
@dp.message()
async def add_item_handler(message: Message) -> None:
    item_text = message.text
    user_name = message.from_user.full_name
    logger.info(f"Пользователь {user_name} добавил в список покупок: '{item_text}'")
    await message.reply(f"📌 Добавлено в корзину: {html.code(item_text)}")


async def main() -> None:
    logger.info("Профессиональный семейный бот на паттерне Repository успешно запущен!")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка при работе бота: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
