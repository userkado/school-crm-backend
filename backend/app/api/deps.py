from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData
from app.services.user import get_user_by_email

# Указываем FastAPI, где искать URL для входа (чтобы Swagger UI умел авторизовываться)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Эта функция проверяет токен.
    Если токен валиден - возвращает объект User.
    Если нет - выбрасывает ошибку 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # 2. Ищем пользователя в БД
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

# ... (код который был выше оставляем без изменений) ...

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not enough permissions"
            )
        return user

# Создаем готовые "проверяльщики"
allow_admin = RoleChecker(["ADMIN"])
allow_teacher = RoleChecker(["TEACHER", "ADMIN"]) # Админ тоже может всё, что может учитель