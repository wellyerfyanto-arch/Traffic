# 🌐 Google Traffic Simulator

Aplikasi web untuk mensimulasikan traffic website yang realistis dengan fitur proxy rotation dan user agent rotation.

## ✨ Fitur Utama

- 🔄 **Proxy Rotation** - Support multiple proxy dengan format IP:PORT atau http://proxy:port
- 🆔 **User Agent Rotation** - Random user agent setiap sesi
- 🛡️ **IP Leak Check** - Memeriksa kebocoran data sebelum melanjutkan
- 🎯 **Realistic Behavior** - Scroll acak, klik postingan, handling iklan
- 📊 **Real-time Monitoring** - Dashboard dengan stats live
- 🔧 **Easy Configuration** - Input proxy list langsung di web interface
- ⚡ **Multi-session** - Jalankan multiple sessions bersamaan

## 🗺️ Panduan Instalasi & Deployment

### Step 1: Fork Repository GitHub

1. **Buat repository baru** di GitHub
2. **Upload semua file** ke repository:
   - `app.py`
   - `requirements.txt`
   - `build.sh`
   - `runtime.txt`
   - Folder `templates/` dengan `index.html`

### Step 2: Deploy di Render

1. **Daftar/Login** ke [Render.com](https://render.com)

2. **Create New Web Service**
   - Klik "New+" → "Web Service"
   - Connect ke GitHub account Anda
   - Pilih repository yang sudah dibuat

3. **Konfigurasi Build Settings:**
   - **Name**: `google-traffic-simulator` (atau sesuai preferensi)
   - **Environment**: `Python 3`
   - **Region**: `Singapore` (atau terdekat)
   - **Branch**: `main`
   - **Root Directory**: (kosongkan)
   - **Build Command**: 
     ```bash
     chmod +x build.sh && ./build.sh
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app
     ```

4. **Advanced Settings** (opsional):
   - **Plan**: `Free` (untuk mulai)
   - **Auto-Deploy**: `Yes`

5. **Klik "Create Web Service"**

6. **Tunggu deployment selesai** (5-10 menit)

### Step 3: Konfigurasi Aplikasi

1. **Dapatkan Proxy** (Opsional):
   - Free proxies: [FreeProxyList](https://free-proxy-list.net/)
   - Paid proxies: [BrightData](https://brightdata.com/), [Oxylabs](https://oxylabs.io/)
   - Telegram: Cari channel proxy provider

2. **Format Proxy yang Didukung**:
