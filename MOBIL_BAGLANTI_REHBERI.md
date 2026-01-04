# Mobil Uygulama Bağlantı Rehberi

## 📋 Ön Hazırlık Adımları

### 1. PostgreSQL Database'i Hazırlayın

```bash
# Database çalışıyor mu kontrol edin
psql -h localhost -U zinzino_user -d zinzino_iot

# Eğer çalışmıyorsa Docker ile başlatın
docker-compose up -d postgres
```

### 2. Database Migration'larını Çalıştırın

```bash
# Migration'ları çalıştır
python migrations/run_migrations.py
```

Bu komut şu tabloları oluşturacak:
- `users` - Kullanıcı hesapları
- `devices` - IoT cihazlar
- `device_states` - Cihaz durumları
- `notifications` - Bildirimler
- `notification_settings` - Bildirim ayarları
- `activities` - Aktivite logları
- `sync_logs` - Senkronizasyon kayıtları

### 3. Backend'i Başlatın

```bash
# Development mode (otomatik reload ile)
uvicorn src.app:app --reload --port 8080

# Ya da direkt Python ile
python src/app.py
```

Backend şu adreste çalışacak: **http://localhost:8080**

### 4. API Dokümantasyonunu Kontrol Edin

Backend çalıştıktan sonra şu adresleri ziyaret edin:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

---

## 🌐 Network Ayarları

### Mobil Cihazdan Erişim İçin

#### A. Aynı WiFi Ağında (Test için)

1. **Bilgisayarınızın IP adresini bulun:**

```bash
# macOS/Linux
ifconfig | grep "inet "
# ya da
ipconfig getifaddr en0

# Örnek çıktı: 192.168.1.100
```

2. **Backend'i tüm interface'lerde dinleyecek şekilde başlatın:**

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload
```

3. **Mobil uygulamanızda Base URL:**
```
http://192.168.1.100:8080
```

#### B. CORS Ayarlarını Güncelleyin

`.env` dosyasında:

```env
# Mobil uygulama için CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://192.168.1.100:8080,*
```

⚠️ **Not**: Production'da `*` kullanmayın, sadece test için!

---

## 📱 Mobil Uygulama Tarafı Ayarları

### 1. Base URL Konfigürasyonu

**React Native / Expo:**

```typescript
// config.ts
const API_CONFIG = {
  // Development (Simulator/Emulator)
  DEV_BASE_URL: __DEV__ 
    ? Platform.select({
        ios: 'http://localhost:8080',      // iOS Simulator
        android: 'http://10.0.2.2:8080',   // Android Emulator
      })
    : 'http://192.168.1.100:8080',        // Real device (WiFi IP)
  
  // Production
  PROD_BASE_URL: 'https://api.zinzino-iot.com',
  
  // Active
  BASE_URL: __DEV__ ? DEV_BASE_URL : PROD_BASE_URL,
};

export default API_CONFIG;
```

**Flutter:**

```dart
// config.dart
class ApiConfig {
  static const String DEV_BASE_URL = 'http://10.0.2.2:8080';  // Android Emulator
  // static const String DEV_BASE_URL = 'http://localhost:8080'; // iOS Simulator
  // static const String DEV_BASE_URL = 'http://192.168.1.100:8080'; // Real Device
  
  static const String PROD_BASE_URL = 'https://api.zinzino-iot.com';
  
