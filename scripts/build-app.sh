#!/usr/bin/env bash
# Build the macOS Harry.app bundle, then package it as a polished
# Claude-style Harry.dmg with a branded background, an arrow from the
# .app icon to the Applications symlink, hidden toolbar/sidebar, and a
# custom volume icon.
#
# Flow:
#   1. Build/refresh Harry.icns from assets/harry-icon-1024.png via iconutil
#   2. Build dist/Harry.app skeleton + launcher + Info.plist
#   3. Stage Harry.app + Applications symlink + .background/ + .VolumeIcon.icns
#   4. hdiutil create UDRW  →  attach  →  AppleScript styles the window
#      →  detach  →  hdiutil convert UDZO  →  dist/Harry.dmg
#
# Requires:  macOS, iconutil, hdiutil, sips, osascript, SetFile
#            (all preinstalled on every Mac except SetFile, which ships
#             with the Command Line Tools — `xcode-select --install`).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
APP="$DIST/Harry.app"
ICNS="$ROOT/assets/Harry.icns"
PNG="$ROOT/assets/harry-icon-1024.png"
BG="$ROOT/assets/dmg-background.png"
BG2X="$ROOT/assets/dmg-background@2x.png"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m✓\033[0m %s\n" "$*"; }

bold "Building Harry.app"

[ -f "$PNG" ] || python3 "$ROOT/scripts/make-icon.py"
[ -f "$BG"  ] || python3 "$ROOT/scripts/make-dmg-bg.py"

# ── icns ──────────────────────────────────────────────────────────────────
ICONSET="$ROOT/assets/Harry.iconset"
rm -rf "$ICONSET"; mkdir -p "$ICONSET"
for size in 16 32 64 128 256 512; do
  /usr/bin/sips -z $size $size "$PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  /usr/bin/sips -z $((size*2)) $((size*2)) "$PNG" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
/usr/bin/sips -z 1024 1024 "$PNG" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"
ok "icon → $ICNS"

# ── .app bundle ───────────────────────────────────────────────────────────
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$ICNS" "$APP/Contents/Resources/Harry.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Harry</string>
  <key>CFBundleDisplayName</key><string>Harry · Intelligence</string>
  <key>CFBundleIdentifier</key><string>dev.rudhrancodes.harry</string>
  <key>CFBundleVersion</key><string>0.2.0</string>
  <key>CFBundleShortVersionString</key><string>0.2.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>Harry</string>
  <key>CFBundleIconFile</key><string>Harry</string>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSMicrophoneUsageDescription</key>
    <string>Harry needs your microphone to listen for the wake word and your spoken requests.</string>
  <key>NSAppleEventsUsageDescription</key>
    <string>Harry uses Apple Events to open and control approved applications on your behalf.</string>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/Harry" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
CANDIDATES=(
  "$HOME/Apps/harry-ai"
  "__DEV_ROOT__"
)
INSTALL_DIR=""
for c in "${CANDIDATES[@]}"; do
  if [ -d "$c/.venv" ] && [ -f "$c/pyproject.toml" ]; then
    INSTALL_DIR="$c"; break
  fi
done
if [ -z "$INSTALL_DIR" ]; then
  osascript -e 'display alert "Harry isn'\''t installed yet" message "Run the one-line installer first:\n\ncurl -sSL https://raw.githubusercontent.com/rudhrancodes-dev/harry-ai/main/install.sh | bash"'
  exit 1
fi
osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "cd \"$INSTALL_DIR\" && source .venv/bin/activate && harry"
end tell
APPLESCRIPT
LAUNCH

sed -i '' "s|__DEV_ROOT__|$ROOT|g" "$APP/Contents/MacOS/Harry"
chmod +x "$APP/Contents/MacOS/Harry"
ok "bundle → $APP"

# ── DMG: built with `create-dmg` for Claude-style polish ──────────────────
DMG="$DIST/Harry.dmg"
rm -f "$DMG"

if ! command -v create-dmg >/dev/null 2>&1; then
  echo "create-dmg not found. Install with:  brew install create-dmg" >&2
  echo "Falling back to plain hdiutil bundle..." >&2
  STAGE="$DIST/dmg-stage"; rm -rf "$STAGE"; mkdir -p "$STAGE"
  cp -R "$APP" "$STAGE/"; ln -s /Applications "$STAGE/Applications"
  hdiutil create -volname Harry -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
  rm -rf "$STAGE"
  ok "dmg   → $DMG (plain)"
else
  # create-dmg drives Finder for us — handles the .DS_Store, background
  # image, window bounds, icon positions, hidden toolbar — all the quirks
  # that make a hand-rolled AppleScript DMG flaky.
  create-dmg \
    --volname "Harry" \
    --volicon "$ICNS" \
    --background "$BG" \
    --window-pos 400 120 \
    --window-size 660 400 \
    --icon-size 128 \
    --text-size 12 \
    --icon "Harry.app" 165 240 \
    --app-drop-link 495 240 \
    --hide-extension "Harry.app" \
    --no-internet-enable \
    --format UDZO \
    "$DMG" \
    "$APP" >/dev/null
  ok "dmg   → $DMG  ($(du -h "$DMG" | awk '{print $1}'))"
fi

ok "dmg   → $DMG  ($(du -h "$DMG" | awk '{print $1}'))"
bold "Done."
echo  "  open $APP        # launch directly"
echo  "  open $DMG        # mount the polished installer"
