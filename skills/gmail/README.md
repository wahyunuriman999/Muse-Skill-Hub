# gmail (`gmail`)

> Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments.

## Apa ini?

Skill `gmail` adalah salah satu kemampuan Muse. Deskripsi resmi: Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments.

## Kapan dipakai?

Ketika user minta baca, cari, balas, atau kelola email Gmail.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: gmail
Tujuan: Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage la
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*