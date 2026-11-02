#!/usr/bin/env python3
"""
Bangun 10.000 varian gambar Spooky Halloween dari 16 gambar dasar master
(masters/master-<slug>.png, gaya AI kaya, langit polos + bulan pucat).

Setiap varian menerapkan trait token dari metadata/<id>.json:
  Moon        -> bulan dideteksi lalu diwarnai ulang (Pale/Original/Blood/Lavender)
  Sky         -> bintang dan/atau kelelawar digambar prosedural (seed = id token)
  Night Grade -> grading warna (Original/Warm/Cool/Deep)
  Frame       -> bingkai (None/Purple/Orange/Checker)
  Finish      -> Vivid / Matte
  Mirror      -> Yes membalik gambar di langkah terakhir

Dua token memakai gambar asli dari kreator dan tidak ditimpa:
  #10000 (Ghost Puppy) dan #7000 (Pumpkin Bear) — lihat ORIGINALS.

Keluaran: collection-master-512/images/<id>.webp (512x512).
"""
import json
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
META_DIR = os.path.join(ROOT, "metadata")
MASTERS_DIR = os.path.join(ROOT, "masters")
OUT_DIR = os.path.join(ROOT, "collection-master-512", "images")
SIZE = 512

MOON_TARGETS = {
    "Pale": (243, 238, 214),
    "Original": (250, 196, 92),
    "Blood": (226, 62, 52),
    "Lavender": (190, 156, 255),
}
# Gambar asli kreator untuk token tertentu. Direktori sumber dapat
# dioverride lewat SPOXY_ORIGINALS_DIR (dipakai CI); nama file di dalamnya
# mengikuti pola <id>.png bila variabel itu diset.
_ORIG_DIR = os.environ.get("SPOXY_ORIGINALS_DIR")
if _ORIG_DIR:
    ORIGINALS = {10000: os.path.join(_ORIG_DIR, "10000.png"),
                 7000: os.path.join(_ORIG_DIR, "7000.png")}
else:
    ORIGINALS = {
        10000: os.path.expanduser("~/workspace/user/media_library/image/Token__10000_Anjing_Hantu_512.png"),
        7000: os.path.expanduser("~/workspace/user/media_library/image/Token__7000_Beruang_Labu.png"),
    }

_master_cache = {}


def slug(master):
    return "master-" + master.lower().replace(" ", "-")


def load_master(master):
    if master not in _master_cache:
        p = os.path.join(MASTERS_DIR, slug(master) + ".png")
        _master_cache[master] = Image.open(p).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    return _master_cache[master].copy()


# ------------------------------------------------------------------ bulan
def find_moon(img):
    """Deteksi cakram bulan pucat di area langit kanan-atas gambar.

    Hanya komponen terang yang kompak menyerupai cakram, terpisah dari
    karakter (tidak menyentuh tepi bawah zona cari), yang diterima —
    supaya bagian karakter yang terang (bulu putih, perban) tidak
    ikut terdeteksi sebagai bulan. Mengembalikan (cx, cy, r) atau None.
    """
    from scipy import ndimage

    a = np.asarray(img).astype(int)
    h, w, _ = a.shape
    zh, zx = int(h * 0.30), int(w * 0.35)
    zone = a[:zh, zx:]
    r, g, b = zone[:, :, 0], zone[:, :, 1], zone[:, :, 2]
    mask = (r > 175) & (g > 165) & (b > 140) & ((r - b) < 70) & ((r - b) > -10)
    lab, n = ndimage.label(mask)
    best = None
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        area = len(xs)
        if area < 250:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if y1 >= zh - 2:
            continue  # menyentuh tepi bawah zona = menyatu dengan karakter
        if not (0.65 <= bw / bh <= 1.5):
            continue  # bukan cakram
        if area / (bw * bh) < 0.5:
            continue
        if best is None or area > best[0]:
            best = (area, xs.mean() + zx, ys.mean(), (area / np.pi) ** 0.5)
    if best is None:
        return None
    return best[1], best[2], best[3]


