# Semweb-AksaraJawa
=====================
# 📜 Sistem Pencarian Naskah Jawa

Aplikasi web untuk pencarian teks dalam naskah Jawa dengan dukungan Aksara Jawa dan transliterasi Latin. Sistem ini terintegrasi dengan GraphDB untuk manajemen data semantik dan menyediakan antarmuka pencarian yang intuitif.

## 🌐 Akses Langsung

**Demo Online:** [https://semweb-aksarajawa.streamlit.app/](https://semweb-aksarajawa.streamlit.app/)

**Repository:** [https://github.com/Tabinaadeliarafa/Semweb-AksaraJawa.git](https://github.com/Tabinaadeliarafa/Semweb-AksaraJawa.git)

## ✨ Fitur Utama

- **Pencarian Multi-format**: Mendukung pencarian dalam Aksara Jawa, Latin, dan terjemahan Indonesia
- **Keyboard Aksara Jawa Virtual**: Interface keyboard yang user-friendly untuk input Aksara Jawa
- **Highlighting Presisi**: Menandai hasil pencarian dengan word boundary yang akurat
- **Integrasi GraphDB**: Koneksi langsung dengan repository GraphDB untuk data semantik
- **Hasil Terstruktur**: Menampilkan hasil pencarian yang dikelompokkan berdasarkan jenis (Kata/Paragraf)
- **Interface Responsif**: Desain modern dan responsif dengan CSS kustom

## 🚀 Panduan Instalasi

### Prasyarat Sistem

- Python 3.8 atau lebih tinggi
- GraphDB Server (untuk produksi) atau akses ke endpoint GraphDB
- pip package manager

### Langkah Instalasi

1. **Clone Repository**
   ```bash
   git clone https://github.com/Tabinaadeliarafa/Semweb-AksaraJawa.git
   cd Semweb-AksaraJawa
   ```

2. **Buat Virtual Environment (Opsional)**
   ```bash
   python -m venv semweb-env
   source semweb-env/bin/activate  # Linux/Mac
   # atau
   semweb-env\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Atau install manual:
   ```bash
   pip install streamlit pandas SPARQLWrapper pathlib

4. **Pastikan Konfigurasi GraphDB Dapat Jalan**
   
   Pastikan GraphDB Server berjalan dan repository 'AksaraJawa' telah dibuat dengan data yang sesuai. Endpoint default: `http://localhost:7200/repositories/AksaraJawa`

5. **Jalankan Aplikasi**
   ```bash
   streamlit run app.py
   ```

   Aplikasi akan tersedia di: `http://localhost:8501`

## 📋 Panduan Pengguna

### Memulai Pencarian

1. **Akses Aplikasi**: Buka browser dan navigasi ke URL aplikasi
2. **Input Pencarian**: 
   - Gunakan text input untuk mengetik kata/frasa
   - Atau gunakan keyboard Aksara Jawa virtual untuk input aksara
3. **Pilih Jenis Pencarian**:
   - **Semua**: Mencari di semua format teks
   - **Latin**: Khusus teks Latin
   - **Aksara Jawa**: Khusus teks Aksara Jawa
   - **Terjemahan**: Khusus terjemahan Indonesia
4. **Klik Tombol "Cari"** untuk menjalankan pencarian

### Menggunakan Keyboard Aksara Jawa

1. **Buka Keyboard**: Klik "Tampilkan/Sembunyikan Keyboard Aksara Jawa"
2. **Pilih Karakter**: Klik karakter yang diinginkan dari kategorisasi:
   - **Aksara Dasar**: Karakter konsonan utama
   - **Sandhangan Vokal**: Tanda vokal
   - **Tanda Baca & Simbol**: Simbol khusus Jawa
3. **Edit Teks**: Gunakan tombol "⌫ Hapus Karakter Terakhir" untuk koreksi
4. **Pencarian**: Teks yang diinput akan otomatis muncul di field pencarian

### Membaca Hasil Pencarian

- **Hasil Terkelompok**: Dibagi berdasarkan jenis (Kata/Paragraf)
- **Highlighting**: Kata yang dicari akan disorot
- **Detail Lengkap**: Setiap hasil menampilkan:
  - Teks Aksara Jawa asli
  - Transliterasi Latin
  - Terjemahan Indonesia
  - Referensi paragraf
  - Indikator lokasi ditemukan

### Fitur Tambahan

- **Contoh Pencarian**: Klik untuk mengisi kata contoh
- **Bersihkan**: Hapus semua input pencarian
- **Info Dataset**: Lihat statistik data dan koneksi GraphDB

## 🔧 Contoh Hasil Penggunaan

### Pencarian Kata "punika"

**Input**: `punika`
**Jenis Pencarian**: Semua

**Hasil**:
```
📝 Hasil Pencarian
Ditemukan 15 kemunculan untuk "punika"

📑 Kata (10 kemunculan)
└── Kata: 'punika' (Total: 10)
    ├── Informasi Utama
    │   ├── Kata/Frasa: punika
    │   ├── Aksara Jawa: ꦥꦸꦤꦶꦏ
    │   └── Arti: ini, tersebut
    └── Detail Setiap Kemunculan:
        ├── [Kata] Paragraf: P001_01
        │   ├── Aksara Jawa: ꦥꦸꦤꦶꦏ
        │   ├── Latin: punika
        │   ├── Terjemahan: ini
        │   └── Ditemukan dalam: 🔹 Latin | 🔸 Aksara Jawa

📑 Paragraf (5 kemunculan)
└── Paragraf: P001_02 - Mengandung 'punika' (Total: 5)
    ├── Informasi Utama
    │   ├── Kata/Frasa: Mencari: punika
    │   ├── Aksara Jawa: ...ꦱꦼꦂꦫꦠ꧀‌ꦏꦒꦸꦁꦔꦤ꧀ꦤꦶꦥꦸꦤꦶꦏ‌ꦱꦼꦂ‌...
    │   └── Arti: ...serat kagunga punika ser...
```

### Pencarian Aksara Jawa "ꦥꦸꦤꦶꦏ"

**Input**: `ꦥꦸꦤꦶꦏ`
**Jenis Pencarian**: Aksara Jawa

**Hasil**:
```
📝 Hasil Pencarian
Ditemukan 8 kemunculan untuk "ꦥꦸꦤꦶꦏ"

📑 Kata (8 kemunculan)
└── Kata: 'ꦥꦸꦤꦶꦏ' (Total: 8)
    ├── Informasi Utama
    │   ├── Kata/Frasa: ꦥꦸꦤꦶꦏ
    │   ├── Aksara Jawa: ꦥꦸꦤꦶꦏ
    │   └── Arti: ini, tersebut
    └── [Hasil detail...]
```

## 🛠️ Struktur File

```
Semweb-AksaraJawa/
├── .devcontainer/
│   └── devcontainer.json       # Konfigurasi environment container
├── dataset/
│   └── pupuh.csv               # Dataset naskah pupuh dalam format CSV
├── RDF/
│   └── pupuh.ttl               # Dataset RDF dalam format Turtle (TTL)
├── app.py                      # Aplikasi utama Streamlit
├── README.md                   # Dokumentasi proyek
├── requirements.txt            # Daftar dependensi Python
├── styles.css                  # Stylesheet kustom untuk aplikasi
```

## 🔍 Detail Teknis

### Arsitektur Sistem

- **Frontend**: Streamlit dengan CSS kustom
- **Backend**: Python dengan pandas untuk manipulasi data
- **Database**: GraphDB dengan SPARQL endpoint
- **Search Engine**: Regex-based dengan word boundary detection
- **Character Encoding**: Unicode support untuk Aksara Jawa (U+A980-U+A9DF)

### Fitur Pencarian Presisi

- **Word Boundary Detection**: Menggunakan regex dengan pembatas kata yang tepat
- **Multi-language Support**: Deteksi otomatis bahasa input (Latin/Jawa)
- **Context Extraction**: Menampilkan konteks di sekitar kata yang ditemukan
- **Exact Match**: Pencarian kata utuh, bukan substring

### SPARQL Query

Aplikasi menjalankan query SPARQL untuk mengambil data:

```sparql
PREFIX ex: <http://example.org/pupuh#>
SELECT ?s ?type ?isiLatin ?isiAksaraJawa ?arti ?munculDalamParagraf
WHERE {
    {
        ?s a ex:Paragraf .
        OPTIONAL { ?s ex:isiLatin ?isiLatin . }
        OPTIONAL { ?s ex:isiAksaraJawa ?isiAksaraJawa . }
        OPTIONAL { ?s ex:arti ?arti . }
        BIND("Paragraf" AS ?type)
    } UNION {
        ?s a ex:Kata .
        OPTIONAL { ?s ex:latin ?isiLatin . }
        OPTIONAL { ?s ex:aksaraJawa ?isiAksaraJawa . }
        OPTIONAL { ?s ex:arti ?arti . }
        OPTIONAL { ?s ex:munculDalamParagraf ?munculDalamParagrafUri . }
        BIND("Kata" AS ?type)
    }
}
```

## 🐛 Troubleshooting

### Masalah Koneksi GraphDB

**Error**: "Error loading data from GraphDB"

**Solusi**:
1. Pastikan GraphDB Server berjalan
2. Verifikasi URL endpoint di kode (default: localhost:7200)
3. Cek repository 'AksaraJawa' sudah dibuat dan berisi data
4. Pastikan tidak ada firewall yang memblokir koneksi

### Masalah Dependencies

**Error**: "ModuleNotFoundError"

**Solusi**:
```bash
pip install --upgrade streamlit pandas SPARQLWrapper
```

### Masalah CSS

**Warning**: "File styles.css tidak ditemukan"

**Solusi**:
1. Pastikan file `styles.css` ada di direktori yang sama dengan `app.py`
2. Atau buat file CSS kosong jika tidak memiliki styling kustom

### Performance Issues

**Masalah**: Aplikasi lambat saat pencarian

**Solusi**:
1. Pastikan menggunakan `@st.cache_data` untuk caching
2. Optimasi query SPARQL jika dataset besar
3. Batasi jumlah hasil yang ditampilkan

## 📚 Referensi

### Sumber Data
- **Data Aksara Jawa**: [Wikisource Bahasa Jawa - Serat Piwulang](https://jv.wikisource.org/wiki/%EA%A6%B1%EA%A6%BC%EA%A6%AB%EA%A6%A0%EA%A7%80%EA%A6%B1%EA%A6%BA%EA%A6%AD%EA%A6%AB%EA%A6%B1/01)

### Pustaka Ilmiah
- **Implementasi Keyboard**: Mahastama, A. W. (2022). Model berbasis aturan untuk transliterasi bahasa jawa dengan aksara latin ke aksara jawa. *Jurnal Buana Informatika*, 13(02), 146-154. https://ojs.uajy.ac.id/index.php/jbi/article/view/6526

### Teknologi yang Digunakan
- [Streamlit](https://streamlit.io/) - Framework web app Python
- [Pandas](https://pandas.pydata.org/) - Library manipulasi data
- [SPARQLWrapper](https://sparqlwrapper.readthedocs.io/) - Python wrapper untuk SPARQL
- [GraphDB](https://graphdb.ontotext.com/) - Database semantik

## 📞 Kontak

Untuk pertanyaan atau dukungan, silakan buka issue di repository GitHub atau hubungi tim pengembang.
- Reghina Maisarah (https://www.linkedin.com/in/reghinamaisarah/)
- Nabila Rahmanisa Putri A. (https://www.linkedin.com/in/nabila-rahmanisa-putri-arzetta/)
- Tabina Adelia Rafa (https://www.linkedin.com/in/tabinaadeliarafa/)    
---

**Dikembangkan dengan semangat untuk pelestarian budaya dan bahasa Jawa**