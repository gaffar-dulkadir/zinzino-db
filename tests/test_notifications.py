"""
Notification tests for Zinzino IoT API.

Tests for notification creation, retrieval, filtering, and statistics.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.notification
class TestNotificationCreation:
    """Test notification creation functionality."""
    
    def test_create_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_notification_data: dict
    ):
        """Test creating a notification."""
        response = client.post(
            "/api/v1/notifications",
            json=mock_notification_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == mock_notification_data["type"]
        assert data["title"] == mock_notification_data["title"]
        assert data["message"] == mock_notification_data["message"]
        assert "notification_id" in data
        assert data["is_read"] is False
    
    def test_create_notification_without_auth(
        self,
        client: TestClient,
        mock_notification_data: dict
    ):
        """Test creating notification without authentication fails."""
        response = client.post(
            "/api/v1/notifications",
            json=mock_notification_data
        )
        
        assert response.status_code == 401
    
    def test_create_notification_with_device(
        self,
        client: TestClient,
        auth_headers: dict,
        created_device: dict
    ):
        """Test creating notification linked to a device."""
        notification_data = {
            "type": "low_battery",
            "title": "Low Battery Alert",
            "message": "Device battery is below 20%",
            "device_id": created_device["device_id"],
            "metadata": {"battery_level": 15}
        }
        
        response = client.post(
            "/api/v1/notifications",
            json=notification_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == created_device["device_id"]


@pytest.mark.notification
class TestNotificationRetrieval:
    """Test notification retrieval functionality."""
    
    def test_list_notifications(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test listing user notifications."""
        response = client.get("/api/v1/notifications", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data or isinstance(data, list)
    
    def test_list_notifications_with_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test listing notifications with filters."""
        response = client.get(
            "/api/v1/notifications?is_read=false&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_list_notifications_by_type(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test filtering notifications by type."""
        response = client.get(
            f"/api/v1/notifications?type={created_notification['type']}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned notifications match type
        if isinstance(data, list):
            for notif in data:
                assert notif["type"] == created_notification["type"]
    
    def test_get_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test getting specific notification."""
        notification_id = created_notification["notification_id"]
        response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notification_id"] == notification_id
    
    def test_get_nonexistent_notification(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent notification."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/notifications/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.notification
class TestNotificationMarkAsRead:
    """Test marking notifications as read."""
    
    def test_mark_notification_as_read(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test marking a notification as read."""
        notification_id = created_notification["notification_id"]
        response = client.put(
            f"/api/v1/notifications/{notification_id}/read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        assert "read_at" in data
    
    def test_mark_all_notifications_as_read(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test marking all notifications as read."""
        response = client.post(
            "/api/v1/notifications/mark-all-read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "marked_count" in data
        assert data["marked_count"] >= 0
    
    def test_bulk_mark_notifications_as_read(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test bulk marking notifications as read."""
        bulk_data = {
            "notification_ids": [created_notification["notification_id"]]
        }
        
        response = client.post(
            "/api/v1/notifications/bulk-mark-read",
            json=bulk_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "marked_count" in data
        assert data["marked_count"] >= 1


@pytest.mark.notification
class TestNotificationStatistics:
    """Test notification statistics functionality."""
    
    def test_get_unread_count(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test getting unread notification count."""
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        assert data["unread_count"] >= 1  # At least the created notification
    
    def test_get_notification_stats(
        self,
        client: TestClient,
        auth_headers: dict,
        created_notification: dict
    ):
        """Test getting notification statistics."""
        response = client.get(
            "/api/v1/notifications/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "total_count" in data
        assert "unread_count" in data
        
        # Might include type breakdown
        if "by_type" in data:
            assert isinstance(data["by_type"], dict)


@pytest.mark.notification
class TestNotificationDelete:
    """Test notification deletion functionality."""
    
    def test_delete_notification(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_notification_data: dict
    ):
        """Test deleting a notification."""
        # Create a notification to delete
        create_response = client.post(
            "/api/v1/notifications",
            json=mock_notification_data,
            headers=auth_headers
        )
        notification_id = create_response.json()["notification_id"]
        
        # Delete the notification
        response = client.delete(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify notification is deleted
        get_response = client.get(
            f"/api/v1/notifications/{notification_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_notification(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent notification."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/v1/notifications/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.notification
class TestNotificationPagination:
    """Test notification pagination."""
    
    def test_notifications_pagination(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test notification list pagination."""
        # Create multiple notifications
        for i in range(5):
            notification_data = {
                "type": "reminder",
                "title": f"Test Notification {i}",
                "message": f"Message {i}"
            }
            client.post(
                "/api/v1/notifications",
                json=notification_data,
                headers=auth_headers
            )
        
        # Test pagination
        response = client.get(
            "/api/v1/notifications?limit=3&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination
        if isinstance(data, dict) and "notifications" in data:
            assert len(data["notifications"]) <= 3
        elif isinstance(data, list):
            assert len(data) <= 3
