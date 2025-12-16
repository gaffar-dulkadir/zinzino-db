# Zinzino IoT Backend API Documentation

## 📋 Table of Contents
- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [1. Authentication](#1-authentication)
  - [2. Profile Management](#2-profile-management)
  - [3. Device Management](#3-device-management)
  - [4. Device States](#4-device-states)
  - [5. Synchronization](#5-synchronization)
  - [6. Activity Logs](#6-activity-logs)
  - [7. Notifications](#7-notifications)
  - [8. IoT Device Communication](#8-iot-device-communication)
  - [9. Analytics](#9-analytics)
  - [10. Utility](#10-utility)

---

## Overview

**Version:** 1.0.0  
**Protocol:** HTTPS  
**Data Format:** JSON  
**Date Format:** ISO 8601 (UTC)

### Architecture
```
Mobile App (SQLite) <--Sync--> Backend API <--> PostgreSQL
        ↓                         ↓
IoT Devices <--Bluetooth-->  MQTT/WebSocket
```

---

## Base URL

```
Production:  https://api.zinzino.com/v1
Staging:     https://api-staging.zinzino.com/v1
Development: http://localhost:3000/api
```

---

## Authentication

### Bearer Token
All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Lifecycle
- **Access Token:** Expires in 24 hours
- **Refresh Token:** Expires in 30 days
- **Auto-refresh:** Recommended 5 minutes before expiry

### Required Headers
```http
Content-Type: application/json
Authorization: Bearer {token}
X-App-Version: 1.0.0
X-Platform: ios | android
Accept-Language: tr-TR
```

---

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2025-12-05T10:00:00Z"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Invalid or expired token |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Input validation failed |
| `DUPLICATE_ENTRY` | Resource already exists |
| `DEVICE_NOT_CONNECTED` | IoT device offline |
| `SYNC_CONFLICT` | Data synchronization conflict |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Rate Limiting

### Limits
- **General Endpoints:** 100 requests/minute
- **Auth Endpoints:** 10 requests/minute
- **Sync Endpoints:** 20 requests/minute
- **IoT Endpoints:** 200 requests/minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638720000
```

---

## Endpoints

## 1. Authentication

### 1.1 Register

Create a new user account.

```http
POST /auth/register
```

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Ahmet Yılmaz"
}
```

**Validation Rules**
- `email`: Valid email format, unique
- `password`: Minimum 6 characters
- `full_name`: 2-100 characters

**Response 201**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "Ahmet Yılmaz",
      "created_at": "2025-12-05T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string_here"
  }
}
```

**Errors**
- `400` - Validation error
- `409` - Email already exists

---

### 1.2 Login

Authenticate user with email and password.

```http
POST /auth/login
```

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "Ahmet Yılmaz",
      "profile_picture": "https://cdn.zinzino.com/profiles/user.jpg",
      "created_at": "2025-12-05T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string_here"
  }
}
```

**Errors**
- `401` - Invalid credentials
- `403` - Account locked or inactive

---

### 1.3 Google Sign-In

Authenticate with Google OAuth.

```http
POST /auth/google
```

**Request Body**
```json
{
  "id_token": "google_id_token_here",
  "access_token": "google_access_token_here"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@gmail.com",
      "full_name": "Ahmet Yılmaz",
      "profile_picture": "https://lh3.googleusercontent.com/...",
      "created_at": "2025-12-05T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string_here",
    "is_new_user": false
  }
}
```

**Errors**
- `400` - Invalid Google token
- `401` - Google authentication failed

---

### 1.4 Apple Sign-In

Authenticate with Apple ID.

```http
POST /auth/apple
```

**Request Body**
```json
{
  "identity_token": "apple_identity_token_here",
  "user_id": "apple_user_id_here",
  "email": "user@privaterelay.appleid.com",
  "full_name": "Ahmet Yılmaz"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@privaterelay.appleid.com",
      "full_name": "Ahmet Yılmaz",
      "created_at": "2025-12-05T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string_here",
    "is_new_user": true
  }
}
```

**Errors**
- `400` - Invalid Apple token
- `401` - Apple authentication failed

---

### 1.5 Refresh Token

Get a new access token using refresh token.

```http
POST /auth/refresh
```

**Request Body**
```json
{
  "refresh_token": "refresh_token_string_here"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "token": "new_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_refresh_token_string_here",
    "expires_in": 86400
  }
}
```

**Errors**
- `401` - Invalid or expired refresh token

---

### 1.6 Forgot Password

Request password reset email.

```http
POST /auth/forgot-password
```

**Request Body**
```json
{
  "email": "user@example.com"
}
```

**Response 200**
```json
{
  "success": true,
  "message": "Şifre sıfırlama bağlantısı email adresinize gönderildi"
}
```

**Errors**
- `404` - Email not found
- `429` - Too many reset requests

---

### 1.7 Reset Password

Reset password with token from email.

```http
POST /auth/reset-password
```

**Request Body**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePassword123!"
}
```

**Response 200**
```json
{
  "success": true,
  "message": "Şifreniz başarıyla güncellendi"
}
```

**Errors**
- `400` - Invalid or expired token
- `422` - Password validation failed

---

### 1.8 Logout

Invalidate current session.

```http
POST /auth/logout
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "message": "Başarıyla çıkış yapıldı"
}
```

---

### 1.9 Verify Email

Verify user email address.

```http
POST /auth/verify-email
```

**Request Body**
```json
{
  "token": "email_verification_token"
}
```

**Response 200**
```json
{
  "success": true,
  "message": "Email adresiniz doğrulandı"
}
```

---

## 2. Profile Management

### 2.1 Get Profile

Get current user profile.

```http
GET /profile
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Ahmet Yılmaz",
    "profile_picture": "https://cdn.zinzino.com/profiles/user.jpg",
    "phone": "+905551234567",
    "notification_enabled": true,
    "theme_preference": "dark",
    "language": "tr",
    "created_at": "2025-11-01T10:00:00Z",
    "updated_at": "2025-12-05T09:00:00Z"
  }
}
```

---

### 2.2 Update Profile

Update user profile information.

```http
PUT /profile
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "full_name": "Ahmet Yılmaz Güncel",
  "phone": "+905551234567",
  "notification_enabled": false,
  "theme_preference": "light",
  "language": "en"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Ahmet Yılmaz Güncel",
    "phone": "+905551234567",
    "notification_enabled": false,
    "theme_preference": "light",
    "language": "en",
    "updated_at": "2025-12-05T11:00:00Z"
  }
}
```

**Errors**
- `422` - Validation error

---

### 2.3 Upload Profile Picture

Upload or update profile picture.

```http
POST /profile/picture
```

**Headers**
```http
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request Body**
```
file: [image file]
```

**Constraints**
- Max file size: 5MB
- Allowed formats: jpg, jpeg, png, webp
- Recommended: 512x512px, square ratio

**Response 200**
```json
{
  "success": true,
  "data": {
    "profile_picture": "https://cdn.zinzino.com/profiles/550e8400.jpg",
    "thumbnail": "https://cdn.zinzino.com/profiles/550e8400_thumb.jpg"
  }
}
```

**Errors**
- `400` - Invalid file format
- `413` - File too large

---

### 2.4 Change Password

Change user password.

```http
PUT /profile/password
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response 200**
```json
{
  "success": true,
  "message": "Şifre başarıyla güncellendi"
}
```

**Errors**
- `401` - Current password incorrect
- `422` - Password validation failed

---

### 2.5 Delete Account

Permanently delete user account.

```http
DELETE /profile
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "password": "CurrentPassword123!",
  "confirmation": "DELETE"
}
```

**Response 200**
```json
{
  "success": true,
  "message": "Hesabınız kalıcı olarak silindi"
}
```

**Errors**
- `401` - Invalid password
- `400` - Missing confirmation

---

## 3. Device Management

### 3.1 List Devices

Get all devices for current user.

```http
GET /devices
```

**Headers**
```http
Authorization: Bearer {token}
```

**Query Parameters**
- `include_inactive`: boolean (default: false)
- `sort`: string (name, created_at, battery_level)
- `order`: string (asc, desc)

**Response 200**
```json
{
  "success": true,
  "data": [
    {
      "id": "device-uuid-1",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_name": "Mutfak Dispenseri",
      "device_type": "fish_oil",
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "location": "Mutfak",
      "battery_level": 85,
      "supplement_level": 70,
      "is_connected": true,
      "last_sync": "2025-12-05T09:30:00Z",
      "firmware_version": "1.2.3",
      "serial_number": "ZNZ-2024-001",
      "total_doses_dispensed": 145,
      "created_at": "2025-11-01T10:00:00Z",
      "updated_at": "2025-12-05T09:30:00Z"
    },
    {
      "id": "device-uuid-2",
      "device_name": "Yatak Odası",
      "device_type": "vitamin_d",
      "battery_level": 45,
      "supplement_level": 20,
      "is_connected": false,
      "last_sync": "2025-12-04T22:15:00Z"
    }
  ]
}
```

---

### 3.2 Get Device Details

Get detailed information for a specific device.

```http
GET /devices/:deviceId
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "device-uuid-1",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_name": "Mutfak Dispenseri",
    "device_type": "fish_oil",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "location": "Mutfak",
    "battery_level": 85,
    "supplement_level": 70,
    "is_connected": true,
    "last_sync": "2025-12-05T09:30:00Z",
    "firmware_version": "1.2.3",
    "serial_number": "ZNZ-2024-001",
    "total_doses_dispensed": 145,
    "created_at": "2025-11-01T10:00:00Z",
    "updated_at": "2025-12-05T09:30:00Z",
    "current_state": {
      "cup_placed": false,
      "last_state_change": "2025-12-05T09:25:00Z"
    },
    "statistics": {
      "daily_average": 1.2,
      "weekly_total": 8,
      "monthly_total": 32
    }
  }
}
```

**Errors**
- `404` - Device not found
- `403` - Not authorized to access this device

---

### 3.3 Add Device

Register a new IoT device.

```http
POST /devices
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "device_name": "Salon Dispenseri",
  "device_type": "krill_oil",
  "mac_address": "FF:EE:DD:CC:BB:AA",
  "location": "Salon",
  "serial_number": "ZNZ-2024-002"
}
```

**Device Types**
- `fish_oil` - Balık Yağı
- `vitamin_d` - D Vitamini
- `krill_oil` - Krill Yağı
- `vegan` - Vegan Omega

**Response 201**
```json
{
  "success": true,
  "data": {
    "id": "new-device-uuid",
    "device_name": "Salon Dispenseri",
    "device_type": "krill_oil",
    "mac_address": "FF:EE:DD:CC:BB:AA",
    "location": "Salon",
    "battery_level": 100,
    "supplement_level": 100,
    "is_connected": false,
    "serial_number": "ZNZ-2024-002",
    "created_at": "2025-12-05T10:00:00Z"
  }
}
```

**Errors**
- `409` - Device already registered
- `422` - Validation error

---

### 3.4 Update Device

Update device information.

```http
PUT /devices/:deviceId
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "device_name": "Mutfak - Balık Yağı",
  "location": "Mutfak Tezgahı"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "device-uuid-1",
    "device_name": "Mutfak - Balık Yağı",
    "location": "Mutfak Tezgahı",
    "updated_at": "2025-12-05T10:15:00Z"
  }
}
```

**Errors**
- `404` - Device not found
- `403` - Not authorized

---

### 3.5 Delete Device

Remove a device from user account.

```http
DELETE /devices/:deviceId
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "message": "Cihaz başarıyla silindi"
}
```

**Errors**
- `404` - Device not found
- `403` - Not authorized

---

### 3.6 Update Device Status

Update device status information (used by IoT devices).

```http
PATCH /devices/:deviceId/status
```

**Headers**
```http
Authorization: Bearer {device_token}
```

**Request Body**
```json
{
  "battery_level": 82,
  "supplement_level": 65,
  "is_connected": true,
  "firmware_version": "1.2.4"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "device-uuid-1",
    "battery_level": 82,
    "supplement_level": 65,
    "is_connected": true,
    "last_sync": "2025-12-05T10:30:00Z",
    "notifications_sent": ["low_supplement"]
  }
}
```

---

### 3.7 Get Device History

Get usage history for a device.

```http
GET /devices/:deviceId/history
```

**Headers**
```http
Authorization: Bearer {token}
```

**Query Parameters**
- `start_date`: ISO date string
- `end_date`: ISO date string
- `limit`: integer (default: 50)
- `offset`: integer (default: 0)

**Response 200**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": "activity-uuid-1",
        "action": "dose_dispensed",
        "timestamp": "2025-12-05T08:00:00Z",
        "metadata": {
          "dose_amount": "5ml",
          "triggered_by": "automatic"
        }
      }
    ],
    "pagination": {
      "total": 145,
      "limit": 50,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

## 4. Device States

### 4.1 Get Device State

Get current state of a device (cup placement).

```http
GET /states/:deviceId
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "device_id": "device-uuid-1",
    "cup_placed": false,
    "sensor_reading": 0.12,
    "last_state_change": "2025-12-05T09:25:00Z",
    "state_history": [
      {
        "cup_placed": true,
        "timestamp": "2025-12-05T09:20:00Z",
        "duration_seconds": 300
      },
      {
        "cup_placed": false,
        "timestamp": "2025-12-05T09:25:00Z"
      }
    ]
  }
}
```

---

### 4.2 Update Device State

Update device state (called by IoT device).

```http
POST /states/:deviceId
```

**Headers**
```http
Authorization: Bearer {device_token}
```

**Request Body**
```json
{
  "cup_placed": true,
  "sensor_reading": 0.85,
  "timestamp": "2025-12-05T10:35:00Z"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "device_id": "device-uuid-1",
    "cup_placed": true,
    "last_state_change": "2025-12-05T10:35:00Z",
    "should_dispense": true,
    "dispense_amount": "5ml"
  }
}
```

---

### 4.3 Get All States

Get current states for all user devices.

```http
GET /states
```

**Headers**
```http
Authorization: Bearer {token}
```

**Response 200**
```json
{
  "success": true,
  "data": [
    {
      "device_id": "device-uuid-1",
      "device_name": "Mutfak Dispenseri",
      "cup_placed": false,
      "last_state_change": "2025-12-05T09:25:00Z"
    },
    {
      "device_id": "device-uuid-2",
      "device_name": "Yatak Odası",
      "cup_placed": true,
      "last_state_change": "2025-12-05T10:30:00Z"
    }
  ]
}
```

---

### 4.4 Get State History

Get historical state changes for a device.

```http
GET /states/:deviceId/history
```

**Headers**
```http
Authorization: Bearer {token}
```

**Query Parameters**
- `start_date`: ISO date string
- `end_date`: ISO date string
- `limit`: integer (default: 100)

**Response 200**
```json
{
  "success": true,
  "data": {
    "device_id": "device-uuid-1",
    "history": [
      {
        "cup_placed": true,
        "sensor_reading": 0.87,
        "timestamp": "2025-12-05T08:00:00Z",
        "duration_seconds": 450
      },
      {
        "cup_placed": false,
        "sensor_reading": 0.15,
        "timestamp": "2025-12-05T08:07:30Z"
      }
    ],
    "statistics": {
      "total_placements": 32,
      "average_duration_seconds": 380,
      "total_duration_minutes": 203
    }
  }
}
```

---

## 5. Synchronization

### 5.1 Full Sync

Complete data synchronization (used on app startup).

```http
POST /sync/full
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "last_sync": "2025-12-04T22:00:00Z",
  "device_info": {
    "platform": "ios",
    "app_version": "1.0.0",
    "os_version": "17.2"
  }
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "profile": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "Ahmet Yılmaz",
      "email": "user@example.com",
      "theme_preference": "dark",
      "notification_enabled": true,
      "updated_at": "2025-12-05T09:00:00Z"
    },
    "devices": [
      {
        "id": "device-uuid-1",
        "device_name": "Mutfak Dispenseri",
        "device_type": "fish_oil",
        "battery_level": 85,
        "supplement_level": 70,
        "is_connected": true,
        "updated_at": "2025-12-05T09:30:00Z"
      }
    ],
    "states": [
      {
        "device_id": "device-uuid-1",
        "cup_placed": false,
        "last_state_change": "2025-12-05T09:25:00Z"
      }
    ],
    "activity_logs": [
      {
        "id": "log-uuid-1",
        "device_id": "device-uuid-1",
        "action": "dose_dispensed",
        "timestamp": "2025-12-05T08:00:00Z",
        "metadata": {
          "dose_amount": "5ml"
        }
      }
    ],
    "notifications": [
      {
        "id": "notif-uuid-1",
        "type": "reminder",
        "title": "Takviye Zamanı",
        "message": "Günlük takviyelenizi almayı unutmayın",
        "is_read": false,
        "created_at": "2025-12-05T08:00:00Z"
      }
    ],
    "sync_timestamp": "2025-12-05T10:40:00Z",
    "has_more": false
  }
}
```

---

### 5.2 Delta Sync

Incremental synchronization (only changes since last sync).

```http
POST /sync/delta
```

**Headers**
```http
Authorization: Bearer {token}
```

**Request Body**
```json
{
  "last_sync": "2025-12-05T09:00:00Z"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "updated_devices": [
      {
        "id": "device-uuid-1",
        "battery_level": 83,
        "supplement_level": 68,
        "updated_at": "2025-12-05T10:00:00Z"
      }
    ],
    "updated_states": [
      {
        "device_id": "device-uuid-2",
        "cup_placed": true,
        "last_state_change": "2025-12-05T10:30:00Z"
      }
    ],
    "new_activity_logs": [
      {
        "id": "new-log-uuid",
        "device_id": "device-uuid-2",
        "action": "dose_dispensed",
        "timestamp": "2025-12-05T10:30:00Z"
      }
    ],
    "new_notifications": [
      {
        "id": "new-notif-uuid",
        "type": "achievement",
        "title": "7 Günlük Seri!",
        "message": "Harika! 7 gün üst üste takviye aldınız",
        "created_at": "2025-12-05T10:00:00Z"
      }
    ],
    "deleted_items": {
      "devices": [],
      "activity_logs": [],
      "notifications": []
    },
    "sync_