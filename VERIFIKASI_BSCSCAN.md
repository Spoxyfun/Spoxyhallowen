# Paket Verifikasi Kontrak di BscScan — Spooky Halloween

Sudah diuji Muse 2026-11-03: source code di repo dikompilasi ulang dengan persis
pengaturan di bawah dan hasilnya **identik byte-per-byte** dengan kode kontrak yang
sudah terpasang on-chain (runtime 7.308 byte, termasuk hash metadata — *full match*).
Jadi verifikasi ini pasti diterima BscScan.

## Data kontrak

| Kolom | Nilai |
|---|---|
| Contract Address | `0xC75B0003AC4A5FfaE3feb37278a03d503f344C3f` |
| Compiler Version | `v0.8.26+commit.8a97fa7a` |
| License | MIT License (MIT) — SPDX di baris 1 source |
| Optimization | Yes, 200 runs |
| EVM Version | default |
| Constructor Arguments | *(kosong — tidak ada)* |
| Nama file sumber | `contracts/SpookyHalloween.sol` |

## Cara kirim (perlu akun BscScan gratis — ±2 menit)

1. Login / daftar di https://bscscan.com
2. Buka tautan verifikasi (alamat sudah terisi otomatis):
   https://bscscan.com/verifyContract?a=0xC75B0003AC4A5FfaE3feb37278a03d503f344C3f
3. Isi formulir:
   - **Compiler Type:** `Solidity (Standard-Json-Input)`
   - **Compiler Version:** `v0.8.26+commit.8a97fa7a`
   - **Open Source License Type:** `MIT License (MIT)`
4. Tempel **seluruh isi file `bscscan-standard-json.json`** (ada di folder repo ini)
   ke kotak "Standard-Json-Input" — atau unggah filenya bila ada tombol upload.
5. Centang captcha → klik **Verify and Publish**.

## Setelah berhasil

- Halaman kontrak menampilkan nama **Spooky Halloween (SPOOKY)**.
- Tab **Contract** berubah jadi terverifikasi: muncul **Code**, **Read Contract**,
  dan **Write Contract**.
- Token muncul rapi di BscScan Token Tracker sebagai SPOOKY.

## Alternatif: metode Single File

Bila formulir Standard-Json bermasalah, pilih Compiler Type
`Solidity (Single file)`, versi compiler sama, Optimization **Yes**, Runs **200**,
lisensi MIT, lalu tempel isi file `contracts/SpookyHalloween.sol`.
