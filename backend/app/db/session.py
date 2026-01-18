import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 1. Получаем переменную
raw_url = os.getenv("DATABASE_URL")

if not raw_url:
    print("WARNING: DATABASE_URL not found, using sqlite.")
    DATABASE_URL = "sqlite+aiosqlite:///./school.db"
    connect_args = {"check_same_thread": False}
else:
    # 2. ЧИСТКА ОТ МУСОРА (Самое важное!)
    # Удаляем пробелы по краям и случайные кавычки
    DATABASE_URL = raw_url.strip().replace('"', '').replace("'", "")

    # 3. Исправляем префикс для драйвера asyncpg
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Для Postgres аргументы не нужны
    connect_args = {}

# 4. Создаем движок
# Мы уверены, что URL теперь чистый
try:
    engine = create_async_engine(DATABASE_URL, echo=True, connect_args=connect_args)
except Exception as e:
    print(f"CRITICAL ERROR: Could not parse URL: {DATABASE_URL}")
    raise e

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