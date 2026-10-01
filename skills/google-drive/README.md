# google-drive (`google-drive`)

> Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.

## Apa ini?

Skill `google-drive` adalah salah satu kemampuan Muse. Deskripsi resmi: Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.

## Kapan dipakai?

Ketika user minta cari, baca, atau kelola file di Google Drive.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: google-drive
Tujuan: Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*