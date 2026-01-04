# Mobil Uygulama Emülatör Kurulum ve Çalıştırma Rehberi

Bu rehber, `zinzino` mobil uygulamasını (Expo/React Native) emülatörde nasıl çalıştıracağınızı adım adım açıklamaktadır.

## 1. Ön Hazırlıklar

Uygulamayı çalıştırmadan önce bilgisayarınızda aşağıdaki araçların kurulu olduğundan emin olun:

*   **Node.js:** En az v18 veya üzeri (LTS önerilir).
*   **Watchman:** (macOS için) Dosya değişikliklerini izlemek için gereklidir. `brew install watchman` ile kurabilirsiniz.
*   **Android Studio:** Android emülatörü için gereklidir.
*   **Xcode:** (Sadece macOS) iOS simülatörü için gereklidir.

## 2. Proje Dizinine Geçiş

Terminalinizde mobil uygulama projesinin bulunduğu klasöre gidin:

```bash
cd ../../zinzino
```

## 3. Bağımlılıkların Yüklenmesi

Proje klasöründeyken gerekli paketleri yükleyin:

```bash
npm install
```
veya (yarn kullanıyorsanız):
```bash
yarn install
```

## 4. Emülatörün Hazırlanması

### Android için:
1.  **Android Studio**'u açın.
2.  **Virtual Device Manager** (VDM) üzerinden bir sanal cihaz (AVD) oluşturun ve başlatın.
3.  `ANDROID_HOME` ortam değişkeninin tanımlı olduğundan emin olun.

### iOS için (Sadece macOS):
1.  **Xcode**'u açın.
2.  `Settings > Platforms` altından bir iOS simülatörü indirdiğinizden emin olun.

## 5. Uygulamayı Başlatma

Uygulamayı başlatmak için birkaç seçeneğiniz vardır:

### Seçenek A: Expo Geliştirici Menüsü ile (Önerilen)
Bu komut Expo sunucusunu başlatır ve size seçenekler sunar:
```bash
npx expo start
```
*   **'a'** tuşuna basarak Android emülatöründe açabilirsiniz.
*   **'i'** tuşuna basarak iOS simülatöründe açabilirsiniz.

### Seçenek B: Doğrudan Android/iOS Komutları ile
```bash
# Android için
npm run android

# iOS için
npm run ios
```

## 6. Sık Karşılaşılan Sorunlar ve Çözümleri

*   **"Command not found: expo":** Expo CLI'ın yüklü olduğundan emin olun veya komutların başına `npx` ekleyin.
*   **Önbellek (Cache) Sorunları:** Eğer uygulama garip hatalar veriyorsa önbelleği temizleyerek başlatın:
    ```bash
    npx expo start -c
    ```
*   **Native Modül Hataları:** Projede `react-native-wifi-reborn` gibi native bağımlılıklar olduğu için standart Expo Go uygulaması yerine **Development Build** kullanmanız gerekebilir. Bunun için:
    1.  Emülatör açıkken `npm run android` veya `npm run ios` komutunu kullanın. Bu komut uygulamayı emülatöre "build" ederek yükleyecektir.

## 7. Backend Bağlantısı

Mobil uygulamanın `zinzino-db` (backend) ile iletişim kurabilmesi için:
1.  Backend projesinin (`zinzino-db`) çalıştığından emin olun.
2.  Mobil uygulamadaki API URL ayarlarının emülatörün erişebileceği bir IP adresine (örneğin Android için `10.0.2.2`) ayarlandığını kontrol edin.