def recolor_moon(img, moon_name):
    found = find_moon(img)
    if not found:
        return img
    cx, cy, rad = found
    target = np.array(MOON_TARGETS[moon_name], dtype=float)
    a = np.asarray(img).astype(float)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    inside = dist <= rad * 1.03
    lum = a[inside].mean(axis=1, keepdims=True) / 255.0  # pola kawah dipertahankan
    colored = target * (0.30 + 0.85 * lum)
    a[inside] = np.clip(colored, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


# ------------------------------------------------------------------ langit
def draw_sky(img, sky, token_id, moon):
    if sky == "None":
        return img
    rng = random.Random(token_id * 31 + 7)
    d = ImageDraw.Draw(img, "RGBA")
    moon_zone = None
    if moon:
        cx, cy, rad = moon
        moon_zone = (cx - rad - 14, cy - rad - 14, cx + rad + 14, cy + rad + 14)

    def clear_of_moon(x, y):
        return not moon_zone or not (moon_zone[0] <= x <= moon_zone[2] and moon_zone[1] <= y <= moon_zone[3])

    def in_safe_area(x, y):
        # bintang/kelelawar hanya di margin langit, tidak menimpa wajah karakter
        return y < 120 or x < 105 or x > SIZE - 105

    if "Stars" in sky:
        for _ in range(46):
            x, y = rng.randrange(4, SIZE - 4), rng.randrange(4, 300)
            if not in_safe_area(x, y) or not clear_of_moon(x, y):
                continue
            col = rng.choice([(255, 222, 120), (255, 255, 255), (150, 240, 220), (255, 190, 120)])
            s = rng.choice([3, 4, 5])
            d.line([(x - s, y), (x + s, y)], fill=col + (255,), width=2)
            d.line([(x, y - s), (x, y + s)], fill=col + (255,), width=2)
            if rng.random() < 0.4:
                d.point((x, y), fill=(255, 255, 255, 255))
    if "Bats" in sky:
        for _ in range(4):
            x, y = rng.randrange(10, SIZE - 70), rng.randrange(8, 150)
            if not clear_of_moon(x + 30, y + 10):
                continue
            bat = (12, 6, 22, 255)
            w = rng.choice([44, 54, 64])
            h = w // 3
            d.polygon([(x, y + h // 2), (x + w // 4, y), (x + w // 2, y + h // 2),
                       (x + 3 * w // 4, y), (x + w, y + h // 2), (x + 3 * w // 4, y + h),
                       (x + w // 2, y + h // 2 + 3), (x + w // 4, y + h)], fill=bat)
            d.point((x + w // 2 - 4, y + h // 2), fill=(255, 190, 60, 255))
            d.point((x + w // 2 + 4, y + h // 2), fill=(255, 190, 60, 255))
    return img


# ------------------------------------------------------------------ grade
def apply_grade(img, grade):
    if grade == "Original":
        return img
    a = np.asarray(img).astype(float)
    if grade == "Warm":
        a[:, :, 0] *= 1.09
        a[:, :, 1] *= 1.02
        a[:, :, 2] *= 0.90
    elif grade == "Cool":
        a[:, :, 0] *= 0.93
        a[:, :, 2] *= 1.10
    elif grade == "Deep":
        a = (a - 128) * 1.10 + 128 - 16
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def apply_finish(img, finish):
    if finish == "Vivid":
        img = ImageEnhance.Color(img).enhance(1.25)
        img = ImageEnhance.Contrast(img).enhance(1.05)
    else:  # Matte
        img = ImageEnhance.Color(img).enhance(0.78)
        img = ImageEnhance.Brightness(img).enhance(1.03)
    return img


def apply_frame(img, frame):
    if frame == "None":
        return img
    d = ImageDraw.Draw(img)
    if frame in ("Purple", "Orange"):
        col = (179, 136, 255) if frame == "Purple" else (255, 167, 38)
        d.rectangle([0, 0, SIZE - 1, SIZE - 1], outline=(35, 16, 63), width=14)
        d.rectangle([7, 7, SIZE - 8, SIZE - 8], outline=col, width=7)
    elif frame == "Checker":
        sq, wdt = 32, 24
        for x in range(0, SIZE, sq):
            for k in range(2):
                y = k * (wdt // 2)
                c = (255, 167, 38) if ((x // sq) + k) % 2 == 0 else (88, 44, 150)
                d.rectangle([x, y, x + sq - 1, y + wdt // 2 - 1], fill=c)
                y2 = SIZE - wdt + k * (wdt // 2)
                c2 = (255, 167, 38) if ((x // sq) + k) % 2 == 0 else (88, 44, 150)
                d.rectangle([x, y2, x + sq - 1, y2 + wdt // 2 - 1], fill=c2)
        for y in range(0, SIZE, sq):
            for k in range(2):
                x = k * (wdt // 2)
                c = (255, 167, 38) if ((y // sq) + k) % 2 == 0 else (88, 44, 150)
                d.rectangle([x, y, x + wdt // 2 - 1, y + sq - 1], fill=c)
                x2 = SIZE - wdt + k * (wdt // 2)
                d.rectangle([x2, y, x2 + wdt // 2 - 1, y + sq - 1], fill=c)
    return img


# ------------------------------------------------------------------ utama
def load_traits(token_id):
    with open(os.path.join(META_DIR, f"{token_id}.json")) as f:
        meta = json.load(f)
    return {a["trait_type"]: a["value"] for a in meta["attributes"]}


def build(token_id, traits):
    if token_id in ORIGINALS and os.path.exists(ORIGINALS[token_id]):
        img = Image.open(ORIGINALS[token_id]).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
        return img
    img = load_master(traits["Master"])
    moon = find_moon(img)
    img = recolor_moon(img, traits["Moon"])
    img = draw_sky(img, traits["Sky"], token_id, moon)
    img = apply_grade(img, traits["Night Grade"])
    img = apply_frame(img, traits["Frame"])
    img = apply_finish(img, traits["Finish"])
    if traits["Mirror"] == "Yes":
        img = ImageOps.mirror(img)
    return img


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    args = ap.parse_args()
    if args.all:
        ids = range(1, 10001)
    elif args.start is not None:
        ids = range(args.start, (args.end or args.start) + 1)
    else:
        ids = [int(x) for x in args.tokens.split(",")]
    os.makedirs(OUT_DIR, exist_ok=True)
    n = 0
    for tid in ids:
        img = build(tid, load_traits(tid))
        if tid in ORIGINALS:
            # karya asli kreator disimpan sebagai PNG (metadata menunjuk .png)
            img.save(os.path.join(OUT_DIR, f"{tid}.png"), "PNG")
        else:
            img.save(os.path.join(OUT_DIR, f"{tid}.webp"), "WEBP", quality=86, method=4)
        n += 1
        if n % 500 == 0:
            print(f"{n} varian selesai", flush=True)
    print(f"Selesai: {n} varian")


if __name__ == "__main__":
    main()
