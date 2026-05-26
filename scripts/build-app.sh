#!/usr/bin/env bash
# Build a self-installing Harry.app + Claude-style Harry.dmg.
#
# What this script does, end to end:
#   1. Generate the Harry.icns from the iridescent PNG icon.
#   2. Build a Python wheel of harry-jarvis (via `pip wheel`) so the .app
#      can install offline without cloning the repo.
#   3. Lay out Harry.app/Contents/:
#         Info.plist             — usage strings + bundle id + version
#         MacOS/Harry            — Bash shim: finds python3, execs launcher
#         Resources/Harry.icns
#         Resources/launcher/    — harry_launcher.py (self-installer)
#         Resources/wheel/       — the freshly built wheel
#   4. Package as a polished Claude-style DMG via `create-dmg`.
#
# First-launch behaviour for the user:
#   • Double-click Harry.app
#   • A native macOS notification says "Setting up your runtime…"
#   • The launcher creates ~/Library/Application Support/Harry/runtime/
#     (a venv) and pip-installs the bundled wheel + its dependencies.
#   • Server boots; the default browser opens to http://127.0.0.1:7424.
#   • macOS prompts for Microphone + Apple Events permission attributed
#     to "Harry" (not Terminal), because python is a direct child of the
#     .app's MacOS/Harry shim.
#
# Subsequent launches just boot the server (~1 s) and open the browser.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
APP="$DIST/Harry.app"
ICNS="$ROOT/assets/Harry.icns"
PNG="$ROOT/assets/harry-icon-1024.png"
BG="$ROOT/assets/dmg-background.png"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m✓\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m⚠\033[0m %s\n" "$*"; }

bold "Building Harry.app  (self-installing)"

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
ok "icon"

# ── build the harry-jarvis wheel ─────────────────────────────────────────
WHEELHOUSE="$DIST/wheel"
rm -rf "$WHEELHOUSE"; mkdir -p "$WHEELHOUSE"
( cd "$ROOT" && python3 -m pip wheel . --no-deps --wheel-dir "$WHEELHOUSE" --quiet )
ok "wheel  → $(ls "$WHEELHOUSE")"

# ── lay out the .app ─────────────────────────────────────────────────────
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
mkdir -p "$APP/Contents/Resources/launcher"
mkdir -p "$APP/Contents/Resources/wheel"

cp "$ICNS" "$APP/Contents/Resources/Harry.icns"
cp "$ROOT/scripts/harry_launcher.py" "$APP/Contents/Resources/launcher/"
cp "$WHEELHOUSE"/*.whl "$APP/Contents/Resources/wheel/"

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
  <key>LSUIElement</key><false/>
  <key>NSHighResolutionCapable</key><true/>

  <!-- TCC usage strings — shown in the system prompt -->
  <key>NSMicrophoneUsageDescription</key>
    <string>Harry uses the microphone to hear your wake word and your spoken requests.</string>
  <key>NSAppleEventsUsageDescription</key>
    <string>Harry uses Apple Events to open and control approved applications on your behalf.</string>
  <key>NSSpeechRecognitionUsageDescription</key>
    <string>Harry transcribes your speech locally and via cloud STT so it can understand you.</string>
  <key>NSSystemAdministrationUsageDescription</key>
    <string>Harry only uses elevated permissions for the actions you ask for.</string>
  <key>NSCameraUsageDescription</key>
    <string>Harry does not record video; this is requested only by macOS scaffolding.</string>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/Harry" <<'LAUNCH'
#!/usr/bin/env bash
# Thin shim. Finds a usable system python3, then execs the launcher
# script that lives inside this .app bundle. Running python *directly*
# (not through Terminal) means TCC attributes prompts to Harry.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RES="$HERE/../Resources"
LAUNCHER="$RES/launcher/harry_launcher.py"

# Prefer 3.10–3.13. Homebrew 3.14 is often default but has incomplete
# wheel coverage for native extensions; the launcher's find_python()
# enforces the same upper bound, but we try to pick a good interpreter
# here so we don't even start the launcher with a doomed one.
for PY in /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
          /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
          /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
          /Library/Frameworks/Python.framework/Versions/3.10/bin/python3 \
          /opt/homebrew/opt/python@3.12/bin/python3.12 \
          /opt/homebrew/opt/python@3.11/bin/python3.11 \
          /opt/homebrew/bin/python3.12 \
          /opt/homebrew/bin/python3.11 \
          /opt/homebrew/bin/python3 \
          /usr/local/bin/python3 \
          "$HOME/.local/bin/python3" \
          /usr/bin/python3; do
  if [ -x "$PY" ]; then
    VER=$("$PY" -c "import sys;print(sys.version_info[0]*100+sys.version_info[1])" 2>/dev/null || echo 0)
    # 310 ≤ VER ≤ 313
    if [ "$VER" -ge 310 ] && [ "$VER" -le 313 ]; then
      exec "$PY" "$LAUNCHER"
    fi
  fi
done

osascript -e 'display alert "Harry needs Python 3" message "Install Python 3.10 or newer from python.org, then re-open Harry.\n\nThe quickest path is:\n  brew install python"'
exit 1
LAUNCH
chmod +x "$APP/Contents/MacOS/Harry"

# Stamp the bundle so Finder picks up the new icon immediately
touch "$APP"

ok "bundle → $APP"

# ── DMG via create-dmg ───────────────────────────────────────────────────
DMG="$DIST/Harry.dmg"
rm -f "$DMG"

if command -v create-dmg >/dev/null 2>&1; then
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
    "$DMG" "$APP" >/dev/null
  ok "dmg    → $DMG  ($(du -h "$DMG" | awk '{print $1}'))"
else
  warn "create-dmg not installed; falling back to plain hdiutil"
  STAGE="$DIST/dmg-stage"; rm -rf "$STAGE"; mkdir -p "$STAGE"
  cp -R "$APP" "$STAGE/"; ln -s /Applications "$STAGE/Applications"
  hdiutil create -volname Harry -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
  rm -rf "$STAGE"
  ok "dmg    → $DMG (plain)"
fi

bold "Done."
echo  "  open $APP        # launch (first run installs deps)"
echo  "  open $DMG        # mount the installer"
