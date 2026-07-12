import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from os import getenv

# =====================================================================
# НАСТРОЙКА НАСТОЯЩИХ ЖИВЫХ ЛОГОВ (Для Dozzle)
# =====================================================================
logging.basicConfig(
    level=logging.INFO,  # Уровень INFO позволяет видеть всё: от старта до кликов
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Направляем логи прямо в Docker
)
logger = logging.getLogger("ShoppingBot")

# Загружаем токен из .env файла, который проброшен через Docker
BOT_TOKEN = getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.critical("Бот не запущен: Переменная BOT_TOKEN не найдена в файле .env!")
    sys.exit(1)

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# =====================================================================
# ХЕНДЛЕРЫ (ОБРАБОТКА КОМАНД И ДЕЙСТВИЙ)
# =====================================================================


# 1. Обработка команды /start
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.full_name
    user_id = message.from_user.id

    # Этот лог МГНОВЕННО отобразится в Dozzle со всеми данными!
    logger.info(
        f"Пользователь {user_name} (ID: {user_id}) запустил бота командой /start"
    )

    await message.answer(
        f"Привет, {html.bold(user_name)}! Я твой профессиональный семейный помощник для покупок. Напиши, что нужно купить."
    )


# 2. Пример обработки добавления товара (команда /add или любой текст)
@dp.message()
async def add_item_handler(message: Message) -> None:
    item_text = message.text
    user_name = message.from_user.full_name

    # 💥 ВОТ ЗДЕСЬ ПРОИСХОДИТ МАГИЯ ЛОГИРОВАНИЯ ДЕЙСТВИЙ:
    logger.info(f"Пользователь {user_name} добавил в список покупок: '{item_text}'")

    # Тут будет твоя логика сохранения в базу данных shopping_bot.db
    # Сделай запись в репозиторий...

    await message.reply(f"📌 Добавлено в корзину: {html.code(item_text)}")


# =====================================================================
# ЗАПУСК БОТА
# =====================================================================
async def main() -> None:
    logger.info("Профессиональный семейный бот на паттерне Repository успешно запущен!")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка при работе бота: {e}", exc_info=True)


if __name__ == "__main__":
    # Запуск асинхронного движка
    asyncio.run(main())
