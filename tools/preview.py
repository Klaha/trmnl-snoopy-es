"""Render recipe/shared.liquid with the live feed and TRMNL's framework CSS, in every layout, for review.

Usage: python tools/preview.py [--item N] [--out DIR]   (item 0 is the newest strip)
Writes one contact sheet per device and orientation, reduced to the device's grays.
"""

import argparse
from pathlib import Path

import requests
import xmltodict
from liquid import Environment
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

FEED_URL = "https://comiccaster.xyz/rss/peanuts-espanol"
TEMPLATE = Path(__file__).parent.parent / "recipe" / "shared.liquid"

# (name, screen classes, width, height, grays)
SCREENS = [
    ("og-landscape", "screen--og", 800, 480, 4),
    ("og-portrait", "screen--og screen--portrait", 480, 800, 4),
    ("x-landscape", "screen--v2", 1872, 1404, 16),
    ("x-portrait", "screen--v2 screen--portrait", 1404, 1872, 16),
]
# (name, mashup class, view classes)
LAYOUTS = [
    ("full", "mashup--1x1", ["full"]),
    ("half_horizontal", "mashup--1Tx1B", ["half_horizontal"] * 2),
    ("half_vertical", "mashup--1Lx1R", ["half_vertical"] * 2),
    ("quadrant", "mashup--2x2", ["quadrant"] * 4),
]

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://trmnl.com/css/latest/plugins.css">
<script src="https://trmnl.com/js/latest/plugins.js"></script>
</head><body class="environment trmnl">
<div class="screen {screen}"><div class="mashup {mashup}">{views}</div></div>
</body></html>"""


def render_markup(item: int) -> str:
    data = xmltodict.parse(requests.get(FEED_URL, timeout=15).text)
    # Mimic "show item N" by dropping the newer ones; the template always takes the first.
    data["rss"]["channel"]["item"] = data["rss"]["channel"]["item"][item:]
    return Environment().from_string(TEMPLATE.read_text()).render(**data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item", type=int, default=0)
    parser.add_argument("--out", default="preview")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    markup = render_markup(args.item)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, screen, width, height, grays in SCREENS:
            shots = []
            page = browser.new_page(viewport={"width": width, "height": height})
            for layout, mashup, views in LAYOUTS:
                html_views = "".join(f'<div class="view view--{v}">{markup}</div>' for v in views)
                page.set_content(PAGE.format(screen=screen, mashup=mashup, views=html_views))
                page.wait_for_load_state("networkidle")
                path = out / f"{name}-{layout}.png"
                page.screenshot(path=path)
                shots.append((layout, Image.open(path).convert("L")))
            page.close()

            # Contact sheet, quantized to the device's grays like the real panel.
            gap = 30
            sheet = Image.new("L", (width * 2 + gap * 3, (height + gap) * 2 + gap), 200)
            draw = ImageDraw.Draw(sheet)
            for i, (layout, shot) in enumerate(shots):
                x, y = gap + (i % 2) * (width + gap), gap + (i // 2) * (height + gap)
                levels = shot.quantize(grays, dither=Image.Dither.NONE).convert("L")
                sheet.paste(levels, (x, y))
                draw.text((x, y - 14), layout, fill=0)
            sheet.save(out / f"{name}.png")
            print(out / f"{name}.png")
        browser.close()


if __name__ == "__main__":
    main()
