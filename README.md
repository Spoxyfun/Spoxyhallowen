# Spooky Halloween — Spoxyhallowen

Situs + metadata koleksi **Spooky Halloween**: 10.000 NFT pixel di BNB Chain,
live di [spoxydev.fun](https://spoxydev.fun) (GitHub Pages, domain dari file `CNAME`).

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

## Status (2 Nov 2026)

- ✅ Situs live di spoxydev.fun
- ✅ Metadata lengkap 1–10.000, JSON valid, skema atribut konsisten
- ✅ Kontrak `SpookyHalloween.sol` selesai dan ter-compile bersih (solc 0.8.26, 0 error)
- ⏳ **Kontrak belum di-deploy** — tombol mint masih nonaktif & prompt Agent masih penanda
- ⏳ **Gambar koleksi belum di-upload** — kolom `image` di metadata menunjuk ke
  `collection-master-512/images/<id>.png`, folder itu belum ada di repo
  (URL gambar saat ini 404). Upload folder gambarnya ke root repo, atau ubah
  kolom `image` ke URL hosting gambar final sebelum kontrak live.

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
