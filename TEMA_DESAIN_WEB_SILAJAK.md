# Tema Desain Web SILAJAK

## 1. Konsep Desain

Tema desain SILAJAK dibuat dengan gaya modern, bersih, mudah dibaca, dan berfokus pada fungsi pelaporan jalan rusak. Tampilan web harus terasa resmi, terpercaya, dan mudah digunakan oleh masyarakat umum, admin, serta petugas lapangan.

Karena sistem ini berhubungan dengan laporan jalan, lokasi, peta, dan status penanganan, desain utama diarahkan pada tampilan dashboard, formulir laporan, map view, kartu status, dan tabel data.

## 2. Karakter Visual

Karakter visual yang disarankan:

- Bersih dan profesional
- Mudah dipahami oleh pengguna umum
- Menggunakan warna status yang jelas
- Mengutamakan peta dan data laporan
- Tidak terlalu ramai
- Cocok untuk penggunaan desktop dan mobile

## 3. Palet Warna

### 3.1 Warna Utama

| Nama Warna | Kode | Penggunaan |
| --- | --- | --- |
| Hijau Pemerintahan | `#1F7A4D` | Tombol utama, header, aksen utama |
| Biru Informasi | `#2563EB` | Link, informasi, lokasi peta |
| Abu Gelap | `#1F2937` | Teks utama |
| Abu Sedang | `#6B7280` | Teks sekunder |
| Abu Muda | `#F3F4F6` | Background halaman |
| Putih | `#FFFFFF` | Card, form, panel data |

### 3.2 Warna Status Laporan

| Status | Warna | Kode |
| --- | --- | --- |
| Menunggu Verifikasi | Kuning | `#F59E0B` |
| Diverifikasi | Biru | `#2563EB` |
| Ditolak | Merah | `#DC2626` |
| Ditugaskan ke Petugas | Ungu | `#7C3AED` |
| Dalam Penanganan | Oranye | `#EA580C` |
| Selesai | Hijau | `#16A34A` |

### 3.3 Warna Tingkat Kerusakan

| Tingkat Kerusakan | Warna | Kode |
| --- | --- | --- |
| Ringan | Hijau | `#22C55E` |
| Sedang | Kuning | `#EAB308` |
| Berat | Merah | `#EF4444` |

## 4. Tipografi

Font yang disarankan:

- `Inter`
- `Poppins`
- `Roboto`
- `Nunito Sans`

Rekomendasi penggunaan:

| Elemen | Ukuran |
| --- | --- |
| Judul halaman | 28px sampai 32px |
| Subjudul halaman | 20px sampai 24px |
| Judul card | 16px sampai 18px |
| Isi teks | 14px sampai 16px |
| Label form | 13px sampai 14px |
| Badge status | 12px sampai 13px |

## 5. Layout Utama

### 5.1 Layout Desktop

Layout desktop menggunakan sidebar di kiri dan area konten utama di kanan.

Struktur:

- Sidebar navigasi
- Topbar berisi nama halaman, pencarian, dan profil pengguna
- Area konten utama
- Card ringkasan
- Tabel laporan
- Map view
- Panel detail laporan

Contoh struktur:

```text
+------------------------------------------------------+
| Sidebar | Topbar                                     |
|         |--------------------------------------------|
|         | Konten utama                               |
|         |                                            |
|         | Card statistik | Map view | Tabel laporan  |
+------------------------------------------------------+
```

### 5.2 Layout Mobile

Layout mobile menggunakan bottom navigation atau menu hamburger agar mudah digunakan di layar kecil.

Struktur:

- Header ringkas
- Konten utama satu kolom
- Tombol aksi utama mudah dijangkau
- Bottom navigation untuk halaman penting

Menu mobile yang disarankan:

- Beranda
- Buat Laporan
- Riwayat
- Profil

## 6. Komponen Desain

### 6.1 Sidebar

Sidebar digunakan untuk admin dan petugas.

Menu admin:

- Dashboard
- Data Laporan
- Verifikasi
- Penugasan
- Petugas
- Rekap Data
- Pengaturan

Menu petugas:

- Dashboard
- Tugas Saya
- Riwayat Penanganan
- Profil

### 6.2 Topbar

Topbar berisi:

- Judul halaman
- Search bar
- Notifikasi
- Nama pengguna
- Menu profil

### 6.3 Card Statistik

Card statistik digunakan di dashboard admin untuk menampilkan ringkasan data.

Contoh card:

- Total laporan
- Menunggu verifikasi
- Dalam penanganan
- Selesai

Isi card:

- Ikon
- Angka utama
- Label
- Perubahan data jika diperlukan

### 6.4 Badge Status

Badge digunakan untuk menampilkan status laporan secara cepat.

Contoh:

```text
[Menunggu Verifikasi]
[Diverifikasi]
[Dalam Penanganan]
[Selesai]
```

Setiap badge wajib memakai warna sesuai status agar mudah dikenali.

### 6.5 Tabel Laporan

Tabel laporan digunakan oleh admin untuk melihat dan mengelola laporan.

