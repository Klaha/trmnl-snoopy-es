"""Fetch the daily "Snoopy en Español" strip from GoComics and prepare it for a TRMNL OG (800x480, e-ink)."""

import argparse
import io
import json
import re
from datetime import date, datetime

import requests
from PIL import Image, ImageOps

COMIC_URL = "https://www.gocomics.com/peanuts-espanol/{:%Y/%m/%d}"
HEADERS = {
    # Browser-like headers get past GoComics' Bunny Shield without solving its JS challenge.
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

# Area left for the strip once TRMNL's title bar is drawn.
MAX_WIDTH, MAX_HEIGHT = 800, 430
# Grays at or above this become white, so pastel backgrounds don't turn into dither noise.
WHITE_POINT = 200
# The OG shows 4 grays (2-bit) on current firmware; 1-bit is pure black and white.
PALETTES = {2: [0, 85, 170, 255], 1: [0, 255]}
MONTHS = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
WEEKDAYS = "lunes martes miércoles jueves viernes sábado domingo".split()


def strip_image_url(day: date) -> str:
    url = COMIC_URL.format(day)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    if b"bunny-shield" in r.content[:2048]:
        raise RuntimeError(f"GoComics answered with its anti-bot challenge for {url}")

    # GoComics serves the latest strip at future dates instead of a 404, so check which date we got.
    canonical = re.search(r'rel="canonical" href="[^"]*/(\d{4}/\d{2}/\d{2})"', r.text)
    if canonical and canonical.group(1) != f"{day:%Y/%m/%d}":
        raise RuntimeError(f"No strip for {day} yet (GoComics served {canonical.group(1)})")

    og_image = re.search(r'property="og:image" content="([^"]+)"', r.text)
    if not og_image:
        raise RuntimeError(f"No strip image found at {url}")
    return og_image.group(1)


def download(url: str) -> Image.Image:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def to_eink(img: Image.Image, bits: int = 2, dither: bool = False) -> Image.Image:
    gray = img.convert("L")
    # Stretch the tones so light backgrounds go white and ink stays black.
    gray = gray.point(lambda v: min(255, round(v * 255 / WHITE_POINT)))

    scale = min(MAX_WIDTH / gray.width, MAX_HEIGHT / gray.height)
    size = (round(gray.width * scale), round(gray.height * scale))
    gray = gray.resize(size, Image.LANCZOS)

    levels = PALETTES[bits]
    palette = Image.new("P", (1, 1))
    palette.putpalette([v for level in levels for v in (level, level, level)])
    quantized = gray.convert("RGB").quantize(
        palette=palette, dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    )
    return quantized.convert("L")


def preview(strip: Image.Image) -> Image.Image:
    """Mimic the OG screen: 800x480 white canvas with a title bar at the bottom."""
    screen = Image.new("L", (800, 480), 255)
    screen.paste(strip, ((800 - strip.width) // 2, (MAX_HEIGHT - strip.height) // 2 + 5))
    screen.paste(0, (0, 440, 800, 480))
    return ImageOps.expand(screen, border=2, fill=128)


def strip_info(day: date) -> dict:
    """Variables the TRMNL template receives through the webhook."""
    return {
        "date": day.isoformat(),
        "date_label": f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), default=date.today())
    parser.add_argument("--bits", type=int, choices=[1, 2], default=2)
    parser.add_argument("--dither", action="store_true")
    parser.add_argument("--out", default="strip.png")
    parser.add_argument("--json", help="also save the template variables (date) here")
    parser.add_argument("--preview", help="also save a simulated 800x480 screen here")
    args = parser.parse_args()

    image_url = strip_image_url(args.date)
    print(image_url)
    strip = to_eink(download(image_url), bits=args.bits, dither=args.dither)
    strip.save(args.out, optimize=True)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(strip_info(args.date), f, ensure_ascii=False)
    if args.preview:
        preview(strip).save(args.preview)


if __name__ == "__main__":
    main()
