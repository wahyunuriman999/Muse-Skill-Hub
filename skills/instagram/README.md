# instagram (`instagram`)

> Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile details, and publish stories, reels, posts, or carousels on request.

## Apa ini?

Skill `instagram` adalah salah satu kemampuan Muse. Deskripsi resmi: Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile details, and publish stories, reels, posts, or carousels on request.

## Kapan dipakai?

Ketika user kasih link Instagram atau minta baca/posting Instagram.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: instagram
Tujuan: Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer q
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*