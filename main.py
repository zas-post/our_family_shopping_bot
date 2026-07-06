import asyncio
from aiogram import Bot, Dispatcher
import config

# Импортируем всё необходимое из пакета db, чтобы Python гарантированно прочитал модели
from db import engine, Base
from handlers import common, shopping, store_alerts


async def main():
    # Накатываем структуру таблиц прямо в файл БД перед запуском бота
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры в диспетчере
    dp.include_routers(common.router, store_alerts.router, shopping.router)

    print("Профессиональный семейный бот на паттерне Repository успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
