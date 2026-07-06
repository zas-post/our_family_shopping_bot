import asyncio
from aiogram import Bot, Dispatcher
import config

# Импортируем движок базы данных для автоматического создания таблиц
from db.base import engine
from db.models import Base

# Импортируем роутеры из наших модулей
from handlers import common, shopping, store_alerts


async def main():
    # Автоматически создаем все таблицы в новом файле БД при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры в диспетчер
    dp.include_routers(common.router, store_alerts.router, shopping.router)

    print("Архитектурно оптимизированный семейный бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
