# 🎬 Tam Ekran Video Oynatıcı / Full Screen Video Player

Windows için tasarlanmış, **Netflix, YouTube ve tüm video platformlarını** adres çubuğu, sekmeler ve pencere kenarlığı olmadan **tamamen çerçevesiz, 16:9 oranını koruyarak** açan hafif ve modern bir masaüstü video oynatıcı.

---

[English Documentation](#-english-documentation) | [Türkçe Dokümantasyon](#-türkçe-dokümantasyon)

---

## 🇹🇷 Türkçe Dokümantasyon

### 🎯 Amaç ve Çözüm
- **DRM ve Widevine Desteği:** Standart `pywebview` veya `PyQt WebEngine` gömülü tarayıcıları, DRM koruması (Widevine) lisansına sahip olmadıkları için Netflix, Prime Video gibi platformlarda videoları oynatamaz.
- **Yerel Tarayıcı Uygulama Modu (`--app`):** Bu uygulama, sistemde kurulu olan Google Chrome veya Microsoft Edge'i özel bir kullanıcı profili (`--user-data-dir=profil`) ve `--app` bayrağıyla başlatır. Böylece hem Netflix/YouTube oturumlarınız hatırlanır hem de DRM korumalı videolar sorunsuz çalışır.
- **Çerçevesiz İstemci Görünümü:** Win32 API (`SetWindowRgn`) kullanılarak tarayıcının tüm başlık çubuğu ve çerçeveleri kırpılır; geriye yalnızca video oynatıcı alanı kalır.
- **Otomatik 16:9 Oran Koruması:** Pencere boyutu değiştiğinde video en-boy oranı arka planda sessizce korunur.

---

### ✨ Özellikler

1. **Tamamen Çerçevesiz Pencere:** Başlık çubuğu, kenarlıklar veya buton kalabalığı yok.
2. **16:9 En-Boy Oranı Kilidi:** Pencereyi yeniden boyutlandırdığınızda 16:9 sinematik oran otomatik olarak korunur.
3. **Akıllı Üst Tutma Barı (Gizlenebilir Overlay):**
   - Fareyi video alanının en üst kenarına (ilk 6 piksel) getirdiğinizde yumuşak bir animasyonla açılır.
   - **Taşıma Tutamacı:** Pencereyi ekranın dilediğiniz yerine sürüklemenizi sağlar.
   - **Sol & Sağ Boyutlandırma:** Üst kenar sabit kalarak pencereyi 16:9 oranında büyütüp küçültebilirsiniz.
   - **📌 Her Zaman Üstte:** Diğer pencerelerin üzerinde kalmasını sağlar.
   - **✕ Kapat Butonu:** Video penceresini tek tıkla kapatır.
   - Fare üzerinden çekildiğinde veya 1.5 saniye hareketsiz kalındığında otomatik olarak yukarı kayarak gizlenir.
4. **Klavye Kısayolları (Video Penceresi Odaktayken):**
   - `Ctrl + Shift + T`: "Her zaman üstte" modunu açar / kapatır.
   - `Ctrl + Shift + R`: Pencereyi varsayılan 1280x720 boyutuyla ekranın ortasına sıfırlar.
   - `Ctrl + Shift + B`: Çerçevesiz modu açar / kapatır (ihtiyaç halinde standart pencereye döner).
5. **Çoklu Dil Desteği (i18n):** `lang/` klasörü üzerinden kolayca yeni diller eklenebilir.

---

### 🚀 Kurulum ve Çalıştırma

#### 1. Gereksinimler
- Windows 10 veya Windows 11
- Python 3.8+
- Google Chrome veya Microsoft Edge

#### 2. Çalıştırma
En kolay yol:
1. Depoyu klonlayın veya zip olarak indirin.
2. Klasördeki **`baslat.bat`** dosyasına çift tıklayın.
   *(Eksik kütüphaneler otomatik olarak yüklenecektir).*

Alternatif manuel çalıştırma:
```bash
pip install -r requirements.txt
python main.py
```

---

### 🌐 Yeni Dil Ekleme Rehberi

Uygulama, `lang/` klasöründeki tüm JSON dil dosyalarını dinamik olarak algılar. Yeni bir dil eklemek için:

1. **`lang/`** klasörüne gidin.
2. Mevcut `en.json` veya `tr.json` dosyasını kopyalayın ve hedef dilin koduyla adlandırın (örneğin Almanca için `de.json`, İspanyolca için `es.json`, Fransızca için `fr.json`).
3. Dosyayı bir metin düzenleyiciyle açıp anahtarların karşılığını çevirin:

```json
{
  "app_title": "Full Screen Video Player",
  "title": "Full Screen Video Player",
  "placeholder_link": "Paste Netflix / YouTube / video link",
  "btn_paste": "Paste",
  "recent_empty": "No recent links",
  "recent_header": "Recent Links",
  "chk_fullscreen": "True fullscreen (F11)",
  "btn_open": "OPEN",
  "err_empty_link": "Please enter a video link.",
  "err_browser_not_found": "Google Chrome or Microsoft Edge not found!\nPlease install one.",
  "err_window_not_found": "Browser window could not be captured.",
  "err_launch_failed": "Launch error: {error}",
  "pin_tooltip": "Always on top",
  "close_tooltip": "Close"
}
```

4. Uygulamayı yeniden başlattığınızda yeni dil, sağ üstteki dil açılır menüsünde (örneğin `DE`, `ES`) otomatik olarak listelenecektir.

---
---

## 🇬🇧 English Documentation

### 🎯 Purpose & Approach
- **DRM & Widevine Support:** Standard embedded web engines like `pywebview` or `PyQt WebEngine` lack official Widevine DRM licensing, preventing playback on DRM-protected streaming services like Netflix and Prime Video.
- **Native Browser App Mode (`--app`):** This application launches your locally installed Google Chrome or Microsoft Edge using dedicated profile data (`--user-data-dir=profil`) and the `--app` flag. This preserves logins, cookies, and ensures smooth DRM playback.
- **Frameless Borderless Client Area:** Uses Windows Win32 API (`SetWindowRgn`) to clip away the title bar, borders, and tabs, leaving pure video content.
- **Automatic 16:9 Aspect Ratio Enforcement:** Continuously and silently preserves the 16:9 cinematic aspect ratio during window resizing.

---

### ✨ Key Features

1. **Zero-Chrome Borderless Mode:** No address bar, no tabs, no native borders.
2. **Fixed 16:9 Aspect Ratio:** Automatically corrects sizing discrepancies in real time.
3. **Smart Top Control Bar (Slide-down Overlay):**
   - Appears with a smooth slide-down animation when hovering over the top 6 pixels of the video client area.
   - **Move Grip:** Drag the window anywhere across monitors.
   - **Corner Sizing Grips:** Resize with fixed top edges while strictly preserving 16:9 proportions.
   - **📌 Always-on-Top:** Pin the player above all other windows.
   - **✕ Close Button:** Safely closes the video instance.
   - Automatically hides when the mouse leaves or remains idle for 1.5 seconds.
4. **Global Hotkeys (When Video Window is Focused):**
   - `Ctrl + Shift + T`: Toggle Always-on-Top mode.
   - `Ctrl + Shift + R`: Reset window to 1280x720 centered on the current display.
   - `Ctrl + Shift + B`: Toggle borderless mode on/off.
5. **Dynamic Internationalization (i18n):** Easy translation by adding JSON files in the `lang/` folder.

---

### 🚀 Getting Started

#### 1. Prerequisites
- Windows 10 or 11
- Python 3.8+
- Google Chrome or Microsoft Edge

#### 2. Running
- Double-click **`baslat.bat`** (it automatically verifies dependencies and starts the app).
- Or run via terminal:
  ```bash
  pip install -r requirements.txt
  python main.py
  ```

---

### 🌐 How to Add a New Language

1. Navigate to the **`lang/`** directory.
2. Copy `en.json` and rename it to your target language code (e.g., `es.json` for Spanish, `de.json` for German, `fr.json` for French).
3. Translate the values corresponding to the keys.
4. Restart the app. Your language code will automatically appear in the top-right language selector!

---

### 📄 License
This project is open-source and available under the [MIT License](LICENSE).
