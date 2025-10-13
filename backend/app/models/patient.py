from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, func
from app.db import Base


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    
    medical_identifier: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(320))
    last_name: Mapped[str] = mapped_column(String(320))
    rut: Mapped[str] = mapped_column(String(320))
    birth_date: Mapped[Date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(320))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())