from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.models.user import User

# 👇 ВОТ ЗДЕСЬ БЫЛА ОШИБКА. МЫ ДОБАВИЛИ UserPasswordChange В ИМПОРТЫ
from app.schemas.user import UserCreate, Token, UserResponse, UserUpdate, UserPasswordChange
from app.api.deps import get_current_user, allow_admin 

router = APIRouter()

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---
async def authenticate_user(session: AsyncSession, email: str, password: str):
    result = await session.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# --- РЕГИСТРАЦИЯ ---
@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# --- ВХОД (LOGIN) ---
@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- ПРОФИЛЬ ---
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user

# --- СПИСОК ПОЛЬЗОВАТЕЛЕЙ (Админ) ---
@router.get("/users", response_model=list[UserResponse])
async def read_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_admin) 
):
    result = await db.execute(select(User))
    return result.scalars().all()

# --- РЕДАКТИРОВАТЬ ПОЛЬЗОВАТЕЛЯ (Админ) ---
@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_admin)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)

    await db.commit()
    await db.refresh(user)
    return user

# --- СМЕНА ПАРОЛЯ (Личный кабинет) ---
@router.post("/change-password")
async def change_password(
    body: UserPasswordChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user = Depends(get_current_user)
):
    # 1. Проверяем старый пароль
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Старый пароль введен неверно")
    
    # 2. Сохраняем новый
    current_user.hashed_password = get_password_hash(body.new_password)
    
    await db.commit()
    return {"message": "Пароль успешно изменен"}