  static String get baseUrl {
    return kDebugMode ? DEV_BASE_URL : PROD_BASE_URL;
  }
}
```

### 2. API Client Oluşturun

**React Native (Axios):**

```typescript
// api/client.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import API_CONFIG from './config';

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Token ekle
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Token yenileme
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // 401 hatası ve ilk deneme ise token yenile
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = await AsyncStorage.getItem('refresh_token');
        const response = await axios.post(
          `${API_CONFIG.BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );
        
        const { access_token, refresh_token } = response.data;
        await AsyncStorage.setItem('access_token', access_token);
        await AsyncStorage.setItem('refresh_token', refresh_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Token yenileme başarısız, logout yap
        await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
        // Navigate to login screen
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

**Flutter (Dio):**

```dart
// api/client.dart
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';

class ApiClient {
  static final Dio _dio = Dio(
    BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: Duration(seconds: 10),
      receiveTimeout: Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ),
  );

  static Future<void> init() async {
    // Request interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final prefs = await SharedPreferences.getInstance();
          final token = prefs.getString('access_token');
          
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          
          return handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            // Token yenileme
            final refreshed = await _refreshToken();
            if (refreshed) {
              // Retry original request
              return handler.resolve(await _retry(error.requestOptions));
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  static Future<bool> _refreshToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final refreshToken = prefs.getString('refresh_token');
      
      final response = await _dio.post('/auth/refresh', 
        data: {'refresh_token': refreshToken},
      );
      
      await prefs.setString('access_token', response.data['access_token']);
      await prefs.setString('refresh_token', response.data['refresh_token']);
      
      return true;
    } catch (e) {
      return false;
    }
  }

  static Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: requestOptions.headers,
    );
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  static Dio get instance => _dio;
}
```

---

## 🔐 Authentication Flow

### 1. Kullanıcı Kaydı

```typescript
// services/auth.service.ts
export const register = async (
  email: string,
  password: string,
  fullName: string,
  phone?: string
) => {
  try {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      phone,
      language: 'tr',  // ya da 'en'
      timezone: 'Europe/Istanbul',
    });
    
    const { access_token, refresh_token, user } = response.data;
    
    // Token'ları kaydet
    await AsyncStorage.multiSet([
      ['access_token', access_token],
      ['refresh_token', refresh_token],
      ['user', JSON.stringify(user)],
    ]);
    
    return { success: true, user };
  } catch (error) {
    if (error.response?.status === 409) {
      throw new Error('Bu email zaten kullanılıyor');
    }
    throw error;
  }
};
```

### 2. Giriş Yapma

```typescript
export const login = async (email: string, password: string) => {
  try {
    const response = await apiClient.post('/auth/login', {
      email,
      password,
    });
    
    const { access_token, refresh_token, user } = response.data;
    
    await AsyncStorage.multiSet([
      ['access_token', access_token],
      ['refresh_token', refresh_token],
      ['user', JSON.stringify(user)],
    ]);
    
    return { success: true, user };
  } catch (error) {
    if (error.response?.status === 401) {
      throw new Error('Email veya şifre hatalı');
    }
    throw error;
  }
};
```

### 3. Çıkış Yapma

```typescript
export const logout = async () => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    console.log('Logout error:', error);
  } finally {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
  }
};
```

---

## 📱 Temel Endpoint Kullanımları

### Cihazları Listele

```typescript
// services/device.service.ts
export const getDevices = async () => {
  try {
    const response = await apiClient.get('/devices');
    return response.data;
  } catch (error) {
    console.error('Get devices error:', error);
    throw error;
  }
};
```

### Yeni Cihaz Ekle

```typescript
export const addDevice = async (deviceData: {
  device_name: string;
  device_type: 'fish_oil' | 'vitamin_d' | 'krill_oil' | 'vegan';
  mac_address: string;
  serial_number: string;
  location?: string;
}) => {
  try {
    const response = await apiClient.post('/devices', deviceData);
    return response.data;
  } catch (error) {
    if (error.response?.status === 409) {
      throw new Error('Bu cihaz zaten kayıtlı');
    }
    throw error;
  }
};
```

### Bildirimleri Al

```typescript
export const getNotifications = async (isRead?: boolean) => {
  try {
    const params = isRead !== undefined ? { is_read: isRead } : {};
    const response = await apiClient.get('/notifications', { params });
    return response.data;
  } catch (error) {
    console.error('Get notifications error:', error);
    throw error;
  }
};
```

### Senkronizasyon

```typescript
// İlk açılışta full sync
export const fullSync = async () => {
  try {
    const response = await apiClient.post('/sync/full', {
      device_info: {
        platform: Platform.OS,
        app_version: '1.0.0',
        os_version: Platform.Version,
        device_model: DeviceInfo.getModel(),
      },
      include_deleted: false,
    });
    return response.data;
  } catch (error) {
    console.error('Full sync error:', error);
    throw error;
  }
};

// Periyodik delta sync (her 5-15 dakikada)
export const deltaSync = async (lastSyncTimestamp: string) => {
  try {
    const response = await apiClient.post('/sync/delta', {
      device_info: {
        platform: Platform.OS,
        app_version: '1.0.0',
        os_version: Platform.Version,
        device_model: DeviceInfo.getModel(),
      },
      last_sync_timestamp: lastSyncTimestamp,
      client_changes: {
        devices_modified: [],
        notifications_read: [],
      },
    });
    return response.data;
  } catch (error) {
    console.error('Delta sync error:', error);
    throw error;
  }
};
```

---

## 🧪 Test Etme

### 1. Backend'i Test Edin

```bash
# Health check
curl http://localhost:8080/health

# Register
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "full_name": "Test User",
    "language": "tr",
    "timezone": "Europe/Istanbul"
  }'

# Login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234"
  }'
```

### 2. Postman Collection

`examples/postman_collection.json` dosyasını Postman'e import edin ve tüm endpoint'leri test edin.

---

## 🐛 Sorun Giderme

### Bağlantı Sorunları

1. **Backend çalışıyor mu?**
```bash
curl http://localhost:8080/health
```

2. **Firewall engeli var mı?** (macOS için)
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
```

3. **CORS hatası?**
- `.env` dosyasında `CORS_ORIGINS` ayarını kontrol edin
- Mobil IP adresini ekleyin

4. **Token hatası?**
- Token süresi dolmuş olabilir (1440 dakika = 1 gün)
- Refresh token kullanarak yenileyin

### Android Emulator Notları

- `localhost` yerine `10.0.2.2` kullanın
- Emulator settings'ten ağ ayarlarını kontrol edin

### iOS Simulator Notları

- `localhost:8080` direkt çalışır
- Gerçek cihazda WiFi IP adresi gerekir

---

## 📊 Önerilen Senkronizasyon Stratejisi

1. **İlk Açılış**: Full Sync
2. **Arka Plan**: Delta Sync (her 5-15 dakika)
3. **Pull-to-Refresh**: Delta Sync
4. **7+ gün sonra**: Full Sync
5. **Çakışma durumunda**: Full Sync

---

## 🔒 Güvenlik Notları

- **Production'da**: HTTPS kullanın
- **API Keys**: `.env` dosyasını commit etmeyin
- **Token Storage**: Güvenli storage kullanın (Keychain/KeyStore)
- **SSL Pinning**: Production'da implement edin

---

## 📞 Yardım

Sorun yaşarsanız:
1. Backend loglarını kontrol edin
2. Network inspector kullanın (Flipper, Reactotron)
3. API dokümantasyonuna bakın: http://localhost:8080/docs

