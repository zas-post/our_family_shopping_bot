import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Подключаем роутеры из твоих файлов папки handlers
from handlers.start import router as start_router
from handlers.shopping import router as shopping_router
from handlers.store import router as store_router

# Настройка живых логов для Dozzle
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ShoppingBot")

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("Переменная BOT_TOKEN не найдена в .env!")
    sys.exit(1)

# ИСПРАВЛЕНО: parse_mode через нижнее подчеркивание
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def main() -> None:
    logger.info("Запуск семейного списка покупок на SQLAlchemy...")

    # Регистрируем роутеры всех модулей
    dp.include_routers(start_router, shopping_router, store_router)

    logger.info("Оригинальная архитектура и Inline-таблицы успешно подключены!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
