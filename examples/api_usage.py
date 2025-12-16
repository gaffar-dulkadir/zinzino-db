"""
Zinzino IoT API Usage Examples

This module demonstrates how to use the Zinzino IoT API with Python.
It covers authentication, device management, notifications, and synchronization.

Requirements:
    pip install requests python-dotenv

Usage:
    python examples/api_usage.py
"""

import requests
from typing import Optional, Dict, Any
import json
from datetime import datetime


class ZinzinoAPIClient:
    """Client for interacting with Zinzino IoT API."""
    
    def __init__(self, base_url: str = "http://localhost:8080/api/v1"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
    
    # Authentication Methods
    
    def register(self, email: str, password: str, full_name: str,
                phone: Optional[str] = None, language: str = "en",
                timezone: str = "Europe/Istanbul") -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            full_name: User's full name
            phone: Phone number (optional)
            language: Preferred language (default: en)
            timezone: User timezone (default: Europe/Istanbul)
            
        Returns:
            Registration response with tokens
        """
        url = f"{self.base_url}/auth/register"
        data = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "phone": phone,
            "language": language,
            "timezone": timezone
        }
        
        response = requests.post(url, json=data)
        result = self._handle_response(response)
        
        # Store tokens
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        
        return result
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Login response with tokens
        """
        url = f"{self.base_url}/auth/login"
        data = {"email": email, "password": password}
        
        response = requests.post(url, json=data)
        result = self._handle_response(response)
        
        # Store tokens
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        
        return result
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New tokens
        """
        url = f"{self.base_url}/auth/refresh"
        data = {"refresh_token": self.refresh_token}
        
        response = requests.post(url, json=data)
        result = self._handle_response(response)
        
        # Update tokens
        self.access_token = result.get("access_token")
        self.refresh_token = result.get("refresh_token")
        
        return result
    
    def logout(self) -> Dict[str, Any]:
        """Logout user."""
        url = f"{self.base_url}/auth/logout"
        response = requests.post(url, headers=self._headers())
        result = self._handle_response(response)
        
        # Clear tokens
        self.access_token = None
        self.refresh_token = None
        
        return result
    
    # Device Methods
    
    def create_device(self, device_name: str, device_type: str,
                     mac_address: str, serial_number: str,
                     location: Optional[str] = None,
                     firmware_version: str = "1.0.0") -> Dict[str, Any]:
        """
        Register a new IoT device.
        
        Args:
            device_name: Name for the device
            device_type: Type of device (fish_oil, vitamin_d, krill_oil, vegan)
            mac_address: Device MAC address
            serial_number: Device serial number
            location: Device location (optional)
            firmware_version: Firmware version
            
        Returns:
            Created device information
        """
        url = f"{self.base_url}/devices"
        data = {
            "device_name": device_name,
            "device_type": device_type,
            "mac_address": mac_address,
            "serial_number": serial_number,
            "location": location,
            "firmware_version": firmware_version
        }
        
        response = requests.post(url, json=data, headers=self._headers())
        return self._handle_response(response)
    
    def get_devices(self, include_inactive: bool = False,
                   sort: str = "name", order: str = "asc") -> list:
        """
        Get all user devices.
        
        Args:
            include_inactive: Include inactive devices
            sort: Sort field (name, created_at, type)
            order: Sort order (asc, desc)
            
        Returns:
            List of devices
        """
        url = f"{self.base_url}/devices"
        params = {
            "include_inactive": include_inactive,
            "sort": sort,
            "order": order
        }
        
        response = requests.get(url, params=params, headers=self._headers())
        return self._handle_response(response)
    
    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device by ID."""
        url = f"{self.base_url}/devices/{device_id}"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)
    
    def update_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update device information.
        
        Args:
            device_id: Device UUID
            **kwargs: Fields to update (device_name, location, etc.)
            
        Returns:
            Updated device information
        """
        url = f"{self.base_url}/devices/{device_id}"
        response = requests.put(url, json=kwargs, headers=self._headers())
        return self._handle_response(response)
    
    def delete_device(self, device_id: str) -> None:
        """Delete device."""
        url = f"{self.base_url}/devices/{device_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    def get_device_history(self, device_id: str, limit: int = 50,
                          offset: int = 0) -> Dict[str, Any]:
        """Get device activity history."""
        url = f"{self.base_url}/devices/{device_id}/history"
        params = {"limit": limit, "offset": offset}
        response = requests.get(url, params=params, headers=self._headers())
        return self._handle_response(response)
    
    # Notification Methods
    
    def get_notifications(self, is_read: Optional[bool] = None,
                         notification_type: Optional[str] = None,
                         limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get user notifications.
        
        Args:
            is_read: Filter by read status
            notification_type: Filter by type
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Notifications list
        """
        url = f"{self.base_url}/notifications"
        params = {"limit": limit, "offset": offset}
        
        if is_read is not None:
            params["is_read"] = is_read
        if notification_type:
            params["type"] = notification_type
        
        response = requests.get(url, params=params, headers=self._headers())
        return self._handle_response(response)
    
    def mark_notification_as_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as read."""
        url = f"{self.base_url}/notifications/{notification_id}/read"
        response = requests.put(url, headers=self._headers())
        return self._handle_response(response)
    
    def mark_all_notifications_as_read(self) -> Dict[str, Any]:
        """Mark all notifications as read."""
        url = f"{self.base_url}/notifications/mark-all-read"
        response = requests.post(url, headers=self._headers())
        return self._handle_response(response)
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        url = f"{self.base_url}/notifications/stats"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)
    
    # Synchronization Methods
    
    def full_sync(self, platform: str = "ios", app_version: str = "1.0.0",
                 os_version: str = "17.0", device_model: str = "iPhone 15",
                 include_deleted: bool = False) -> Dict[str, Any]:
        """
        Perform full synchronization.
        
        Args:
            platform: Platform (ios, android)
            app_version: App version
            os_version: OS version
            device_model: Device model
            include_deleted: Include deleted records
            
        Returns:
            Full sync response with all data
        """
        url = f"{self.base_url}/sync/full"
        data = {
            "device_info": {
                "platform": platform,
                "app_version": app_version,
                "os_version": os_version,
                "device_model": device_model
            },
            "include_deleted": include_deleted
        }
        
        response = requests.post(url, json=data, headers=self._headers())
        return self._handle_response(response)
    
    def delta_sync(self, last_sync_timestamp: str,
                  platform: str = "ios", app_version: str = "1.0.0",
                  os_version: str = "17.0", device_model: str = "iPhone 15") -> Dict[str, Any]:
        """
        Perform delta synchronization.
        
        Args:
            last_sync_timestamp: Last sync timestamp (ISO format)
            platform: Platform (ios, android)
            app_version: App version
            os_version: OS version
            device_model: Device model
            
        Returns:
            Delta sync response with changes
        """
        url = f"{self.base_url}/sync/delta"
        data = {
            "device_info": {
                "platform": platform,
                "app_version": app_version,
                "os_version": os_version,
                "device_model": device_model
            },
            "last_sync_timestamp": last_sync_timestamp
        }
        
        response = requests.post(url, json=data, headers=self._headers())
        return self._handle_response(response)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status."""
        url = f"{self.base_url}/sync/status"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)


