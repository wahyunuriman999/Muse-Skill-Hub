# google-sheets (`google-sheets`)

> Read, write, and manage the user's Google Sheets.

## Apa ini?

Skill `google-sheets` adalah salah satu kemampuan Muse. Deskripsi resmi: Read, write, and manage the user's Google Sheets.

## Kapan dipakai?

Ketika user minta baca/tulis spreadsheet, olah data tabular.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: google-sheets
Tujuan: Read, write, and manage the user's Google Sheets.
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*