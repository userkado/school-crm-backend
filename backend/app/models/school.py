from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base # <--- Используем Base

class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    students = relationship("Student", back_populates="class_group")
    schedules = relationship("Schedule", back_populates="class_group")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"))

    class_group = relationship("ClassGroup", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)

class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Integer)
    date = Column(Date)
    
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    status = Column(String) 
    student_id = Column(Integer, ForeignKey("students.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True) 

    student = relationship("Student", back_populates="attendance")
    teacher = relationship("User")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    room_number = Column(String)

    class_group_id = Column(Integer, ForeignKey("class_groups.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("users.id")) 

    class_group = relationship("ClassGroup", back_populates="schedules")
    subject = relationship("Subject")
    teacher = relationship("User", back_populates="lessons") 

class BellSchedule(Base):
    __tablename__ = "bell_schedules"

    id = Column(Integer, primary_key=True, index=True)
    order = Column(Integer, unique=True)
    start_time = Column(String)
    end_time = Column(String)

# 👇 ИСПРАВЛЕННЫЙ КЛАСС (FinalGrade(Base))
class FinalGrade(Base):
    __tablename__ = "final_grades"

    id = Column(Integer, primary_key=True, index=True)
    period_name = Column(String) # "1 Четверть", "Годовая"
    value = Column(Integer)      # Оценка (4, 5...)
    
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    student = relationship("Student")
    subject = relationship("Subject")