# Example Usage
def main():
    """Demonstrate API usage."""
    
    # Initialize client
    client = ZinzinoAPIClient()
    
    print("=" * 60)
    print("Zinzino IoT API Examples")
    print("=" * 60)
    
    # 1. Register or Login
    print("\n1. Authentication")
    print("-" * 60)
    
    try:
        # Try to login (change credentials as needed)
        user_email = "demo@example.com"
        user_password = "Demo1234!"
        
        print(f"Logging in as {user_email}...")
        auth_result = client.login(user_email, user_password)
        print(f"✓ Login successful!")
        print(f"  User: {auth_result['user']['full_name']}")
        print(f"  Token expires in: {auth_result.get('expires_in', 'N/A')} seconds")
        
    except requests.exceptions.HTTPError:
        # If login fails, register new user
        print(f"Login failed. Registering new user...")
        auth_result = client.register(
            email=user_email,
            password=user_password,
            full_name="Demo User",
            phone="+905551234567",
            language="en"
        )
        print(f"✓ Registration successful!")
        print(f"  User ID: {auth_result['user']['user_id']}")
    
    # 2. Create Device
    print("\n2. Device Management")
    print("-" * 60)
    
    print("Creating new device...")
    device = client.create_device(
        device_name="My Fish Oil Dispenser",
        device_type="fish_oil",
        mac_address="AA:BB:CC:DD:EE:FF",
        serial_number=f"ZNZ-2024-{datetime.now().timestamp():.0f}",
        location="Kitchen",
        firmware_version="1.0.0"
    )
    print(f"✓ Device created!")
    print(f"  Device ID: {device['device_id']}")
    print(f"  Name: {device['device_name']}")
    print(f"  Type: {device['device_type']}")
    
    device_id = device['device_id']
    
    # 3. List Devices
    print("\nListing all devices...")
    devices = client.get_devices()
    print(f"✓ Found {len(devices)} device(s)")
    for dev in devices:
        print(f"  - {dev['device_name']} ({dev['device_type']})")
    
    # 4. Update Device
    print("\nUpdating device location...")
    updated_device = client.update_device(
        device_id,
        location="Living Room",
        battery_level=85
    )
    print(f"✓ Device updated!")
    print(f"  New location: {updated_device['location']}")
    print(f"  Battery: {updated_device['battery_level']}%")
    
    # 5. Notifications
    print("\n3. Notifications")
    print("-" * 60)
    
    print("Getting notifications...")
    notifications = client.get_notifications(is_read=False)
    notif_list = notifications.get('notifications', notifications)
    if isinstance(notif_list, list):
        print(f"✓ Found {len(notif_list)} unread notification(s)")
        for notif in notif_list[:3]:  # Show first 3
            print(f"  - {notif.get('title', 'N/A')}")
    
    print("\nGetting notification statistics...")
    stats = client.get_notification_stats()
    print(f"✓ Notification stats:")
    print(f"  Total: {stats.get('total_count', 0)}")
    print(f"  Unread: {stats.get('unread_count', 0)}")
    
    # 6. Synchronization
    print("\n4. Synchronization")
    print("-" * 60)
    
    print("Performing full sync...")
    sync_result = client.full_sync(
        platform="ios",
        app_version="1.0.0",
        os_version="17.0",
        device_model="iPhone 15"
    )
    print(f"✓ Full sync completed!")
    print(f"  Sync ID: {sync_result['sync_id']}")
    print(f"  Status: {sync_result['sync_status']}")
    print(f"  Timestamp: {sync_result['sync_timestamp']}")
    
    # Save timestamp from last sync
    last_sync = sync_result['sync_timestamp']
    
    # 7. Delta Sync (after some time)
    print("\nPerforming delta sync...")
    delta_result = client.delta_sync(
        last_sync_timestamp=last_sync,
        platform="ios",
        app_version="1.0.0"
    )
    print(f"✓ Delta sync completed!")
    print(f"  Updated devices: {len(delta_result.get('devices_updated', []))}")
    print(f"  New notifications: {len(delta_result.get('notifications_new', []))}")
    
    # 8. Cleanup (optional)
    print("\n5. Cleanup")
    print("-" * 60)
    
    # Uncomment to delete device
    # print("Deleting test device...")
    # client.delete_device(device_id)
    # print("✓ Device deleted!")
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
