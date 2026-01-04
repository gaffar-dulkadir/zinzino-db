# 📡 Zinzino IoT API - Endpoint Referansı

## Base URL
```
http://localhost:8080
```

---

## 🔐 Authentication Endpoints

### 1. Kullanıcı Kaydı
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "Ahmet Yılmaz",
  "phone": "+905551234567",
  "language": "tr",
  "timezone": "Europe/Istanbul"
}

Response 201 Created:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "full_name": "Ahmet Yılmaz",
    "language": "tr",
    "timezone": "Europe/Istanbul",
    "created_at": "2024-01-03T12:00:00Z"
  }
}
```

### 2. Giriş Yapma
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response 200 OK:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { ... }
}
```

### 3. Google OAuth
```http
POST /auth/google
Content-Type: application/json

{
  "id_token": "google_id_token_from_google_sign_in",
  "full_name": "Ahmet Yılmaz",
  "profile_picture": "https://..."
}

Response 200 OK: (Same as login)
```

### 4. Apple OAuth
```http
POST /auth/apple
Content-Type: application/json

{
  "id_token": "apple_id_token",
  "authorization_code": "apple_auth_code",
  "full_name": "Ahmet Yılmaz"
}

Response 200 OK: (Same as login)
```

### 5. Token Yenileme
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

Response 200 OK:
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 6. Çıkış Yapma
```http
POST /auth/logout
Authorization: Bearer {access_token}

Response 200 OK:
{
  "message": "Logged out successfully"
}
```

### 7. Şifremi Unuttum
```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}

Response 200 OK:
{
  "message": "If the email exists, a password reset link has been sent"
}
```

### 8. Şifre Sıfırlama
```http
POST /auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_from_email",
  "new_password": "NewSecure123",
  "confirm_password": "NewSecure123"
}

Response 200 OK:
{
  "message": "Password has been reset successfully"
}
```

### 9. Email Doğrulama
```http
POST /auth/verify-email
Content-Type: application/json

{
  "token": "verification_token_from_email"
}

Response 200 OK:
{
  "message": "Email verified successfully"
}
```

---

## 👤 Profile Endpoints

### 1. Profil Bilgilerini Getir
```http
GET /profile
Authorization: Bearer {access_token}

Response 200 OK:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "Ahmet Yılmaz",
  "phone": "+905551234567",
  "language": "tr",
  "timezone": "Europe/Istanbul",
  "created_at": "2024-01-03T12:00:00Z",
  "updated_at": "2024-01-03T12:00:00Z"
}
```

### 2. Profil Güncelle
```http
PUT /profile
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "full_name": "Ahmet Mehmet Yılmaz",
  "phone": "+905559876543",
  "language": "en",
  "timezone": "Europe/London"
}

Response 200 OK: (Updated profile)
```

### 3. Şifre Değiştir
```http
PUT /profile/password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}

Response 200 OK:
{
  "message": "Password changed successfully"
}
```

---

## 📱 Device Endpoints

### 1. Cihazları Listele
```http
GET /devices
Authorization: Bearer {access_token}
Query Params: ?include_inactive=false

Response 200 OK:
[
  {
    "device_id": "uuid",
    "device_name": "Mutfak Dispenseri",
    "device_type": "fish_oil",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "serial_number": "ZNZ-2024-0001",
    "location": "Mutfak",
    "firmware_version": "1.0.0",
    "battery_level": 85,
    "supplement_level": 70,
    "is_connected": true,
    "is_active": true,
    "last_seen": "2024-01-03T12:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-03T12:00:00Z"
  }
]
```

**Device Types:**
- `fish_oil` - Balık Yağı Dispenseri
- `vitamin_d` - D Vitamini Dispenseri
- `krill_oil` - Krill Yağı Dispenseri
- `vegan` - Vegan Takviye Dispenseri

### 2. Yeni Cihaz Ekle
```http
POST /devices
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_name": "Yatak Odası Dispenseri",
  "device_type": "fish_oil",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "serial_number": "ZNZ-2024-0002",
  "location": "Yatak Odası",
  "firmware_version": "1.0.0"
}

Response 201 Created: (Device object)
```

### 3. Cihaz Detayı
```http
GET /devices/{device_id}
Authorization: Bearer {access_token}

Response 200 OK: (Device object)
```

### 4. Cihaz Güncelle
```http
PUT /devices/{device_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_name": "Yeni İsim",
  "location": "Salon",
  "is_active": true
}

Response 200 OK: (Updated device)
```

### 5. Cihaz Sil
```http
DELETE /devices/{device_id}
Authorization: Bearer {access_token}

Response 200 OK:
{
  "success": true,
  "device_id": "uuid"
}
```

