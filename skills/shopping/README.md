# shopping (`shopping`)

> Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, including buying or browsing Facebook Marketplace listings. Use when presenting shopping search results from any source. For shopping intent, load this skill first before any other skills.

## Apa ini?

Skill `shopping` adalah salah satu kemampuan Muse. Deskripsi resmi: Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, including buying or browsing Facebook Marketplace listings. Use when presenting shopping search results from any source. For shopping intent, load this skill first before any other skills.

## Kapan dipakai?

Ketika user minta cari/bandingkan/beli produk.

## Pola umum

- **Read dulu, write dengan persetujuan**: operasi baca didahulukan untuk verifikasi, operasi tulis selalu minta konfirmasi.
- **Verifikasi sebelum klaim**: cek status koneksi dan akses sebelum bilang bisa.
- **Jangan asal nebak**: kalau butuh info live (harga, jadwal, ketersediaan), cek sumber live, bukan dari ingatan.

## Contoh pola adaptasi untuk LLM lain

```
Skill: shopping
Tujuan: Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare
Input: kebutuhan user yang jelas + parameter terstruktur
Output: hasil terverifikasi + sumbernya
Aturan: pisahkan read vs write, minta approval untuk write
```

---
*Disanitasi dari dokumentasi internal Muse — hanya pola publik yang dibagikan.*