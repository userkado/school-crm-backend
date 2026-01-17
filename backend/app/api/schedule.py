from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.school import Schedule, ClassGroup, Subject
from app.models.user import User 
from app.schemas.school import ScheduleCreate, ScheduleResponse
from app.api.deps import allow_admin, get_current_user

router = APIRouter()

@router.post("/", response_model=ScheduleResponse)
async def create_schedule_item(
    schedule_in: ScheduleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_admin) 
):
    # 1. Проверки существования объектов
    class_exists = await db.get(ClassGroup, schedule_in.class_group_id)
    subject_exists = await db.get(Subject, schedule_in.subject_id)
    teacher_exists = await db.get(User, schedule_in.teacher_id)

    if not class_exists or not subject_exists:
        raise HTTPException(status_code=404, detail="Класс или Предмет не найдены")
    if not teacher_exists or teacher_exists.role != "TEACHER":
        raise HTTPException(status_code=400, detail="Учитель не найден или это не учитель")

    # ==========================================
    # 🔥 ПОЛИЦИЯ КОНФЛИКТОВ (ПРОВЕРКИ) 🔥
    # ==========================================

    # А. ПРОВЕРКА КАБИНЕТА
    # Ищем: есть ли урок в этот день, в это время, в этом кабинете?
    q_room = select(Schedule).filter(
        Schedule.day_of_week == schedule_in.day_of_week,
        Schedule.start_time == schedule_in.start_time,
        Schedule.room_number == schedule_in.room_number
    )
    res_room = await db.execute(q_room)
    if res_room.scalars().first():
        raise HTTPException(status_code=400, detail=f"⛔ Кабинет {schedule_in.room_number} уже занят в это время!")

    # Б. ПРОВЕРКА УЧИТЕЛЯ
    # Ищем: занят ли этот учитель другим уроком в это же время?
    q_teacher = select(Schedule).filter(
        Schedule.day_of_week == schedule_in.day_of_week,
        Schedule.start_time == schedule_in.start_time,
        Schedule.teacher_id == schedule_in.teacher_id
    )
    res_teacher = await db.execute(q_teacher)
    if res_teacher.scalars().first():
        raise HTTPException(status_code=400, detail=f"⛔ Учитель {teacher_exists.email} уже ведет урок в это время!")

    # В. ПРОВЕРКА КЛАССА
    # Ищем: есть ли у этого класса урок в это время?
    q_class = select(Schedule).filter(
        Schedule.day_of_week == schedule_in.day_of_week,
        Schedule.start_time == schedule_in.start_time,
        Schedule.class_group_id == schedule_in.class_group_id
    )
    res_class = await db.execute(q_class)
    if res_class.scalars().first():
        raise HTTPException(status_code=400, detail=f"⛔ У класса {class_exists.name} уже есть урок в это время!")

    # ==========================================

    # Если все проверки пройдены — сохраняем
    new_item = Schedule(
        day_of_week=schedule_in.day_of_week,
        start_time=schedule_in.start_time,
        end_time=schedule_in.end_time,
        room_number=schedule_in.room_number,
        class_group_id=schedule_in.class_group_id,
        subject_id=schedule_in.subject_id,
        teacher_id=schedule_in.teacher_id
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

# ... (Остальной код get_schedule и delete_schedule_item оставьте без изменений) ...
@router.get("/", response_model=list[ScheduleResponse])
async def get_schedule(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user = Depends(get_current_user),
    class_id: int | None = None,
    teacher_id: int | None = None,
    day: str | None = None
):
    query = select(Schedule).options(
        selectinload(Schedule.subject),
        selectinload(Schedule.class_group),
        selectinload(Schedule.teacher)
    )
    if current_user.role == "TEACHER":
        query = query.filter(Schedule.teacher_id == current_user.id)
    if class_id:
        query = query.filter(Schedule.class_group_id == class_id)
    if day:
        query = query.filter(Schedule.day_of_week == day)
    if teacher_id:
        query = query.filter(Schedule.teacher_id == teacher_id)
    result = await db.execute(query)
    schedules = result.scalars().all()
    response_data = []
    for item in schedules:
        resp = ScheduleResponse.model_validate(item)
        resp.subject_name = item.subject.name if item.subject else "Unknown"
        resp.class_group_name = item.class_group.name if item.class_group else "Unknown"
        resp.teacher_name = item.teacher.email if item.teacher else "No Teacher"
        response_data.append(resp)
    return response_data

@router.delete("/{id}")
async def delete_schedule_item(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_admin)
):
    item = await db.get(Schedule, id)
    if not item:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await db.delete(item)
    await db.commit()
    return {"message": "Lesson deleted"}