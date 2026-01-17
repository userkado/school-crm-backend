from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.school import ClassGroup
from app.schemas.school import ClassGroupCreate, ClassGroupResponse
from app.api.deps import allow_admin, get_current_user

router = APIRouter()

@router.post("/", response_model=ClassGroupResponse)
async def create_class(
    class_in: ClassGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_admin)  # <--- Только АДМИН может создавать классы
):
    """
    Создание нового учебного класса (напр. '9-B').
    Только для роли ADMIN.
    """
    # Проверяем, нет ли уже такого класса
    result = await db.execute(select(ClassGroup).filter(ClassGroup.name == class_in.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Class with this name already exists")

    new_class = ClassGroup(name=class_in.name)
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class

@router.get("/", response_model=list[ClassGroupResponse])
async def read_classes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(get_current_user) # <--- Любой авторизованный пользователь
):
    """
    Получить список всех классов.
    """
    result = await db.execute(select(ClassGroup))
    return result.scalars().all()