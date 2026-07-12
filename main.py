import asyncio
import logging
import sys
import sqlite3
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# Настройка логов для Dozzle
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

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# =====================================================================
# РЕПОЗИТОРИЙ БД
# =====================================================================
class ShoppingRepository:
    def __init__(self, db_path="shopping_bot.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Чистая и верная структура таблицы
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shopping_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    user_name TEXT
                )
            """)
            conn.commit()

    def add_item(self, item_name, user_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO shopping_list (item_name, user_name) VALUES (?, ?)",
                (item_name, user_name),
            )
            conn.commit()

    def get_all_items(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, item_name, user_name FROM shopping_list")
            return cursor.fetchall()


repo = ShoppingRepository()


# =====================================================================
# ГЕНЕРАЦИЯ ТАБЛИЦЫ СПИСКА
# =====================================================================
def generate_shopping_table():
    items = repo.get_all_items()
    if not items:
        return "🛒 Список покупок пуст."

    table = f"{html.bold('📋 ТЕКУЩИЙ СПИСОК ПОКУПОК:')}\n"
    table += "<code>" + "—" * 30 + "</code>\n"

    for idx, item, user in items:
        table += f"🔹 {html.code(item)} (добавил: {user})\n"

    table += "<code>" + "—" * 30 + "</code>"
    return table


# =====================================================================
# ХЕНДЛЕРЫ
# =====================================================================


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.full_name
    logger.info(f"Пользователь {user_name} запустил бота")
    await message.answer(
        f"Привет, {user_name}! Используй команду {html.bold('п+ название')} для добавления товара."
    )


@dp.message()
async def handle_message(message: Message):
    text = message.text.strip()
    user_name = message.from_user.full_name

    if text.lower().startswith("п+"):
        product = text[2:].strip()

        if not product:
            await message.reply("❌ Укажите название продукта после 'п+'")
            return

        repo.add_item(product, user_name)
        logger.info(f"Пользователь {user_name} успешно добавил: '{product}'")

        table_output = generate_shopping_table()
        await message.answer(table_output)
    else:
        table_output = generate_shopping_table()
        await message.answer(table_output)


async def main():
    logger.info("Профессиональный семейный бот на паттерне Repository успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
