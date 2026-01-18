import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# 1. Импортируем Базу и Модели
from app.db.session import engine
from app.db.base import Base

# Импортируем модели, чтобы SQLAlchemy знала о них перед созданием таблиц
from app.models.user import User
from app.models.school import Student, ClassGroup, Schedule, Grade, Attendance, Subject, BellSchedule

# 2. Импортируем Роутеры (Разделы сайта)
from app.api import (
    auth,       # Вход/Регистрация
    classes,    # Управление классами
    students,   # Управление учениками
    schedule,   # Расписание
    grades,     # Оценки
    attendance, # Посещаемость
    reports,    # Отчеты
    settings    # Настройки (звонки, предметы)
)

app = FastAPI(title="School CRM")

# --- 3. Подключаем Статику (CSS, JS) ---
static_dir = "app/static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- 4. Настройка Шаблонов (HTML) ---
templates = Jinja2Templates(directory="app/templates")

# --- 5. Подключаем API Маршруты ---
app.include_router(auth.router) # Префикс /auth уже внутри
app.include_router(classes.router, prefix="/classes", tags=["Classes"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(grades.router, prefix="/grades", tags=["Grades"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

# --- 6. Создание таблиц при старте ---
@app.on_event("startup")
async def init_tables():
    print(">>> 🛠️ ПРОВЕРКА БАЗЫ ДАННЫХ: Создание таблиц, если их нет...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(">>> ✅ БАЗА ДАННЫХ ГОТОВА!")

# --- 7. Страницы (Frontend) ---
@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard")
async def dashboard_page(request: Request):
    # Данные пользователя подгрузятся через JS (fetch /auth/me)
    # Здесь просто отдаем каркас страницы
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": {"email": "Loading...", "role": "GUEST"}, 
        "users": []
    })