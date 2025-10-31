"""
Tests for patient endpoints.
"""
import pytest
from datetime import date


class TestGetPatients:
    """Tests for GET /patients/ endpoint."""
    
    async def test_list_patients_empty(self, client):
        """Test listing patients when database is empty."""
        response = await client.get("/patients/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    async def test_create_and_list_patient(self, client):
        """Test creating a patient and then listing patients."""
        # Create a patient
        patient_data = {
            "medical_identifier": "MED001",
            "first_name": "John",
            "last_name": "Doe",
            "rut": "12345678-9",
            "birth_date": "1990-01-15",
            "gender": "M"
        }
        
        # POST to create patient
        create_response = await client.post("/patients/", json=patient_data)
        assert create_response.status_code == 200
        
        created_patient = create_response.json()
        assert created_patient["first_name"] == "John"
        assert created_patient["last_name"] == "Doe"
        assert created_patient["rut"] == "12345678-9"
        assert created_patient["medical_identifier"] == "MED001"
        assert "id" in created_patient
        
        # GET to list patients
        list_response = await client.get("/patients/")
        assert list_response.status_code == 200
        
        patients = list_response.json()
        assert len(patients) == 1
        assert patients[0]["first_name"] == "John"
        assert patients[0]["last_name"] == "Doe"

