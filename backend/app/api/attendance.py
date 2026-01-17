from datetime import datetime, date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.school import Attendance, Student, Schedule # Добавили Schedule
from app.schemas.school import AttendanceCreate, AttendanceResponse
from app.api.deps import get_current_user, allow_teacher

router = APIRouter()

DAYS_MAPPING = {
    0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
    4: "Пятница", 5: "Суббота", 6: "Воскресенье"
}

@router.post("/", response_model=AttendanceResponse)
async def mark_attendance(
    attendance_in: AttendanceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user = Depends(allow_teacher)
):
    # 1. Проверки существования
    student = await db.get(Student, attendance_in.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2. ПРОВЕРКА ВРЕМЕНИ (Если это учитель)
    if current_user.role == "TEACHER":
        today_date = datetime.now().date()
        
        # Только сегодня
        if attendance_in.date != today_date:
            raise HTTPException(status_code=400, detail="Отмечать посещаемость можно только день в день")

        # Ищем урок в расписании, чтобы узнать время начала
        # Нам нужно узнать предмет? Attendance не привязан к предмету напрямую в БД, 
        # но логически мы отмечаем на уроке. 
        # Упрощение: Проверяем, есть ли ХОТЬ ОДИН урок у этого учителя с этим классом сейчас.
        
        now = datetime.now()
        current_day_name = DAYS_MAPPING[now.weekday()]
        current_time_str = now.strftime("%H:%M")

        # Ищем любой урок этого учителя у этого класса на сегодня
        query = select(Schedule).filter(
            Schedule.class_group_id == student.class_group_id,
            Schedule.teacher_id == current_user.id,
            Schedule.day_of_week == current_day_name
        )
        result = await db.execute(query)
        lessons = result.scalars().all()

        if not lessons:
             raise HTTPException(status_code=403, detail="У вас нет уроков с этим классом сегодня")

        # Проверяем, начался ли хоть один из этих уроков
        # (Если уроков несколько подряд, разрешаем с начала первого)
        lesson_started = False
        for lesson in lessons:
            if current_time_str >= lesson.start_time:
                lesson_started = True
                break
        
        if not lesson_started:
            raise HTTPException(status_code=400, detail="Урок еще не начался, отмечать нельзя")


    # 3. Логика сохранения (без изменений)
    query = select(Attendance).filter(
        Attendance.student_id == attendance_in.student_id,
        Attendance.date == attendance_in.date
    )
    result = await db.execute(query)
    existing_record = result.scalars().first()

    if existing_record:
        existing_record.status = attendance_in.status
        await db.commit()
        await db.refresh(existing_record)
        return existing_record

    new_attendance = Attendance(
        student_id=attendance_in.student_id,
        date=attendance_in.date,
        status=attendance_in.status
    )
    db.add(new_attendance)
    await db.commit()
    await db.refresh(new_attendance)
    return new_attendance

@router.get("/", response_model=list[AttendanceResponse])
async def get_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(get_current_user),
    class_id: int | None = None,
    check_date: date | None = None
):
    """
    Получить список посещаемости.
    Можно фильтровать по классу и дате.
    """
    query = select(Attendance)

    # Если указан класс - нужно сделать JOIN (соединение таблиц), 
    # так как в таблице посещаемости нет class_id, он есть только у ученика
    if class_id:
        query = query.join(Student).filter(Student.class_group_id == class_id)
    
    # Фильтр по дате
    if check_date:
        query = query.filter(Attendance.date == check_date)

    result = await db.execute(query)
    return result.scalars().all()