Kolom tabel yang disarankan:

- Nomor
- Judul laporan
- Pelapor
- Ruas jalan
- Tingkat kerusakan
- Status laporan
- Tanggal laporan
- Aksi

Tabel harus mendukung:

- Pencarian
- Filter status
- Filter tanggal
- Filter tingkat kerusakan
- Pagination

## 7. Desain Form Buat Laporan

Form buat laporan dibuat sederhana agar masyarakat mudah mengisi laporan.

Field utama:

- Judul laporan
- Deskripsi kerusakan
- Map view untuk memilih ruas jalan
- Alamat otomatis dari lokasi jika tersedia
- Keterangan tambahan
- Upload foto atau video

Catatan penting:

- Upload foto atau video bersifat wajib.
- Pengguna tidak dapat mengirim laporan jika belum memilih ruas jalan di peta.
- Pengguna tidak dapat mengirim laporan jika belum mengunggah media.

## 8. Map View Pemilihan Ruas Jalan

Fitur lokasi menggunakan map view langsung, bukan hanya input alamat manual.

Pengguna dapat:

- Melihat peta wilayah
- Mencari nama jalan
- Memilih titik atau ruas jalan langsung pada peta
- Menggeser marker lokasi
- Melihat nama ruas jalan yang dipilih
- Menyimpan latitude dan longitude
- Menyimpan nama ruas jalan hasil pilihan peta

Komponen map view:

- Search lokasi
- Tombol gunakan lokasi saat ini
- Marker lokasi kerusakan
- Highlight ruas jalan yang dipilih
- Panel informasi lokasi

Data yang disimpan dari map view:

- Nama ruas jalan
- Alamat
- Latitude
- Longitude
- Kecamatan atau kelurahan jika tersedia

Rekomendasi library:

- Leaflet
- OpenStreetMap
- Mapbox
- Google Maps API

Untuk tahap awal, Leaflet dan OpenStreetMap cocok karena ringan dan gratis untuk prototipe.

## 9. Upload Foto atau Video

Area upload dibuat jelas dan besar agar pengguna mudah mengunggah bukti kerusakan jalan.

Ketentuan:

- Upload media wajib.
- Minimal 1 file harus diunggah.
- File dapat berupa foto atau video.
- Sistem menampilkan preview media sebelum laporan dikirim.
- Sistem menampilkan pesan error jika file belum diunggah.

Format yang disarankan:

- Foto: JPG, JPEG, PNG
- Video: MP4, MOV, AVI

Tampilan upload:

```text
+--------------------------------------+
| Upload Foto atau Video Jalan Rusak   |
|                                      |
| [Pilih File] atau drag and drop      |
|                                      |
| Preview media tampil di sini         |
+--------------------------------------+
```

## 10. Desain Hasil Deteksi Pothole

Hasil deteksi pothole dapat dilihat oleh semua jenis pengguna, tetapi tampilannya disesuaikan dengan kebutuhan masing-masing role.

### 10.1 Tampilan untuk Masyarakat

Masyarakat dapat melihat hasil deteksi pada detail laporan dan status laporan.

Informasi yang ditampilkan:

- Status deteksi
- Tingkat kerusakan
- Jumlah lubang terdeteksi jika tersedia
- Media hasil deteksi jika tersedia
- Catatan bahwa hasil deteksi tetap diverifikasi oleh admin

### 10.2 Tampilan untuk Admin

Admin melihat hasil deteksi sebagai bahan verifikasi.

Informasi yang ditampilkan:

- Media asli
- Media hasil deteksi
- Bounding box jika tersedia
- Jumlah lubang
- Confidence score
- Tingkat kerusakan otomatis
- Tombol setujui, tolak, atau ubah tingkat kerusakan

### 10.3 Tampilan untuk Petugas

Petugas melihat hasil deteksi untuk membantu memahami kondisi lokasi.

Informasi yang ditampilkan:

- Media hasil deteksi
- Tingkat kerusakan
- Lokasi kerusakan
- Catatan admin
- Status penanganan

## 11. Detail Laporan

Halaman detail laporan harus menampilkan informasi lengkap dalam susunan yang mudah dibaca.

Susunan halaman:

- Judul laporan
- Status laporan
- Tingkat kerusakan
- Informasi pelapor
- Deskripsi kerusakan
- Map lokasi
- Media unggahan
- Hasil deteksi pothole
- Riwayat status
- Catatan admin atau petugas

## 12. Dashboard Masyarakat

Dashboard masyarakat menampilkan ringkasan laporan milik pengguna.

Komponen:

- Tombol buat laporan baru
- Total laporan pengguna
- Laporan menunggu verifikasi
- Laporan dalam penanganan
- Laporan selesai
- Riwayat laporan terbaru

Fokus utama dashboard masyarakat adalah memudahkan pengguna membuat laporan dan memantau status laporan.

## 13. Dashboard Admin

Dashboard admin berfokus pada monitoring dan pengambilan keputusan.

Komponen:

- Card total laporan
- Card laporan menunggu verifikasi
- Card laporan dalam penanganan
- Card laporan selesai
- Grafik laporan per bulan
- Grafik tingkat kerusakan
- Map sebaran laporan
- Daftar laporan terbaru

Map dashboard admin menampilkan marker laporan berdasarkan status dan tingkat kerusakan.

## 14. Dashboard Petugas

Dashboard petugas berfokus pada daftar tugas dan status penanganan.

Komponen:

- Tugas baru
- Tugas dalam proses
- Tugas selesai
- Daftar tugas berdasarkan prioritas
- Map lokasi tugas
- Tombol update status

## 15. Gaya Tombol

Jenis tombol:

| Tombol | Warna | Fungsi |
| --- | --- | --- |
| Primary | Hijau | Aksi utama seperti kirim laporan |
| Secondary | Abu | Aksi tambahan |
| Info | Biru | Lihat detail |
| Warning | Kuning | Verifikasi atau proses |
| Danger | Merah | Tolak atau hapus |

Contoh tombol:

```text
[Buat Laporan]
[Kirim Laporan]
[Lihat Detail]
[Verifikasi]
[Tolak]
[Update Status]
```

## 16. Gaya Form

Form harus sederhana, rapi, dan mudah dipindai.

Aturan desain form:

- Label berada di atas input.
- Field wajib diberi tanda wajib.
- Error ditampilkan tepat di bawah input.
- Tombol submit berada di bagian bawah form.
- Field panjang menggunakan textarea.
- Map view dibuat lebih besar daripada input teks biasa.

Contoh validasi:

- Judul laporan wajib diisi.
- Deskripsi kerusakan wajib diisi.
- Ruas jalan wajib dipilih dari map view.
- Foto atau video wajib diunggah.

## 17. Ikon yang Disarankan

Ikon dapat menggunakan Lucide, Font Awesome, atau Bootstrap Icons.

Contoh ikon:

- Map pin untuk lokasi
- Camera untuk upload foto
- Video untuk upload video
- Alert triangle untuk kerusakan
- Check circle untuk selesai
- Clock untuk menunggu
- User untuk profil
- File text untuk laporan
- Bar chart untuk rekap

## 18. Wireframe Halaman Buat Laporan

```text
+------------------------------------------------------+
| Header                                               |
+------------------------------------------------------+
| Buat Laporan Jalan Rusak                             |
|                                                      |
| Judul Laporan                                        |
| [________________________________________]           |
|                                                      |
| Deskripsi Kerusakan                                  |
| [________________________________________]           |
| [________________________________________]           |
|                                                      |
| Pilih Ruas Jalan                                     |
| +--------------------------------------------------+ |
| |                    MAP VIEW                      | |
| |     Search jalan, pilih ruas, marker lokasi      | |
| +--------------------------------------------------+ |
| Ruas jalan terpilih: Jl. Contoh Raya                |
|                                                      |
| Upload Foto atau Video                              |
| +--------------------------------------------------+ |
| |          Upload wajib dan preview media          | |
| +--------------------------------------------------+ |
|                                                      |
| Keterangan Tambahan                                  |
| [________________________________________]           |
|                                                      |
| [Kirim Laporan]                                      |
+------------------------------------------------------+
```

## 19. Wireframe Detail Laporan

```text
+------------------------------------------------------+
| Detail Laporan                                       |
+------------------------------------------------------+
| Judul: Jalan berlubang di Jl. Contoh Raya            |
| Status: [Menunggu Verifikasi]                        |
| Tingkat Kerusakan: [Sedang]                          |
|                                                      |
| +-----------------------+ +------------------------+ |
| | Media Unggahan        | | Hasil Deteksi          | |
| | Foto atau video       | | Bounding box/status    | |
| +-----------------------+ +------------------------+ |
|                                                      |
| +--------------------------------------------------+ |
| | Map lokasi dan ruas jalan terpilih               | |
| +--------------------------------------------------+ |
|                                                      |
| Riwayat Status                                      |
| - Laporan dibuat                                    |
| - Deteksi pothole selesai                           |
| - Menunggu verifikasi admin                         |
+------------------------------------------------------+
```

## 20. Catatan Responsif

Desain harus nyaman digunakan di desktop dan mobile.

Aturan responsif:

- Tabel berubah menjadi card list di mobile.
- Sidebar berubah menjadi hamburger menu.
- Map view tetap terlihat besar dan mudah disentuh.
- Tombol utama dibuat penuh lebar di mobile.
- Upload media tetap menampilkan preview.
- Badge status tetap mudah dibaca.

## 21. Kesimpulan Tema

Tema desain SILAJAK mengutamakan tampilan yang bersih, informatif, dan berbasis peta. Pengguna diarahkan untuk memilih ruas jalan langsung melalui map view, wajib mengunggah foto atau video, lalu dapat melihat hasil deteksi pothole. Admin dan petugas mendapatkan tampilan dashboard yang lebih lengkap untuk verifikasi, penugasan, dan pemantauan penanganan jalan rusak.
