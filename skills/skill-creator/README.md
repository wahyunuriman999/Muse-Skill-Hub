# skill-creator (`skill-creator`)

> Create or update a workspace skill: its description, structure, instructions, and supporting files.

## Apa ini?

Skill `skill-creator` adalah salah satu kemampuan Muse. Deskripsi resmi: Create or update a workspace skill: its description, structure, instructions, and supporting files.

## Kapan dipakai?

Ketika ingin membuat skill baru yang reusable dari workflow yang berhasil.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: skill-creator
Tujuan: Create or update a workspace skill: its description, structure, instructions, and supporting files.
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*