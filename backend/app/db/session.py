from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

# Создаем движок (engine)
# echo=True выводит SQL-запросы в консоль (полезно при разработке)
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True,
    future=True
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
)

# Функция для получения сессии (Dependency Injection)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session