### 6. Cihaz Geçmişi
```http
GET /devices/{device_id}/history
Authorization: Bearer {access_token}
Query Params: ?limit=50&offset=0

Response 200 OK:
{
  "activities": [
    {
      "activity_id": "uuid",
      "device_id": "uuid",
      "action_type": "dispense",
      "dosage_ml": 5.0,
      "timestamp": "2024-01-03T09:00:00Z",
      "metadata": {
        "supplement_type": "fish_oil",
        "scheduled": true,
        "temperature": 22.5
      }
    }
  ],
  "total": 150
}
```

**Action Types:**
- `dispense` - Dozaj verildi
- `refill` - Takviye dolduruldu
- `battery_change` - Pil değiştirildi
- `connection_lost` - Bağlantı kesildi
- `connection_restored` - Bağlantı yeniden kuruldu

---

## 🔋 Device State Endpoints

### 1. Cihaz Durumunu Güncelle (IoT için)
```http
PATCH /states/{device_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "battery_level": 80,
  "supplement_level": 65,
  "is_connected": true,
  "temperature": 23.5,
  "humidity": 45.2,
  "last_dispense_time": "2024-01-03T09:00:00Z"
}

Response 200 OK:
{
  "device_id": "uuid",
  "battery_level": 80,
  "supplement_level": 65,
  "is_connected": true,
  "updated_at": "2024-01-03T12:30:00Z"
}
```

### 2. Son Cihaz Durumu
```http
GET /states/{device_id}/latest
Authorization: Bearer {access_token}

Response 200 OK: (Latest device state)
```

---

## 🔔 Notification Endpoints

### 1. Bildirimleri Listele
```http
GET /notifications
Authorization: Bearer {access_token}
Query Params: ?is_read=false&limit=50&offset=0

Response 200 OK:
{
  "notifications": [
    {
      "notification_id": "uuid",
      "type": "reminder",
      "title": "Takviye Zamanı!",
      "message": "Günlük balık yağı dozunuzu almayı unutmayın",
      "device_id": "uuid",
      "is_read": false,
      "created_at": "2024-01-03T09:00:00Z",
      "read_at": null,
      "metadata": {
        "scheduled_time": "09:00",
        "dosage_ml": 5.0
      }
    }
  ],
  "total": 25
}
```

**Notification Types:**
- `reminder` - Hatırlatma
- `low_battery` - Düşük pil uyarısı
- `low_supplement` - Takviye azaldı
- `achievement` - Başarı kazanıldı
- `device_offline` - Cihaz çevrimdışı
- `device_online` - Cihaz çevrimiçi

### 2. Bildirim Oluştur
```http
POST /notifications
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "type": "reminder",
  "title": "Hatırlatma",
  "message": "Mesaj içeriği",
  "device_id": "uuid",
  "metadata": {}
}

Response 201 Created: (Notification object)
```

### 3. Bildirimi Okundu İşaretle
```http
PUT /notifications/{notification_id}/read
Authorization: Bearer {access_token}

Response 200 OK:
{
  "notification_id": "uuid",
  "is_read": true,
  "read_at": "2024-01-03T12:30:00Z"
}
```

### 4. Tümünü Okundu İşaretle
```http
POST /notifications/mark-all-read
Authorization: Bearer {access_token}

Response 200 OK:
{
  "marked_count": 15
}
```

### 5. Bildirim İstatistikleri
```http
GET /notifications/stats
Authorization: Bearer {access_token}

Response 200 OK:
{
  "total_count": 50,
  "unread_count": 15,
  "by_type": {
    "reminder": 30,
    "low_battery": 10,
    "low_supplement": 5,
    "achievement": 5
  }
}
```

### 6. Bildirim Sil
```http
DELETE /notifications/{notification_id}
Authorization: Bearer {access_token}

Response 200 OK:
{
  "success": true,
  "notification_id": "uuid"
}
```

---

## ⚙️ Notification Settings Endpoints

### 1. Bildirim Ayarlarını Getir
```http
GET /notification-settings
Authorization: Bearer {access_token}

Response 200 OK:
{
  "user_id": "uuid",
  "reminders_enabled": true,
  "low_battery_alerts": true,
  "low_supplement_alerts": true,
  "achievement_notifications": true,
  "device_status_alerts": true,
  "reminder_times": ["09:00", "21:00"],
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "notification_sound": true,
  "notification_vibration": true,
  "email_notifications": false,
  "push_notifications": true
}
```

### 2. Bildirim Ayarlarını Güncelle
```http
PUT /notification-settings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reminders_enabled": true,
  "reminder_times": ["08:00", "20:00"],
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00",
  "push_notifications": true
}

Response 200 OK: (Updated settings)
```

