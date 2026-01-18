import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 1. Получаем ссылку. Если её нет (None), используем заглушку для SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Если на сервере забыли добавить переменную, используем локальную базу,
    # чтобы программа хотя бы запустилась и выдала ошибку понятнее, или работала локально.
    print("WARNING: DATABASE_URL not found, using sqlite.")
    DATABASE_URL = "sqlite+aiosqlite:///./school.db"

# 2. Исправляем "postgres://" на "postgresql+asyncpg://" для драйвера
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 3. Настройки движка
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Создаем движок
engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session