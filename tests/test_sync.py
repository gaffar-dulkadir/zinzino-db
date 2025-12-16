"""
Synchronization tests for Zinzino IoT API.

Tests for full sync, delta sync, and sync status.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


@pytest.mark.sync
class TestFullSync:
    """Test full synchronization functionality."""
    
    def test_full_sync(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test full sync returns all user data."""
        sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "include_deleted": False
        }
        
        response = client.post(
            "/api/v1/sync/full",
            json=sync_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "sync_id" in data
        assert "devices" in data
        assert "notifications" in data
        assert "sync_timestamp" in data
        assert "sync_status" in data
        
        # Verify devices are included
        assert isinstance(data["devices"], list)
        assert any(d["device_id"] == created_device["device_id"] for d in data["devices"])
    
    def test_full_sync_include_deleted(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test full sync with deleted records."""
        sync_data = {
            "device_info": {
                "platform": "android",
                "app_version": "1.0.0",
                "os_version": "14.0",
                "device_model": "Samsung Galaxy S24"
            },
            "include_deleted": True
        }
        
        response = client.post(
            "/api/v1/sync/full",
            json=sync_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
    
    def test_full_sync_without_auth(self, client: TestClient):
        """Test full sync without authentication fails."""
        sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            }
        }
        
        response = client.post("/api/v1/sync/full", json=sync_data)
        
        assert response.status_code == 401


@pytest.mark.sync
class TestDeltaSync:
    """Test delta (incremental) synchronization functionality."""
    
    def test_delta_sync(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test delta sync returns only changes since last sync."""
        # First, do a full sync to get timestamp
        full_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            }
        }
        full_response = client.post(
            "/api/v1/sync/full",
            json=full_sync_data,
            headers=auth_headers
        )
        last_sync_timestamp = full_response.json()["sync_timestamp"]
        
        # Now do delta sync
        delta_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "last_sync_timestamp": last_sync_timestamp
        }
        
        response = client.post(
            "/api/v1/sync/delta",
            json=delta_sync_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify delta response structure
        assert "sync_id" in data
        assert "devices_updated" in data
        assert "devices_deleted" in data
        assert "notifications_new" in data
        assert "sync_timestamp" in data
        assert "sync_status" in data
    
    def test_delta_sync_with_changes(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test delta sync after making changes."""
        # Get initial sync timestamp
        full_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            }
        }
        full_response = client.post(
            "/api/v1/sync/full",
            json=full_sync_data,
            headers=auth_headers
        )
        last_sync_timestamp = full_response.json()["sync_timestamp"]
        
        # Make a change (update device)
        device_id = created_device["device_id"]
        client.put(
            f"/api/v1/devices/{device_id}",
            json={"device_name": "Updated Name"},
            headers=auth_headers
        )
        
        # Delta sync should show the change
        delta_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "last_sync_timestamp": last_sync_timestamp
        }
        
        response = client.post(
            "/api/v1/sync/delta",
            json=delta_sync_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have updated devices
        assert "devices_updated" in data
    
    def test_delta_sync_old_timestamp(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test delta sync with very old timestamp."""
        # Use timestamp from 30 days ago
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        delta_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "last_sync_timestamp": old_timestamp
        }
        
        response = client.post(
            "/api/v1/sync/delta",
            json=delta_sync_data,
            headers=auth_headers
        )
        
        # Should succeed or recommend full sync
        assert response.status_code == 200
    
    def test_delta_sync_without_auth(self, client: TestClient):
        """Test delta sync without authentication fails."""
        delta_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "last_sync_timestamp": datetime.utcnow().isoformat()
        }
        
        response = client.post("/api/v1/sync/delta", json=delta_sync_data)
        
        assert response.status_code == 401


@pytest.mark.sync
class TestSyncStatus:
    """Test sync status functionality."""
    
    def test_get_sync_status(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting sync status."""
        response = client.get("/api/v1/sync/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify status structure
        assert "last_full_sync" in data or "last_sync_timestamp" in data
    
    def test_get_sync_status_after_sync(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test sync status after performing a sync."""
        # Perform full sync
        sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            }
        }
        client.post("/api/v1/sync/full", json=sync_data, headers=auth_headers)
        
        # Get status
        response = client.get("/api/v1/sync/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have recent sync info
        assert data is not None
    
    def test_get_sync_status_without_auth(self, client: TestClient):
        """Test getting sync status without authentication fails."""
        response = client.get("/api/v1/sync/status")
        
        assert response.status_code == 401


@pytest.mark.sync
class TestSyncConflicts:
    """Test sync conflict handling."""
    
    def test_delta_sync_with_client_changes(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test delta sync with client-side changes."""
        # This tests conflict detection/resolution
        delta_sync_data = {
            "device_info": {
                "platform": "ios",
                "app_version": "1.0.0",
                "os_version": "17.0",
                "device_model": "iPhone 15"
            },
            "last_sync_timestamp": datetime.utcnow().isoformat(),
            "client_changes": {
                "devices_modified": [],
                "notifications_read": []
            }
        }
        
        response = client.post(
            "/api/v1/sync/delta",
            json=delta_sync_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Conflicts field might be present
        if "conflicts" in data:
            assert isinstance(data["conflicts"], list)
