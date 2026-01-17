from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.school import ClassGroup, Subject, BellSchedule
from app.schemas.school import ClassGroupResponse, SubjectResponse, BellResponse, BellCreate
from app.api.deps import allow_admin # Только админ может менять настройки

router = APIRouter()

# --- 1. УПРАВЛЕНИЕ КЛАССАМИ ---
@router.post("/classes/", response_model=ClassGroupResponse)
async def create_class(name: str, db: Annotated[AsyncSession, Depends(get_db)], _=Depends(allow_admin)):
    new_class = ClassGroup(name=name)
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class

@router.delete("/classes/{id}")
async def delete_class(id: int, db: Annotated[AsyncSession, Depends(get_db)], _=Depends(allow_admin)):
    item = await db.get(ClassGroup, id)
    if item:
        await db.delete(item)
        await db.commit()
    return {"ok": True}

# --- 2. УПРАВЛЕНИЕ ПРЕДМЕТАМИ ---
@router.post("/subjects/", response_model=SubjectResponse)
async def create_subject(name: str, db: Annotated[AsyncSession, Depends(get_db)], _=Depends(allow_admin)):
    new_subject = Subject(name=name)
    db.add(new_subject)
    await db.commit()
    await db.refresh(new_subject)
    return new_subject

# --- 3. УПРАВЛЕНИЕ ЗВОНКАМИ ---
@router.get("/bells/", response_model=list[BellResponse])
async def get_bells(db: Annotated[AsyncSession, Depends(get_db)]):
    # Сортируем по порядку (1, 2, 3 урок)
    result = await db.execute(select(BellSchedule).order_by(BellSchedule.order))
    return result.scalars().all()

@router.post("/bells/", response_model=BellResponse)
async def create_bell(bell: BellCreate, db: Annotated[AsyncSession, Depends(get_db)], _=Depends(allow_admin)):
    # Проверяем, нет ли уже такого номера урока
    existing = await db.execute(select(BellSchedule).filter(BellSchedule.order == bell.order))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Такой номер урока уже есть")
        
    new_bell = BellSchedule(order=bell.order, start_time=bell.start_time, end_time=bell.end_time)
    db.add(new_bell)
    await db.commit()
    await db.refresh(new_bell)
    return new_bell

@router.delete("/bells/{id}")
async def delete_bell(id: int, db: Annotated[AsyncSession, Depends(get_db)], _=Depends(allow_admin)):
    item = await db.get(BellSchedule, id)
    if item:
        await db.delete(item)
        await db.commit()
    return {"ok": True}


@router.get("/subjects/", response_model=list[SubjectResponse])
async def get_subjects(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Subject))
    return result.scalars().all()