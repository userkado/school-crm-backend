from typing import Annotated, List, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.school import Grade, Student, Schedule, FinalGrade
from app.api.deps import allow_teacher, get_current_user

router = APIRouter()

# --- СХЕМЫ ---
class GradeCreate(BaseModel):
    value: int
    student_id: int
    subject_id: int
    date: date

class FinalGradeCreate(BaseModel):
    period_name: str # "Q1", "Q2", "YEAR"
    value: int
    student_id: int
    subject_id: int

# --- 1. ОБЫЧНАЯ ОЦЕНКА (УРОК) ---
@router.post("/")
async def create_grade(
    grade_in: GradeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_teacher)
):
    # Ищем, есть ли уже оценка у этого ученика по этому предмету в эту дату
    q = select(Grade).filter(
        Grade.student_id == grade_in.student_id,
        Grade.subject_id == grade_in.subject_id,
        Grade.date == grade_in.date
    )
    res = await db.execute(q)
    existing_grade = res.scalars().first()

    if existing_grade:
        existing_grade.value = grade_in.value # Обновляем
    else:
        new_grade = Grade(**grade_in.model_dump())
        db.add(new_grade)
    
    await db.commit()
    return {"ok": True}

# --- 2. ИТОГОВАЯ ОЦЕНКА (ЧЕТВЕРТЬ) ---
@router.post("/final")
async def set_final_grade(
    data: FinalGradeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_teacher)
):
    # Ищем старую итоговую
    q = select(FinalGrade).filter(
        FinalGrade.student_id == data.student_id,
        FinalGrade.subject_id == data.subject_id,
        FinalGrade.period_name == data.period_name
    )
    res = await db.execute(q)
    existing = res.scalars().first()

    if existing:
        existing.value = data.value
    else:
        new_final = FinalGrade(
            student_id=data.student_id,
            subject_id=data.subject_id,
            period_name=data.period_name,
            value=data.value
        )
        db.add(new_final)
    
    await db.commit()
    return {"ok": True}

# --- 3. ПОЛУЧЕНИЕ МАТРИЦЫ (СВОДНЫЙ ЖУРНАЛ) ---
@router.get("/matrix")
async def get_grades_matrix(
    class_id: int,
    subject_id: int,
    period_name: str, # Например "Q1" (нужно для загрузки итоговых)
    db: Annotated[AsyncSession, Depends(get_db)],
    _ = Depends(allow_teacher)
):
    # A. Получаем всех учеников класса
    res_st = await db.execute(select(Student).filter(Student.class_group_id == class_id).order_by(Student.full_name))
    students = res_st.scalars().all()

    # B. Получаем все даты уроков (из расписания или из оценок)
    # Для простоты возьмем уникальные даты из таблицы оценок по этому предмету + даты из расписания
    # Но проще всего взять просто все оценки
    res_grades = await db.execute(select(Grade).filter(Grade.subject_id == subject_id))
    all_grades = res_grades.scalars().all()

    # Собираем уникальные даты уроков (сортируем)
    dates = sorted(list(set([g.date.isoformat() for g in all_grades])))

    # C. Получаем итоговые оценки за этот период
    res_finals = await db.execute(select(FinalGrade).filter(FinalGrade.subject_id == subject_id, FinalGrade.period_name == period_name))
    all_finals = res_finals.scalars().all()

    # D. Собираем структуру данных
    matrix = []
    for s in students:
        student_grades = {}
        total_sum = 0
        count = 0
        
        # Оценки по датам
        for g in all_grades:
            if g.student_id == s.id:
                student_grades[g.date.isoformat()] = g.value
                total_sum += g.value
                count += 1
        
        # Средний балл
        avg = round(total_sum / count, 2) if count > 0 else 0
        
        # Итоговая оценка
        final_g = next((f.value for f in all_finals if f.student_id == s.id), None)

        matrix.append({
            "student_id": s.id,
            "full_name": s.full_name,
            "grades": student_grades, # Словарь {"2026-01-15": 5, "2026-01-16": 4}
            "average": avg,
            "final_grade": final_g
        })

    return {
        "dates": dates, # Заголовки колонок
        "students": matrix
    }