from pydantic import BaseModel, ConfigDict
from datetime import date   

# --- Схемы для Классов (ClassGroup) ---

class ClassGroupBase(BaseModel):
    name: str  # Например: "11-B"

class ClassGroupCreate(ClassGroupBase):
    pass

class ClassGroupResponse(ClassGroupBase):
    id: int
    
    # Разрешаем Pydantic читать данные из SQLAlchemy моделей
    model_config = ConfigDict(from_attributes=True)


# --- Схемы для Учеников (Student) ---

class StudentBase(BaseModel):
    full_name: str

class StudentCreate(StudentBase):
    class_group_id: int  # При создании указываем ID класса

class StudentResponse(StudentBase):
    id: int
    class_group_id: int
    
    model_config = ConfigDict(from_attributes=True)

class AttendanceBase(BaseModel):
    date: date
    status: str  # "PRESENT", "ABSENT", "LATE"

class AttendanceCreate(AttendanceBase):
    student_id: int

class AttendanceResponse(AttendanceBase):
    id: int
    student_id: int
    
    model_config = ConfigDict(from_attributes=True)

# ... (код Attendance был выше) ...

# --- Предметы (Subjects) ---
class SubjectCreate(BaseModel):
    name: str

class SubjectResponse(SubjectCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Оценки (Grades) ---
class GradeCreate(BaseModel):
    value: int        # Сама оценка (например, 5)
    student_id: int
    subject_id: int
    date: date

class GradeResponse(GradeCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ... (код Grade был выше) ...

# --- Расписание (Schedule) ---
class ScheduleCreate(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    room_number: str
    class_group_id: int
    subject_id: int
    teacher_id: int # <--- Добавили поле

class ScheduleResponse(ScheduleCreate):
    id: int

    teacher_id: int | None = None
    
    subject_name: str | None = None 
    class_group_name: str | None = None
    teacher_name: str | None = None # <--- Чтобы красиво выводить имя учителя

    model_config = ConfigDict(from_attributes=True)

# --- ЗВОНКИ ---
class BellCreate(BaseModel):
    order: int
    start_time: str
    end_time: str

class BellResponse(BellCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)