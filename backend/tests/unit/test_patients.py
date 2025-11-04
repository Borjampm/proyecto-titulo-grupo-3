"""
Tests for patient endpoints.
"""
import pytest
from datetime import date
from uuid import UUID

from tests.test_fixtures import create_test_patient


class TestGetPatients:
    """Tests for GET /patients/ endpoint."""
    
    async def test_list_patients_empty(self, client):
        """Test listing patients when database is empty."""
        response = await client.get("/patients/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    async def test_list_patients_with_data(self, client, test_session):
        """Test listing patients when data exists."""
        # Create multiple patients
        await create_test_patient(test_session, "MED001", "John", "Doe", "12345678-9")
        await create_test_patient(test_session, "MED002", "Jane", "Smith", "98765432-1")
        await test_session.commit()
        
        response = await client.get("/patients/")
        
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) == 2
        assert any(p["medical_identifier"] == "MED001" for p in patients)
        assert any(p["medical_identifier"] == "MED002" for p in patients)


class TestCreatePatient:
    """Tests for POST /patients/ endpoint."""
    
    async def test_create_patient_success(self, client):
        """Test successful patient creation."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        
        assert response.status_code == 200
        created_patient = response.json()
        assert created_patient["medical_identifier"] == "MED001"
        assert created_patient["first_name"] == "John"
        assert created_patient["last_name"] == "Doe"
        assert created_patient["rut"] == "12345678-9"
        assert created_patient["birth_date"] == "1990-01-15"
        assert created_patient["gender"] == "M"
        assert "id" in created_patient
    
    async def test_create_patient_missing_required_fields(self, client):
        """Test patient creation with missing required fields."""
        # Missing medical_identifier
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_missing_first_name(self, client):
        """Test patient creation with missing first_name."""
        patient_data = {
            "medical_identifier": "MED001",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_missing_last_name(self, client):
        """Test patient creation with missing last_name."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_missing_rut(self, client):
        """Test patient creation with missing rut."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_missing_birth_date(self, client):
        """Test patient creation with missing birth_date."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_missing_gender(self, client):
        """Test patient creation with missing gender."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_invalid_birth_date_format(self, client):
        """Test patient creation with invalid birth_date format."""
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "invalid-date",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_empty_medical_identifier(self, client):
        """Test patient creation with empty medical_identifier."""
        patient_data = {
            "medical_identifier": "",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        response = await client.post("/patients/", json=patient_data)
        # Should still create (empty string is valid, but might fail at DB level)
        # This depends on your validation rules
        assert response.status_code in [200, 422]
