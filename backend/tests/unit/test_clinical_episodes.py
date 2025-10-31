"""
Tests for clinical episode endpoints.
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime

from tests.test_fixtures import (
    create_test_patient,
    create_test_bed,
    create_test_clinical_episode
)


class TestListClinicalEpisodes:
    """Tests for GET /clinical-episodes/ endpoint."""
    
    async def test_list_episodes_empty(self, client):
        """Test listing episodes when database is empty."""
        response = await client.get("/clinical-episodes/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 50
    
    async def test_list_episodes_with_data(self, client, test_session):
        """Test listing episodes when data exists."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        bed = await create_test_bed(test_session, "101")
        episode1 = await create_test_clinical_episode(test_session, patient.id, bed.id)
        episode2 = await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        response = await client.get("/clinical-episodes/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["data"]) == 2
    
    async def test_list_episodes_with_pagination(self, client, test_session):
        """Test pagination works correctly."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        # Create 3 episodes
        for i in range(3):
            await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        # First page
        response = await client.get("/clinical-episodes/", params={"page": 1, "page_size": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["total"] == 3
        
        # Second page
        response = await client.get("/clinical-episodes/", params={"page": 2, "page_size": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["page"] == 2
    
    async def test_list_episodes_with_search_by_first_name(self, client, test_session):
        """Test search by patient first name."""
        patient1 = await create_test_patient(test_session, "MED001", "John", "Doe")
        patient2 = await create_test_patient(test_session, "MED002", "Jane", "Smith")
        await create_test_clinical_episode(test_session, patient1.id)
        await create_test_clinical_episode(test_session, patient2.id)
        await test_session.commit()
        
        response = await client.get("/clinical-episodes/", params={"search": "John"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
    
    async def test_list_episodes_with_search_by_last_name(self, client, test_session):
        """Test search by patient last name."""
        patient1 = await create_test_patient(test_session, "MED001", "John", "Doe")
        patient2 = await create_test_patient(test_session, "MED002", "Jane", "Smith")
        await create_test_clinical_episode(test_session, patient1.id)
        await create_test_clinical_episode(test_session, patient2.id)
        await test_session.commit()
        
        response = await client.get("/clinical-episodes/", params={"search": "Smith"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
    
    async def test_list_episodes_with_search_by_room(self, client, test_session):
        """Test search by room number."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        bed1 = await create_test_bed(test_session, "101")
        bed2 = await create_test_bed(test_session, "202")
        await create_test_clinical_episode(test_session, patient.id, bed1.id)
        await create_test_clinical_episode(test_session, patient.id, bed2.id)
        await test_session.commit()
        
        response = await client.get("/clinical-episodes/", params={"search": "101"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
    
    async def test_list_episodes_with_include_patient(self, client, test_session):
        """Test including patient data in response."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        response = await client.get("/clinical-episodes/", params={"include": "patient"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "patient" in data["data"][0]
        assert data["data"][0]["patient"]["first_name"] == "John"
    
    async def test_list_episodes_invalid_page(self, client):
        """Test pagination with invalid page number."""
        response = await client.get("/clinical-episodes/", params={"page": 0})
        
        assert response.status_code == 400
        assert "Page must be >= 1" in response.json()["detail"]
    
    async def test_list_episodes_invalid_page_size(self, client):
        """Test pagination with invalid page size."""
        response = await client.get("/clinical-episodes/", params={"page_size": 0})
        
        assert response.status_code == 400
        assert "Page size must be between 1 and 100" in response.json()["detail"]
        
        response = await client.get("/clinical-episodes/", params={"page_size": 101})
        
        assert response.status_code == 400
        assert "Page size must be between 1 and 100" in response.json()["detail"]


class TestGetClinicalEpisode:
    """Tests for GET /clinical-episodes/{episode_id} endpoint."""
    
    async def test_get_episode_success(self, client, test_session):
        """Test successfully getting an episode."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        episode = await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        response = await client.get(f"/clinical-episodes/{episode.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(episode.id)
        assert data["patient_id"] == str(patient.id)
    
    async def test_get_episode_with_include_patient(self, client, test_session):
        """Test getting an episode with patient data included."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        episode = await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        response = await client.get(
            f"/clinical-episodes/{episode.id}",
            params={"include": "patient"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(episode.id)
        assert "patient" in data
        assert data["patient"]["first_name"] == "John"
    
    async def test_get_episode_not_found(self, client):
        """Test getting a non-existent episode."""
        fake_id = uuid4()
        response = await client.get(f"/clinical-episodes/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_episode_invalid_uuid(self, client):
        """Test getting an episode with invalid UUID."""
        response = await client.get("/clinical-episodes/invalid-uuid")
        
        assert response.status_code == 422


class TestGetEpisodeHistory:
    """Tests for GET /clinical-episodes/{episode_id}/history endpoint."""
    
    async def test_get_episode_history_success(self, client, test_session):
        """Test successfully getting episode history."""
        patient = await create_test_patient(test_session, "MED001", "John", "Doe")
        episode = await create_test_clinical_episode(test_session, patient.id)
        await test_session.commit()
        
        response = await client.get(f"/clinical-episodes/{episode.id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["episode_id"] == str(episode.id)
        assert "events" in data
        assert isinstance(data["events"], list)
        # Should have at least the admission event
        assert len(data["events"]) >= 1
    
    async def test_get_episode_history_not_found(self, client):
        """Test getting history for non-existent episode."""
        fake_id = uuid4()
        response = await client.get(f"/clinical-episodes/{fake_id}/history")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_episode_history_invalid_uuid(self, client):
        """Test getting history with invalid UUID."""
        response = await client.get("/clinical-episodes/invalid-uuid/history")
        
        assert response.status_code == 422

