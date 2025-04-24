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

## Testing Menggunakan GNS3

Anda dapat menguji sistem failover ini menggunakan simulasi MikroTik di GNS3 sebelum implementasi pada perangkat fisik.

### Persiapan GNS3

1. **Instalasi GNS3 dan GNS3 VM**:
   ```bash
   # Unduh dan instal GNS3 dari https://gns3.com/software
   # Unduh GNS3 VM dari https://gns3.com/software/download-vm
   ```

2. **Siapkan Image MikroTik RouterOS**:
   - Unduh image RouterOS CHR (Cloud Hosted Router) dari situs MikroTik
   - Import image ke GNS3 sebagai appliance

3. **Buat Topologi Pengujian**:
   ```
   Internet (Cloud) --- [ether1] MikroTik Router [ether2] --- Komputer Pengujian
                          [ether3]
                             |
                      Jalur Backup/ISP Alternatif
   ```

### Konfigurasi MikroTik di GNS3

1. **Aktifkan API RouterOS**:
   ```
   /ip service enable api
   /ip service set api address=0.0.0.0/0
   ```

2. **Konfigurasi Interface Dasar**:
   ```
   /ip address add address=192.168.1.1/24 interface=ether1
   /ip address add address=192.168.2.1/24 interface=ether2
   /ip address add address=192.168.3.1/24 interface=ether3
   ```

3. **Konfigurasi Routing untuk Pengujian**:
   ```
   /ip route add dst-address=0.0.0.0/0 gateway=192.168.1.254 routing-mark=via-ether1
   /ip route add dst-address=0.0.0.0/0 gateway=192.168.3.254 routing-mark=via-ether3 distance=10
   ```

### Menjalankan Pengujian dengan GNS3

1. **Penyesuaian Konfigurasi**:
   - Sesuaikan file `.env` untuk terhubung ke MikroTik di GNS3:
   ```
   MIKROTIK_HOST=192.168.2.1  # IP MikroTik dari sisi komputer pengujian
   MIKROTIK_USER=admin
   MIKROTIK_PASSWORD=password
   PRIMARY_INTERFACE=ether1
   SECONDARY_INTERFACES=ether3
   ```

2. **Pengujian Dasar**:
   - Jalankan aplikasi dan verifikasi koneksi ke router
   - Periksa dashboard untuk memastikan metrik diambil dengan benar

3. **Simulasi Kegagalan**:
   - Simulasikan kegagalan interface primer dengan menonaktifkan interface di MikroTik:
   ```
   /interface disable ether1
   ```
   - Atau tambahkan latency/packet loss untuk memicu failover:
   ```
   /queue simple add target=0.0.0.0/0 interface=ether1 packet-mark=no-mark limit-at=512k/512k max-limit=1M/1M queue=default/default packet-loss=20%
   ```

4. **Verifikasi Failover**:
   - Periksa log aplikasi dan dashboard untuk memastikan failover terjadi
   - Verifikasi bahwa traffic dialihkan ke interface sekunder

5. **Pengujian Pemulihan**:
   - Aktifkan kembali interface primer:
   ```
   /interface enable ether1
   ```
   - Atau hapus pembatasan:
   ```
   /queue simple remove [find target=0.0.0.0/0 interface=ether1]
   ```
   - Verifikasi sistem kembali ke interface utama setelah beberapa saat

### Integrasi dengan CI/CD untuk Automated Testing

Anda dapat mengotomatisasi pengujian GNS3 dengan menggunakan GNS3 Server API:

```python
# Contoh script untuk otomatisasi pengujian
import requests
import time

# Connect to GNS3 API
gns3_api = "http://localhost:3080/v2"

# Disable primary interface
requests.put(f"{gns3_api}/projects/{project_id}/links/{link_id}/stop")

# Wait and check if failover occurs
time.sleep(30)

# Re-enable primary interface
requests.put(f"{gns3_api}/projects/{project_id}/links/{link_id}/start")

# Check metrics and events in the database
```

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
