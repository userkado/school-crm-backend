from app.db.base import Base  # <--- ВОТ ЭТОЙ СТРОКИ НЕ ХВАТАЛО
from app.models.user import User
from app.models.school import ClassGroup, Student, Attendance