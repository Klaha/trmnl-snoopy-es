"""Send today's "Snoopy en Español" strip from GoComics to a TRMNL private plugin webhook.

Only the image URL and the date travel to TRMNL; the device loads the image straight from GoComics.
"""

import argparse
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import requests

COMIC_URL = "https://www.gocomics.com/peanuts-espanol/{:%Y/%m/%d}"
HEADERS = {
    # Browser-like headers get past GoComics' Bunny Shield from a home connection
    # (datacenter IPs such as GitHub Actions get a 403 regardless).
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}
# Kept out of the repo: the webhook URL lets anyone push content to the device.
WEBHOOK_FILE = Path(__file__).with_name("webhook-url.txt")

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


def merge_variables(day: date) -> dict:
    """Variables the TRMNL template receives through the webhook."""
    return {
        "image_url": strip_image_url(day),
        "date": day.isoformat(),
        "date_label": f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), default=date.today())
    parser.add_argument("--dry-run", action="store_true", help="print the payload instead of sending it")
    args = parser.parse_args()

    payload = {"merge_variables": merge_variables(args.date)}
    print(f"{datetime.now():%Y-%m-%d %H:%M} {json.dumps(payload, ensure_ascii=False)}")
    if args.dry_run:
        return

    webhook_url = os.environ.get("TRMNL_WEBHOOK_URL") or WEBHOOK_FILE.read_text().strip()
    r = requests.post(webhook_url, json=payload, timeout=15)
    print(f"TRMNL answered {r.status_code}: {r.text[:200]}")
    r.raise_for_status()


if __name__ == "__main__":
    main()