---

## 🔄 Sync Endpoints

### 1. Full Sync (İlk Açılış)
```http
POST /sync/full
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_info": {
    "platform": "ios",
    "app_version": "1.0.0",
    "os_version": "17.0",
    "device_model": "iPhone 15"
  },
  "include_deleted": false
}

Response 200 OK:
{
  "sync_id": "uuid",
  "sync_timestamp": "2024-01-03T12:30:00Z",
  "sync_status": "success",
  "devices": [...],
  "notifications": [...],
  "activity_logs": [...],
  "notification_settings": {...},
  "user_profile": {...}
}
```

### 2. Delta Sync (Periyodik)
```http
POST /sync/delta
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_info": {
    "platform": "ios",
    "app_version": "1.0.0",
    "os_version": "17.0",
    "device_model": "iPhone 15"
  },
  "last_sync_timestamp": "2024-01-03T12:00:00Z",
  "client_changes": {
    "devices_modified": [],
    "notifications_read": ["uuid1", "uuid2"]
  }
}

Response 200 OK:
{
  "sync_id": "uuid",
  "sync_timestamp": "2024-01-03T12:30:00Z",
  "sync_status": "success",
  "devices_updated": [...],
  "devices_deleted": [],
  "notifications_new": [...],
  "notifications_updated": [...],
  "activity_logs_new": [...],
  "conflicts": []
}
```

### 3. Sync Durumu
```http
GET /sync/status
Authorization: Bearer {access_token}

Response 200 OK:
{
  "last_full_sync": "2024-01-01T10:00:00Z",
  "last_delta_sync": "2024-01-03T12:00:00Z",
  "last_sync_status": "success",
  "recommend_full_sync": false,
  "pending_changes": 0
}
```

---

## 📊 Activity Endpoints

### 1. Aktiviteleri Listele
```http
GET /activities
Authorization: Bearer {access_token}
Query Params: ?limit=50&offset=0&device_id=uuid&action_type=dispense

Response 200 OK:
{
  "activities": [
    {
      "activity_id": "uuid",
      "device_id": "uuid",
      "action_type": "dispense",
      "dosage_ml": 5.0,
      "timestamp": "2024-01-03T09:00:00Z",
      "metadata": {
        "supplement_type": "fish_oil",
        "scheduled": true,
        "temperature": 22.5,
        "success": true
      }
    }
  ],
  "total": 150
}
```

### 2. Aktivite Oluştur
```http
POST /activities
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_id": "uuid",
  "action_type": "dispense",
  "dosage_ml": 5.0,
  "timestamp": "2024-01-03T09:00:00Z",
  "metadata": {
    "supplement_type": "fish_oil",
    "scheduled": true
  }
}

Response 201 Created: (Activity object)
```

### 3. Günlük/Haftalık/Aylık İstatistikler
```http
GET /activities/stats
Authorization: Bearer {access_token}
Query Params: ?period=week&device_id=uuid

Response 200 OK:
{
  "period": "week",
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "total_dispenses": 14,
  "total_dosage_ml": 70.0,
  "avg_dosage_ml": 5.0,
  "by_day": [
    {
      "date": "2024-01-01",
      "dispenses": 2,
      "dosage_ml": 10.0
    }
  ],
  "streak_days": 7,
  "compliance_rate": 100.0
}
```

---

## 🏥 Health Check

### 1. Sistem Sağlığı
```http
GET /health

Response 200 OK:
{
  "status": "healthy",
  "timestamp": "2024-01-03T12:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "uptime_seconds": 3600
}
```

---

## 🌐 Root Endpoint

### 1. API Bilgisi
```http
GET /

Response 200 OK:
{
  "service": "Zinzino IoT Backend API",
  "version": "1.0.0",
  "description": "REST API for Zinzino IoT supplement dispensers",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "authentication": "/auth/*",
    "profile": "/profile/*",
    "devices": "/devices/*",
    "states": "/states/*",
    "activities": "/activities/*",
    "notifications": "/notifications/*",
    "sync": "/sync/*"
  }
}
```

---

## 🔒 Authorization Header

Tüm korumalı endpoint'ler için:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data",
  "error_code": "VALIDATION_ERROR"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token",
  "error_code": "UNAUTHORIZED"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

### 409 Conflict
```json
{
  "detail": "Email already exists",
  "error_code": "DUPLICATE_ERROR"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

---

## 📖 Daha Fazla Bilgi

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **API Dökümantasyonu**: `API_DOCUMENTATION.md`
- **Bağlantı Rehberi**: `MOBIL_BAGLANTI_REHBERI.md`
