#!/bin/zsh
# Install (or update) the daily launchd job that sends the strip to TRMNL.
# launchd jobs can't read ~/Desktop, so the script runs from Application Support.
# Usage: ./install.sh [webhook-url]
set -euo pipefail

LABEL=com.klaha.trmnl-snoopy-es
APP_DIR="$HOME/Library/Application Support/trmnl-snoopy-es"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/trmnl-snoopy-es.log"
REPO_DIR="${0:A:h}"

mkdir -p "$APP_DIR" "${PLIST:h}"
cp "$REPO_DIR/snoopy.py" "$REPO_DIR/requirements.txt" "$APP_DIR/"
[[ -d "$APP_DIR/.venv" ]] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --disable-pip-version-check -r "$APP_DIR/requirements.txt"

if [[ $# -ge 1 ]]; then
  print -r -- "$1" > "$APP_DIR/webhook-url.txt"
  chmod 600 "$APP_DIR/webhook-url.txt"
fi
[[ -f "$APP_DIR/webhook-url.txt" ]] || { echo "Missing webhook URL: run ./install.sh <webhook-url>"; exit 1; }

# 08:00 every day, plus at login so a day the Mac was off at 08:00 still gets its strip.
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_DIR/.venv/bin/python</string>
        <string>$APP_DIR/snoopy.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG</string>
    <key>StandardErrorPath</key>
    <string>$LOG</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed. Log: $LOG"
