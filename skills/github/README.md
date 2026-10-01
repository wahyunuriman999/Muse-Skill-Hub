# GitHub (`github`)

> Search and work with the user's GitHub repositories through GitHub's official MCP server.

## Apa ini?

Skill `github` adalah salah satu kemampuan Muse. Deskripsi resmi: Search and work with the user's GitHub repositories through GitHub's official MCP server.

## Kapan dipakai?

Ketika user menyebut repo, kode, PR, issue, atau minta tolong urusan GitHub.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: github
Tujuan: Search and work with the user's GitHub repositories through GitHub's official MCP server.
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*