import asyncio
from aiogram import Bot, Dispatcher
import config

# Импортируем роутеры из наших модулей
from handlers import common, shopping, store_alerts


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры в диспетчер (порядок имеет значение!)
    dp.include_routers(common.router, store_alerts.router, shopping.router)

    print("Архитектурно оптимизированный семейный бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
