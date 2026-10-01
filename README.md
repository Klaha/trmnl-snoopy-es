# trmnl-snoopy-es

Shows the daily [Snoopy en Español](https://www.gocomics.com/peanuts-espanol) strip on a TRMNL OG.

A launchd job on the Mac reads the day's strip URL from GoComics and sends it to a TRMNL private plugin webhook. TRMNL loads the image straight from GoComics; no images are stored or rehosted here.

It runs on the Mac because GoComics blocks datacenter IPs (GitHub Actions gets a 403).

## Setup

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

Personal use only: Peanuts is © Peanuts Worldwide.
