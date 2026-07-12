import asyncio
import logging
import logging.handlers
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем проверенный BOT_TOKEN напрямую из твоего файла config.py
from config import BOT_TOKEN

# Импортируем асинхронный движок из твоих настроек подключения к БД
from db.base import engine

# Импортируем Base из моделей, чтобы SQLAlchemy знала обо всех таблицах
from db.models import Base

# Импортируем роутеры хендлеров
from handlers.common import router as common_router
from handlers.shopping import router as shopping_router
from handlers.store import router as store_router

# =====================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ И АВТОМАТИЧЕСКОЙ РОТАЦИИ
# =====================================================================
# Создаем папку для лог-файлов на сервере, если её ещё нет
os.makedirs("logs", exist_ok=True)

# Форматирование логов: дата - уровень - компонент - текст сообщения
log_formatter = logging.Formatter(
    "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)

# 1. Стримовый обработчик для Dozzle (вывод в sys.stdout)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

# 2. Ротационный обработчик для сохранения логов в файл
# Каждый файл максимум 5 МБ (5 * 1024 * 1024 байт). Храним 5 архивных копий.
file_handler = logging.handlers.RotatingFileHandler(
    filename="logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

# Настройка корневого логгера
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger("ShoppingBot")

# Снижаем уровень детализации внешних библиотек, чтобы не забивать диск
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Настройка бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# Функция асинхронного создания таблиц
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    logger.info("Семейный список покупок успешно запускается...")

    logger.info("Автоматическая проверка и инициализация базы данных...")
    try:
        await init_db()
        logger.info("База данных успешно подключена и проверена.")
    except Exception as e:
        logger.error(f"Критическая ошибка при инициализации БД: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Регистрация роутеров и обработчиков событий...")
    dp.include_routers(common_router, shopping_router, store_router)

    logger.info("Бот готов к работе! Начинаем опрос серверов Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
