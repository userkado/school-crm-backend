from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

# Импорты для базы данных
from app.db.session import engine
from app.db.base import Base
# 👇 ВАЖНО: Импортируем модели, чтобы SQLAlchemy узнала о них перед созданием таблиц
from app.models import user, school 

from app.core.config import settings
from app.api import auth, classes, students, attendance, grades, schedule, reports
from app.api import settings as school_settings 

app = FastAPI(title="School CRM")

# --- 1. СОЗДАНИЕ ТАБЛИЦ ПРИ ЗАПУСКЕ ---
@app.on_event("startup")
async def init_tables():
    print(">>> 🛠️ ПРОВЕРКА БАЗЫ ДАННЫХ: Создание таблиц, если их нет...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(">>> ✅ БАЗА ДАННЫХ ГОТОВА!")

# --- 2. НАСТРОЙКА CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = "app/static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# --- 3. СТАТИКА И ШАБЛОНЫ ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- 4. РОУТЕРЫ ---
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(classes.router, prefix="/classes", tags=["Classes"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(grades.router, prefix="/grades", tags=["Grades"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(school_settings.router, prefix="/settings", tags=["School Settings"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

# --- 5. СТРАНИЦЫ ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})