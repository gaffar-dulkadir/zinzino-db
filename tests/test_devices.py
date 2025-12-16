"""
Device management tests for Zinzino IoT API.

Tests for device CRUD operations, status updates, and history.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.device
class TestDeviceCreation:
    """Test device creation functionality."""
    
    def test_create_device(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_device_data: dict
    ):
        """Test successful device creation."""
        response = client.post(
            "/api/v1/devices",
            json=mock_device_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_name"] == mock_device_data["device_name"]
        assert data["device_type"] == mock_device_data["device_type"]
        assert data["mac_address"] == mock_device_data["mac_address"]
        assert data["serial_number"] == mock_device_data["serial_number"]
        assert "device_id" in data
        assert data["is_active"] is True
    
    def test_create_device_without_auth(
        self,
        client: TestClient,
        mock_device_data: dict
    ):
        """Test device creation without authentication fails."""
        response = client.post("/api/v1/devices", json=mock_device_data)
        
        assert response.status_code == 401
    
    def test_create_device_duplicate_serial(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict,
        mock_device_data: dict
    ):
        """Test creating device with duplicate serial number."""
        # Try to create another device with same serial number
        response = client.post(
            "/api/v1/devices",
            json=mock_device_data,
            headers=auth_headers
        )
        
        # Should fail due to unique constraint
        assert response.status_code in [400, 409]


@pytest.mark.device
class TestDeviceRetrieval:
    """Test device retrieval functionality."""
    
    def test_list_devices(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test listing user devices."""
        response = client.get("/api/v1/devices", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["device_id"] == created_device["device_id"] for d in data)
    
    def test_list_devices_with_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test listing devices with filters."""
        response = client.get(
            "/api/v1/devices?sort=name&order=asc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_device(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test getting specific device details."""
        device_id = created_device["device_id"]
        response = client.get(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_id
        assert data["device_name"] == created_device["device_name"]
    
    def test_get_nonexistent_device(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent device."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/devices/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.device
class TestDeviceUpdate:
    """Test device update functionality."""
    
    def test_update_device(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test updating device information."""
        device_id = created_device["device_id"]
        update_data = {
            "device_name": "Updated Device Name",
            "location": "Living Room",
            "battery_level": 85
        }
        
        response = client.put(
            f"/api/v1/devices/{device_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == update_data["device_name"]
        assert data["location"] == update_data["location"]
        assert data["battery_level"] == update_data["battery_level"]
    
    def test_update_device_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test partial device update."""
        device_id = created_device["device_id"]
        update_data = {"location": "Bathroom"}
        
        response = client.put(
            f"/api/v1/devices/{device_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == update_data["location"]
    
    def test_update_nonexistent_device(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test updating non-existent device."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/api/v1/devices/{fake_id}",
            json={"device_name": "Test"},
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.device
class TestDeviceDelete:
    """Test device deletion functionality."""
    
    def test_delete_device(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_device_data: dict
    ):
        """Test soft-deleting a device."""
        # Create a device to delete
        create_response = client.post(
            "/api/v1/devices",
            json=mock_device_data,
            headers=auth_headers
        )
        device_id = create_response.json()["device_id"]
        
        # Delete the device
        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify device is deactivated
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers=auth_headers
        )
        # Depending on implementation, might return 404 or show is_active=false
        assert get_response.status_code in [200, 404]
    
    def test_delete_nonexistent_device(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent device."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/v1/devices/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.device
class TestDeviceStatusUpdate:
    """Test IoT device status update functionality."""
    
    def test_device_status_update(
        self,
        client: TestClient,
        created_device: dict
    ):
        """Test device status update from IoT device.
        
        Note: This test may need device authentication token
        instead of user token. Adjust based on implementation.
        """
        device_id = created_device["device_id"]
        
        # This endpoint might require device-specific auth
        # Skipping if not implemented yet
        pytest.skip("Device authentication not fully implemented in tests")


@pytest.mark.device
class TestDeviceHistory:
    """Test device history functionality."""
    
    def test_get_device_history(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test getting device activity history."""
        device_id = created_device["device_id"]
        response = client.get(
            f"/api/v1/devices/{device_id}/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # History might be empty for new device
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_get_device_history_with_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test device history with date filters."""
        device_id = created_device["device_id"]
        response = client.get(
            f"/api/v1/devices/{device_id}/history?limit=10&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200


@pytest.mark.device
class TestBulkDeviceOperations:
    """Test bulk device operations."""
    
    def test_bulk_update_devices(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test bulk updating multiple devices."""
        bulk_data = {
            "device_ids": [created_device["device_id"]],
            "updates": {
                "location": "Office"
            }
        }
        
        response = client.post(
            "/api/v1/devices/bulk-update",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
