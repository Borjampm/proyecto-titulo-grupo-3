from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatientBase(BaseModel):
    medical_identifier: str
    first_name: str
    last_name: str
    rut: str
    birth_date: date
    gender: str


class PatientCreate(PatientBase):
    pass


class Patient(PatientBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
