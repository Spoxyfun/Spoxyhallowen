# Spooky Halloween — Spoxyhallowen

Situs + metadata koleksi **Spooky Halloween**: 10.000 NFT pixel di BNB Chain,
live di [spoxydev.fun](https://spoxydev.fun) (GitHub Pages, domain dari file `CNAME`).

Pengembang: [@SpoxyHallow_fun](https://x.com/SpoxyHallow_fun) di X (Twitter).

## Model koleksi

- **Satu pool bersama** #1–#10.000 untuk semua mint — tanpa pembagian fase.
- **Free mint** — NFT gratis, hanya fee **0,0001 BNB** per mint (`mintFree`).
- **Paid mint** — **0,001 BNB** per NFT (`mintPaid`).
- Setiap mint **diundi acak oleh kontrak** dari token yang belum ter-mint;
  nomor token tidak bisa dipilih dan tidak pernah terundi dua kali.
- Maksimal **10 NFT per transaksi** (sesuai stepper di situs).

## Isi repo

| Path | Isi |
| --- | --- |
| `index.html` | Situs satu halaman (ID/EN, galeri, mint, prompt AI Agent) |
| `assets/nft-01.webp` … `nft-12.webp` | 12 gambar contoh galeri |
| `metadata/1.json` … `10000.json` | Metadata ERC-721 untuk seluruh 10.000 token |
| `contracts/SpookyHalloween.sol` | Smart contract ERC-721 (mandiri, tanpa import) |
| `CNAME` | Domain GitHub Pages: `spoxydev.fun` |

## Status (3 Nov 2026)

- ✅ Situs live di spoxydev.fun
- ✅ Metadata lengkap 1–10.000, JSON valid, skema atribut konsisten
- ✅ Kontrak `SpookyHalloween.sol` selesai dan ter-compile bersih (solc 0.8.26, 0 error)
- ✅ **Kontrak LIVE di BNB Chain**: `0xC75B0003AC4A5FfaE3feb37278a03d503f344C3f`
  (tx deploy `0xc4afb1caf3a2313141b7cb3bb35aea65875a793946e871ba1acc93a50dc5538f`,
  blok 131280953, owner `0x5d372a27da80cfb00f27246b207fc119ce006992`)
- ✅ **Gambar koleksi lengkap & live** — token 1–1570 karya asli PNG,
  1571–10000 varian WebP dari 16 master AI + trait (sesuai metadata),
  #7000 & #10000 karya asli kreator
- ✅ **Mint TERBUKA** (`mintOpen = true`) — dibuka owner lewat
  [deploy.html](https://spoxydev.fun/deploy.html) pada 3 Nov 2026; tombol mint
  di situs aktif dan membaca status live dari chain
- ✅ `setBaseURI("https://spoxydev.fun/metadata/")` sudah diset owner
  (terverifikasi on-chain)

## Deploy kontrak (BNB Chain)

1. Buka [Remix](https://remix.ethereum.org), buat file dari
   `contracts/SpookyHalloween.sol`, compile dengan Solidity **0.8.20+**
   (optimizer ON, runs 200).
2. Deploy dari wallet owner ke **BNB Chain (chainId 56)**.
   Wallet deployer menjadi `owner` (penerima hasil withdraw).
3. Panggil `setBaseURI("https://spoxydev.fun/metadata/")`
   — `tokenURI(id)` menjadi `https://spoxydev.fun/metadata/<id>.json`.
4. Uji dulu di BNB Testnet (chainId 97) bila perlu; pola kontrak sama.
5. Panggil `setMintOpen(true)` untuk membuka mint.
6. Tempel alamat kontrak ke konstanta **`CONTRACT_ADDRESS`** di `index.html`
   (di awal `<script>`) — prompt AI Agent otomatis memakai alamat asli.
   Tombol mint di situs diaktifkan pada langkah rilis yang sama.
7. Verifikasi source code kontrak di BscScan.
8. Hasil mint (fee + paid) terkumpul di kontrak; tarik dengan `withdraw()`
   dari wallet owner.

> Catatan: undian on-chain memakai `block.prevrandao`/`blockhash` — cukup
> untuk undian koleksi ini, tetapi bukan randomness tahan-manipulasi
> validator (bukan VRF). Lihat komentar di header kontrak.
