# 🚀 Zinzino IoT Backend API - Quick Start Guide

## ⚡ Hızlı Başlangıç (5 Dakikada Çalıştır!)

### 1. PostgreSQL'i Başlat

```bash
docker-compose up -d
```

Verify:
```bash
docker-compose ps
# zinzino_postgres should be "healthy"
```

### 2. Environment Variables

```bash
cp .env.example .env
```

**ÖNEMLİ:** `.env` dosyasını açıp `JWT_SECRET_KEY` ekleyin:
```env
JWT_SECRET_KEY=super-secret-key-change-this-in-production-min-32-chars
```

### 3. Python Dependencies

```bash
# Virtual environment oluştur
python -m venv .venv
source .venv/bin/activate  # MacOS/Linux
# Windows: .venv\Scripts\activate

# Dependencies yükle
pip install -r requirements.txt
```

### 4. Database Migration

```bash
python migrations/run_migrations.py
```

Beklenen çıktı:
```
→ Running 001_create_schemas...
✓ Completed 001_create_schemas
→ Running 002_create_auth_tables...
✓ Completed 002_create_auth_tables
...
✓ All migrations completed successfully!
```

### 5. Uygulamayı Başlat

```bash
python src/app.py
```

Beklenen output:
```
🚀 Starting Zinzino IoT Backend API...
📝 Environment: development
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 6. API'yi Test Et

```bash
# Health check
curl http://localhost:8080/health

# Root endpoint
curl http://localhost:8080/

# API Documentation
open http://localhost:8080/docs
```

---

## 📚 API Dokümantasyon

Uygulama çalıştığında:

- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc
- **OpenAPI JSON:** http://localhost:8080/openapi.json

---

## 🧪 Test Workflow

### 1. Kullanıcı Kaydı

```bash
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "full_name": "Test User"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "user": {...},
    "token": "eyJhbGciOi...",
    "refresh_token": "..."
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234"
  }'
```

### 3. Device Ekle (Token Gerekli)

```bash
# Token'ı değişkenekaydet
TOKEN="your_access_token_here"

curl -X POST http://localhost:8080/devices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_name": "Kitchen Dispenser",
    "device_type": "fish_oil",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "serial_number": "ZNZ-2024-001",
    "location": "Kitchen"
  }'
```

### 4. Device Listele

```bash
curl -X GET http://localhost:8080/devices \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Full Sync

```bash
curl -X POST http://localhost:8080/sync/full \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "last_sync": null,
    "device_info": {
      "platform": "ios",
      "app_version": "1.0.0",
      "os_version": "17.2"
    }
  }'
```

---

## 🐛 Troubleshooting

### Port zaten kullanılıyor?

```bash
# Port 8080'i kim kullanıyor kontrol et
lsof -i :8080

# Başka port kullan
APP_PORT=8081 python src/app.py
```

### PostgreSQL bağlantı hatası?

```bash
# Container çalışıyor mu?
docker-compose ps

# Container log'ları kontrol et
docker-compose logs postgres

# PostgreSQL'i restart et
docker-compose restart postgres
```

### Migration hataları?

```bash
# Rollback yap
python migrations/rollback_migrations.py --all

# Tekrar migrate et
python migrations/run_migrations.py

# Manuel SQL kontrol
docker-compose exec postgres psql -U zinzino_user -d zinzino_iot
```

### Import Errors?

```bash
# Virtual environment'ın active olduğundan emin ol
which python  # .venv/bin/python olmalı

# Dependencies tekrar yükle
pip install --force-reinstall -r requirements.txt
```

---

## 📊 Başarılı Kurulum Kontrolü

✅ Database çalışıyor: `docker-compose ps`  
✅ Migrations tamam: `SELECT * FROM schema_migrations;`  
✅ App başladı: http://localhost:8080/health returns {"status": "healthy"}  
✅ Docs açılıyor: http://localhost:8080/docs  
✅ Register çalışıyor: `/auth/register` endpoint 201 döner  

---

## 🎯 Sonraki Adımlar

1. ✅ Test et - Postman collection'ı import et
2. ✅ Customize et - `.env` dosyasını production values ile güncelle
3. ✅ Deploy et - [`DEPLOYMENT.md`](DEPLOYMENT.md) rehberini takip et
4. ✅ Mobile app'i entegre et - API documentation kullanarak

**Başarılar! 🎉**

---

*Daha detaylı bilgi için [`README.md`](README.md), [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) dosyalarına bakın.*
