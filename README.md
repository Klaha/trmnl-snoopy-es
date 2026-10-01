# trmnl-snoopy-es

Shows the daily [Snoopy en Español](https://www.gocomics.com/peanuts-espanol) strip on a TRMNL.

## Recipe (recommended)

A TRMNL private plugin with no server of its own:

- **Strategy:** Polling, URL `https://comiccaster.xyz/rss/peanuts-espanol`.
- **Markup:** paste `recipe/shared.liquid` into **Shared** and each of `recipe/full.liquid`, `half_horizontal.liquid`, `half_vertical.liquid` and `quadrant.liquid` into its layout. Shared works out the strip and the date and defines a `snoopy` template; each layout renders it (the narrow ones ask for the short date). It adapts to landscape and portrait.
- **Form fields:** paste `recipe/form_fields.yml`.

GoComics' CDN converts the strip to grays (`?optimizer=image&saturation=-100…`). In narrow views a small script finds the four panels of a daily strip and lays them out as a 2x2 grid or a column when that makes them bigger; Sunday strips and anything unexpected are shown whole.

Preview every layout on the OG and the X, in both orientations, with the live feed:

```sh
pip install -r tools/requirements.txt && playwright install chromium
python tools/preview.py            # newest strip
python tools/preview.py --item 4   # an older one (e.g. a Sunday)
```

## Webhook + launchd (first version)

Before the recipe, a launchd job on the Mac read the day's strip URL from GoComics and sent it to a webhook plugin. It needs the Mac to be on because GoComics blocks datacenter IPs (GitHub Actions gets a 403).

1. On TRMNL, create a private plugin with the **Webhook** strategy and paste `trmnl/full.liquid` into the Full markup.
2. Install the daily job with the plugin's webhook URL:
   ```sh
   ./install.sh https://trmnl.com/api/custom_plugins/<uuid>
   ```
   It runs at 08:00 and at login. Re-run `./install.sh` (without the URL) after changing `snoopy.py`.

Log: `~/Library/Logs/trmnl-snoopy-es.log`. Try it without sending: `python snoopy.py --dry-run`.

Uninstall:
```sh
launchctl bootout gui/$(id -u)/com.klaha.trmnl-snoopy-es
rm ~/Library/LaunchAgents/com.klaha.trmnl-snoopy-es.plist
rm -r ~/Library/Application\ Support/trmnl-snoopy-es
```

Peanuts is © Peanuts Worldwide LLC. This project stores no strips: it only links to the images GoComics serves.
