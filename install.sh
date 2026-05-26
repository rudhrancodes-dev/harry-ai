#!/usr/bin/env bash
# Harry · one-line installer
#   curl -sSL https://raw.githubusercontent.com/rudhrancodes-dev/harry-ai/main/install.sh | bash
#
# What it does:
#   1. Clones harry-ai into ~/Apps/harry-ai (or updates it if already there)
#   2. Creates a Python 3.10+ venv inside the repo
#   3. Installs runtime deps (pip install -e .)
#   4. Runs `harry-onboard --yes` for a sane default config
#   5. Optionally builds the macOS .app bundle (./scripts/build-app.sh)
#   6. Tells you to run `harry`
#
# Re-running this script is safe — it's an upsert.

set -euo pipefail

REPO_URL="${HARRY_REPO_URL:-https://github.com/rudhrancodes-dev/harry-ai.git}"
INSTALL_DIR="${HARRY_INSTALL_DIR:-$HOME/Apps/harry-ai}"
BUILD_APP="${HARRY_BUILD_APP:-1}"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m✓\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m⚠\033[0m %s\n" "$*"; }

bold "Harry · installer"
echo  "  repo:    $REPO_URL"
echo  "  install: $INSTALL_DIR"
echo

command -v git    >/dev/null || { echo "git not found"; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

PY_MAJ_MIN=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
case "$PY_MAJ_MIN" in
  3.1[0-9]) ok "python $PY_MAJ_MIN" ;;
  *) echo "python 3.10+ required (have $PY_MAJ_MIN)"; exit 1 ;;
esac

mkdir -p "$(dirname "$INSTALL_DIR")"
if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
  ok "updated $INSTALL_DIR"
else
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
  ok "cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ok "venv created"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -e . --quiet
ok "deps installed"

harry-onboard --yes
ok "onboarded"

if [ "$BUILD_APP" = "1" ] && [ "$(uname)" = "Darwin" ]; then
  if [ -x scripts/build-app.sh ]; then
    scripts/build-app.sh || warn ".app build failed (you can still run \`harry\` from CLI)"
  fi
fi

echo
bold "Done. Launch with:"
echo  "  source $INSTALL_DIR/.venv/bin/activate"
echo  "  harry"
echo
echo  "Or double-click ~/Applications/Harry.app if the .app build succeeded."
