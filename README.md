# Network Failover Automation using AI

Sistem otomatisasi failover jaringan yang memanfaatkan AI untuk mengelola perpindahan koneksi pada router MikroTik. Sistem ini memantau status interface, menganalisis metrik jaringan, dan secara otomatis mengalihkan koneksi ke upstream alternatif ketika diperlukan.

## Fitur Utama

- **Monitoring Interface**: Memantau status interface router (up/down), latensi, dan packet loss
- **Deteksi Otomatis**: Deteksi masalah jaringan berdasarkan metrik yang dikumpulkan
- **Failover Cerdas**: Pengambilan keputusan failover berdasarkan model AI
- **Dashboard Web**: Visualisasi status jaringan dan metrik secara real-time
- **Logging & Persistensi**: Penyimpanan data historis untuk analisis

## Prasyarat

- Python 3.8+
- Router MikroTik dengan RouterOS
- Set Top Box atau komputer kecil sebagai server untuk menjalankan aplikasi

## Instalasi

1. Clone repositori ini:
   ```bash
   git clone https://github.com/yourusername/network-failover-automation.git
   cd network-failover-automation
   ```

2. Buat virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/Mac
   # atau
   venv\Scripts\activate  # Untuk Windows
   ```

3. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. Buat file `.env` dan sesuaikan dengan konfigurasi Anda:
   ```bash
   cp .env.example .env
   # Edit file .env dengan editor teks
   ```

## Konfigurasi

Sesuaikan konfigurasi di `.env` dan `config/settings.py`:

- Alamat IP router MikroTik
- Kredensial login router
- Interface utama dan backup
- Parameter threshold untuk failover

## Penggunaan

1. Mulai aplikasi:
   ```bash
   python src/main.py
   ```

2. Buka dashboard web:
   ```
   http://localhost:5000
   ```

## Cara Kerja

1. **Monitoring**: Sistem terus memantau semua interface yang dikonfigurasi, mengumpulkan metrik seperti status, latensi, dan packet loss.

2. **Analisis**: Model AI menganalisis metrik yang dikumpulkan untuk mendeteksi anomali atau masalah potensial.

3. **Keputusan**: Berdasarkan analisis, sistem memutuskan apakah diperlukan failover dan interface mana yang harus digunakan.

4. **Eksekusi**: Jika failover diperlukan, sistem mengonfigurasi router untuk beralih ke interface alternatif.

5. **Pemulihan**: Sistem juga secara teratur memeriksa interface utama dan beralih kembali ketika sudah berfungsi normal.

## Struktur Proyek

```
network-failover-automation/
├── .env                           # File untuk kredensial/konfigurasi rahasia
├── .gitignore                     # File untuk mengabaikan file dalam git
├── README.md                      # Dokumentasi proyek
├── requirements.txt               # Dependensi Python
├── config/
│   ├── __init__.py
│   ├── settings.py                # Konfigurasi aplikasi
│   └── router_config.py           # Template konfigurasi router
├── src/
│   ├── __init__.py
│   ├── main.py                    # Titik masuk utama aplikasi
│   ├── router/
│   │   ├── __init__.py
│   │   ├── mikrotik.py            # Modul komunikasi MikroTik
│   │   └── interfaces.py          # Manajemen interface
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── collector.py           # Pengumpul metrik jaringan
│   │   └── persistence.py         # Penyimpanan data metrik
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── predictor.py           # Model AI untuk prediksi
│   │   └── training.py            # Pelatihan model
│   └── failover/
│       ├── __init__.py
│       ├── controller.py          # Kontroler failover utama
│       └── decision.py            # Engine pengambilan keputusan
├── dashboard/
│   ├── __init__.py
│   ├── app.py                     # Aplikasi Flask untuk dashboard
│   ├── routes.py                  # Rute API dashboard
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Stylesheet dashboard
│   │   └── js/
│   │       └── charts.js          # Kode JavaScript untuk chart
│   └── templates/
│       ├── index.html             # Halaman dashboard utama
│       └── base.html              # Template dasar HTML
└── tests/
    ├── __init__.py
    ├── test_router.py             # Unit test untuk komunikasi router
    ├── test_monitoring.py         # Unit test untuk monitoring
    └── test_failover.py           # Unit test untuk failover
```

## Pengembangan AI

Model AI dalam sistem ini dirancang untuk:

1. **Deteksi Anomali**: Mengidentifikasi pola abnormal dalam metrik jaringan
2. **Prediksi Kegagalan**: Memprediksi kegagalan interface sebelum benar-benar terjadi
3. **Optimasi Pemilihan**: Memilih interface alternatif terbaik berdasarkan metrik secara real-time

Anda dapat melatih model dengan data Anda sendiri dengan menggunakan modul `training.py`.

## Kontribusi

Kontribusi selalu diterima! Silakan buat pull request atau buka issue untuk saran dan perbaikan.

## Lisensi

[MIT License](LICENSE)
