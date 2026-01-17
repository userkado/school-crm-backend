from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship # <--- Убедитесь, что это импортировано
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="STUDENT")
    is_active = Column(Boolean, default=True)

    # 👇 ВОТ ЭТА СТРОКА, КОТОРОЙ НЕ ХВАТАЛО
    lessons = relationship("Schedule", back_populates="teacher")