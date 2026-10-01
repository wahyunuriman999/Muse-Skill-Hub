# image-search (`image-search`)

> Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person.

## Apa ini?

Skill `image-search` adalah salah satu kemampuan Muse. Deskripsi resmi: Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person.

## Kapan dipakai?

Ketika butuh referensi visual dari web untuk ditampilkan.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: image-search
Tujuan: Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not ident
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*