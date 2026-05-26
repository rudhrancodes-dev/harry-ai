#!/usr/bin/env bash
# Build the macOS Harry.app bundle, then package it as Harry.dmg.
#
# - Generates Harry.icns from assets/harry-icon-1024.png via iconutil
# - Writes Info.plist + a launcher shell script
# - The launcher opens Terminal, sources the project venv, runs `harry`
# - Output:   dist/Harry.app  and  dist/Harry.dmg
#
# Requires: macOS, iconutil (preinstalled), hdiutil (preinstalled),
#           and that you've already run `pip install -e .` so the
#           project venv has the `harry` console script.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
APP="$DIST/Harry.app"
ICNS="$ROOT/assets/Harry.icns"
PNG="$ROOT/assets/harry-icon-1024.png"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m✓\033[0m %s\n" "$*"; }

bold "Building Harry.app"

if [ ! -f "$PNG" ]; then
  python3 "$ROOT/scripts/make-icon.py"
fi

# Build .icns
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

# Build .app
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
# Harry launcher — finds the install directory, opens Terminal, runs the server.
set -euo pipefail

# Resolve the install dir: prefer ~/Apps/harry-ai (set by install.sh),
# fall back to the dev tree the .app was built from.
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

# Open Terminal and run the server inside the project venv.
osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "cd \"$INSTALL_DIR\" && source .venv/bin/activate && harry"
end tell
APPLESCRIPT
LAUNCH

# Bake the dev-tree path so the .app works without re-install during dev
sed -i '' "s|__DEV_ROOT__|$ROOT|g" "$APP/Contents/MacOS/Harry"
chmod +x "$APP/Contents/MacOS/Harry"
ok "bundle → $APP"

# Package as DMG
DMG="$DIST/Harry.dmg"
STAGE="$DIST/dmg-stage"
rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

hdiutil create \
  -volname "Harry" \
  -srcfolder "$STAGE" \
  -ov -format UDZO \
  "$DMG" >/dev/null

rm -rf "$STAGE"
ok "dmg   → $DMG"

bold "Done."
echo  "  open $APP        # launch directly"
echo  "  open $DMG        # mount the installer"
