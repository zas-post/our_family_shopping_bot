from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./shopping_bot.db"

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика для создания асинхронных сессий
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass
