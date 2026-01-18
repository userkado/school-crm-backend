from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

# --- ПОЛУЧЕНИЕ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ ---
async def get_current_user_from_cookie(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Сначала ищем в заголовке (для Fetch/AJAX запросов с дашборда)
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 2. Если нет в заголовке, ищем в куках (резерв)
    if not token:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

    if not token:
        return None

    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    return user

# --- РЕГИСТРАЦИЯ ---
@router.post("/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("teacher"),
    db: AsyncSession = Depends(get_db)
):
    # Проверка
    result = await db.execute(select(User).filter(User.email == email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Первый пользователь - Админ
    result_count = await db.execute(select(User))
    users_count = len(result_count.scalars().all())
    final_role = "ADMIN" if users_count == 0 else role.upper()

    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        role=final_role,
        is_active=True # Сразу активен
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"msg": "Registration successful"}

# --- ВХОД (LOGIN) - ИСПРАВЛЕНО ПОД ТВОЙ HTML ---
@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Ищем пользователя
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    # Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Ставим куку (на всякий случай)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False 
    )

    # ГЛАВНОЕ: Возвращаем JSON с токеном, чтобы твой скрипт сработал
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role # Можно вернуть роль, чтобы фронт знал сразу
    }

# --- ПОЛУЧИТЬ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ ---
@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user_from_cookie)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

# --- СПИСОК ПОЛЬЗОВАТЕЛЕЙ (Админ) ---
@router.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    if not current_user or current_user.role != "ADMIN":
         raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()

# --- УДАЛЕНИЕ ---
@router.post("/delete/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    if not current_user or current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete self")

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"msg": "Deleted"}