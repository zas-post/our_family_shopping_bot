import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем проверенный BOT_TOKEN напрямую из твоего файла config.py
from config import BOT_TOKEN

# Импортируем асинхронный движок из твоих настроек подключения к БД
from db.base import engine
# Импортируем Base из моделей, чтобы SQLAlchemy знала обо всех таблицах (ShoppingItem, ChatSetting)
from db.models import Base

# Импортируем твои оригинальные роутеры (из файлов common.py, shopping.py, store_alerts.py)
from handlers.common import router as common_router
from handlers.shopping import router as shopping_router
from handlers.store_alerts import router as store_alerts_router

# =====================================================================
# НАСТРОЙКА ЖИВЫХ ЛОГОВ ДЛЯ DOZZLE
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Направляем логи строго в консоль Docker
)
logger = logging.getLogger("ShoppingBot")

# Снижаем уровень логирования для библиотек, чтобы не засорять Dozzle
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Настройка бота с правильным parse_mode в snake_case
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Функция асинхронного создания таблиц, если файла базы данных еще нет
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
    dp.include_routers(
        common_router,
        shopping_router,
        store_alerts_router
    )
    
    logger.info("Бот готов к работе! Начинаем опрос серверов Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
