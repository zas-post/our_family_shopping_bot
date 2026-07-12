import asyncio
import logging
import logging.handlers
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем проверенный BOT_TOKEN напрямую из файла конфигурации config.py
from config import BOT_TOKEN

# Импортируем асинхронный движок подключения к SQLite
from db.base import engine

# Импортируем декларативную основу Base для автоматического создания всех таблиц
from db.models import Base

# Импортируем роутеры обработчиков событий (строго по именам твоих файлов!)
from handlers.common import router as common_router
from handlers.shopping import router as shopping_router
from handlers.store_alerts import router as store_alerts_router

# =====================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ И АВТОМАТИЧЕСКОЙ РОТАЦИИ ФАЙЛОВ
# =====================================================================
# Создаем директорию для хранения локальных лог-файлов, если её нет
os.makedirs("logs", exist_ok=True)

# Задаем единый понятный формат логов: Дата Время - [Уровень] - Компонент - Текст
log_formatter = logging.Formatter(
    "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)

# 1. Обработчик вывода логов в консоль (sys.stdout) — именно его считывает Dozzle
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

# 2. Обработчик ротации лог-файлов на диске
# Максимальный размер одного файла: 5 МБ (5 * 1024 * 1024 байт).
# При превышении лимита старый файл переименовывается, и создается новый.
# Храним не более 5 архивных копий, более старые файлы удаляются автоматически.
file_handler = logging.handlers.RotatingFileHandler(
    filename="logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

# Привязываем оба созданных обработчика к корневому логгеру приложения
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)

# Создаем изолированный логгер для главного процесса бота
logger = logging.getLogger("ShoppingBot")

# Снижаем уровень шума от внешних системных библиотек, чтобы не засорять Dozzle
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Настройка экземпляра бота с поддержкой HTML-разметки в сообщениях
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# Функция автоматической инициализации таблиц базы данных при старте
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Главная асинхронная функция жизненного цикла бота
async def main() -> None:
    logger.info("Семейный список покупок успешно запускается...")

    logger.info("Автоматическая проверка и инициализация базы данных...")
    try:
        await init_db()
        logger.info("База данных успешно подключена, структура таблиц проверена.")
    except Exception as e:
        logger.error(f"Критическая ошибка при инициализации БД: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Регистрация роутеров и обработчиков событий...")
    dp.include_routers(common_router, shopping_router, store_alerts_router)

    logger.info("Бот готов к работе! Начинаем опрос серверов Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
