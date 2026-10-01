# spotify (`spotify`)

> Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify.

## Apa ini?

Skill `spotify` adalah salah satu kemampuan Muse. Deskripsi resmi: Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify.

## Kapan dipakai?

Ketika user minta cari musik, bikin playlist, atau kelola Spotify.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: spotify
Tujuan: Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created wi
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*