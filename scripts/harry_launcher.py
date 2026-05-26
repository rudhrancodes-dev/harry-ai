#!/usr/bin/env python3
"""Harry desktop-app launcher.

Lives inside Harry.app/Contents/Resources/launcher/. Run by the Mach-O
shim at Harry.app/Contents/MacOS/Harry. Responsibilities:

  1. Find a usable system python3 (3.10+).
  2. Create a venv at  ~/Library/Application Support/Harry/runtime/  if missing.
  3. pip-install the bundled wheel (Harry.app/Contents/Resources/wheel/*.whl)
     plus all its dependencies, showing a native macOS progress dialog.
  4. Spawn the FastAPI server as a direct child of *this* process (no
     Terminal middleman), so TCC attributes mic / Apple-Events prompts
     to Harry.app instead of Terminal.
  5. Wait for /api/health, then open the UI in the default browser.
  6. Sit on the server PID; on Cmd-Q from the Dock, terminate cleanly.

All UI is via osascript so we have zero non-stdlib deps in this launcher.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────

APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Harry"
RUNTIME = APP_SUPPORT / "runtime"          # the venv
STATE_FILE = APP_SUPPORT / "state.json"
LOG_FILE = APP_SUPPORT / "harry.log"

BUNDLE_RESOURCES = Path(__file__).resolve().parent.parent  # ../Resources/
WHEEL_DIR = BUNDLE_RESOURCES / "wheel"

PORT = int(os.environ.get("HARRY_PORT", "7424"))
URL = f"http://127.0.0.1:{PORT}"


# ── osascript helpers ─────────────────────────────────────────────────────

def osa(script: str) -> str:
    try:
        return subprocess.check_output(
            ["/usr/bin/osascript", "-e", script],
            stderr=subprocess.DEVNULL, timeout=600,
        ).decode().strip()
    except subprocess.CalledProcessError:
        return ""


def alert(title: str, message: str, buttons: list[str] = None) -> str:
    btns = buttons or ["OK"]
    btn_list = ", ".join(f'"{b}"' for b in btns)
    return osa(
        f'display alert "{title}" message "{message}" '
        f'buttons {{{btn_list}}} default button "{btns[-1]}"')


def progress(title: str, body: str) -> None:
    """Posts a notification — non-blocking, vanishes after a few seconds."""
    safe_title = title.replace('"', '\\"')
    safe_body = body.replace('"', '\\"')
    osa(f'display notification "{safe_body}" with title "{safe_title}"')


# ── python discovery ─────────────────────────────────────────────────────

PYTHON_CANDIDATES = [
    # Prefer python.org framework installs first — these have the widest
    # wheel availability for pyobjc, PyAudio, and friends.
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
    "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
    # Homebrew next (often 3.13 or 3.14 — 3.14 wheels are still patchy
    # for native extensions, so we require version ≤ 3.13)
    "/opt/homebrew/opt/python@3.12/bin/python3.12",
    "/opt/homebrew/opt/python@3.11/bin/python3.11",
    "/opt/homebrew/bin/python3.12",
    "/opt/homebrew/bin/python3.11",
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3.12",
    "/usr/local/bin/python3.11",
    "/usr/local/bin/python3",
    str(Path.home() / ".local/bin/python3"),
    # System python is last resort — on macOS 12+ it works but version
    # may be 3.9 which is below our floor.
    "/usr/bin/python3",
]


def find_python() -> str | None:
    """Return the first python on disk whose version is 3.10 ≤ ver ≤ 3.13.
    We skip 3.14+ because pyobjc / PyAudio binary wheels lag behind it."""
    for c in PYTHON_CANDIDATES:
        if not Path(c).exists():
            continue
        try:
            out = subprocess.check_output([c, "-c",
                "import sys; print(sys.version_info[0]); print(sys.version_info[1])"],
                timeout=5, stderr=subprocess.DEVNULL).decode().strip().splitlines()
            major, minor = int(out[0]), int(out[1])
        except Exception:
            continue
        if (major, minor) >= (3, 10) and (major, minor) <= (3, 13):
            return c
    return None


# ── install / verify runtime ──────────────────────────────────────────────

def runtime_python() -> Path:
    return RUNTIME / "bin" / "python3"


def clean_env_for_venv(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return an env dict safe to use when invoking the venv python.

    When Harry.app is launched via LaunchServices, the parent process is
    macOS's `launchd`. The framework Python that the bash shim execs
    sets __PYVENV_LAUNCHER__ — and that env var, if inherited by a child
    venv python, makes the child use the parent's sys.prefix instead of
    its own. The venv suddenly can't find packages installed inside it.
    That's exactly the false-positive 'harry.server still can't import'
    alert we were hitting.

    We also drop PYTHONHOME and PYTHONPATH for the same reason."""
    env = os.environ.copy()
    for key in ("__PYVENV_LAUNCHER__", "PYTHONHOME", "PYTHONPATH",
                "PYTHONEXECUTABLE", "PYTHONSTARTUP"):
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def is_runtime_ready() -> tuple[bool, str]:
    """Returns (ok, detail). detail explains *why* on failure."""
    py = runtime_python()
    if not py.exists():
        return False, f"venv python missing: {py}"
    try:
        out = subprocess.check_output(
            [str(py), "-c", "import harry.server; print('OK')"],
            env=clean_env_for_venv(),
            timeout=20, stderr=subprocess.STDOUT,
        ).decode(errors="replace").strip()
        return ("OK" in out), out
    except subprocess.CalledProcessError as e:
        return False, (e.output or b"").decode(errors="replace")
    except subprocess.TimeoutExpired:
        return False, "import harry.server timed out after 20 s"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def install_runtime() -> bool:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    log = LOG_FILE.open("a", buffering=1)
    log.write(f"\n=== install {time.strftime('%Y-%m-%dT%H:%M:%S')} ===\n")

    system_py = find_python()
    if not system_py:
        alert("Python 3.10+ required",
              "Harry needs Python 3.10 or newer.\\n\\n"
              "Install from python.org or run:  brew install python")
        return False
    log.write(f"system python: {system_py}\n")

    progress("Harry", "Setting up your runtime…")

    # Wipe a half-built venv from a previous failed run
    if RUNTIME.exists() and not runtime_python().exists():
        shutil.rmtree(RUNTIME, ignore_errors=True)

    if not RUNTIME.exists():
        log.write("creating venv…\n")
        r = subprocess.run([system_py, "-m", "venv", str(RUNTIME)],
                           env=clean_env_for_venv(),
                           stdout=log, stderr=log)
        if r.returncode != 0:
            alert("Setup failed", "Could not create the Python venv. "
                                  "See ~/Library/Application Support/Harry/harry.log")
            return False

    progress("Harry", "Installing dependencies… first launch takes a minute.")

    py = str(runtime_python())
    venv_env = clean_env_for_venv()
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"],
                   env=venv_env, stdout=log, stderr=log)

    wheels = sorted(WHEEL_DIR.glob("*.whl")) if WHEEL_DIR.exists() else []
    if wheels:
        log.write(f"installing bundled wheel: {wheels[0].name}\n")
        # `pip install <wheel>` only installs that one wheel — we also
        # need to pull its declared dependencies. The wheel was built
        # with --no-deps so we install requirements.txt-equivalents here.
        deps = [
            "SpeechRecognition>=3.10.0",
            "pyttsx3>=2.90",
            "PyAudio>=0.2.13",
            "python-dotenv>=1.0.0",
            "rich>=13.7.0",
            "requests>=2.31.0",
            "fastapi>=0.110.0",
            "uvicorn[standard]>=0.27.0",
            "websockets>=12.0",
        ]
        r = subprocess.run([py, "-m", "pip", "install", str(wheels[0]),
                            *deps], env=venv_env, stdout=log, stderr=log)
    else:
        log.write("no bundled wheel; falling back to PyPI\n")
        r = subprocess.run([py, "-m", "pip", "install", "harry-jarvis"],
                           env=venv_env, stdout=log, stderr=log)

    if r.returncode != 0:
        # Show the last 20 lines of the log so the user sees the real error
        log.flush()
        try:
            tail = "\n".join(LOG_FILE.read_text().splitlines()[-20:])
        except OSError:
            tail = "(log unreadable)"
        alert("Install failed",
              f"pip install exited with status {r.returncode}.\\n\\n"
              f"Last log lines:\\n{tail[:500]}\\n\\n"
              f"Full log: ~/Library/Application Support/Harry/harry.log")
        return False

    STATE_FILE.write_text(json.dumps({
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "system_python": system_py,
    }, indent=2))
    progress("Harry", "Ready.")
    log.close()
    return True


# ── server lifecycle ──────────────────────────────────────────────────────

def start_server() -> subprocess.Popen:
    """Spawn uvicorn as a direct child so TCC attributes prompts to us."""
    extras = {"HARRY_HOST": "127.0.0.1", "HARRY_PORT": str(PORT)}
    # Load env from ~/.config/harry/.env if present so users can pre-set
    # OPENROUTER_API_KEY etc. without editing Application Support.
    user_env = Path.home() / ".config" / "harry" / ".env"
    if user_env.exists():
        for line in user_env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                extras.setdefault(k.strip(), v.strip())
    env = clean_env_for_venv(extras)
    log = LOG_FILE.open("a", buffering=1)
    log.write(f"\n=== server up {time.strftime('%H:%M:%S')} on {URL} ===\n")
    return subprocess.Popen(
        [str(runtime_python()), "-m", "harry.server"],
        env=env, stdout=log, stderr=log,
    )


def wait_and_open(timeout: float = 25.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(URL + "/api/health", timeout=0.5):
                webbrowser.open(URL)
                return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.3)
    return False


# ── permission preflight ─────────────────────────────────────────────────

PREFLIGHT_FLAG = APP_SUPPORT / ".preflight_shown"


def permission_preflight() -> None:
    """First-run only. Explains the four permissions Harry will ask for.

    macOS can prompt automatically for Microphone, Speech Recognition, and
    Apple Events (the Info.plist usage strings handle those), but
    Accessibility (the API used by cliclick to move the cursor / send
    keys) cannot be triggered programmatically — the user has to enable
    it in System Settings. We open that pane for them after the first
    accessibility-needed click fails, and explain it up front here."""
    if PREFLIGHT_FLAG.exists():
        return
    body = (
        "Harry will ask for a few permissions:\\n\\n"
        "• Microphone — to hear what you say\\n"
        "• Speech Recognition — to transcribe locally\\n"
        "• Apple Events — to open and control approved apps\\n\\n"
        "For computer-use (cursor / keystrokes) you'll also need to enable "
        "Accessibility for Harry in System Settings → Privacy & Security. "
        "Harry will open that pane for you the first time it's needed."
    )
    osa(
        f'display alert "Welcome to Harry" message "{body}" '
        f'buttons {{"Open Privacy Settings", "Continue"}} '
        f'default button "Continue"'
    )
    if "Open Privacy Settings" in osa(
            'set the clipboard to (button returned of (display dialog '
            '"" buttons {"x"} default button "x" giving up after 0))'):
        # No-op — the alert above already returned, this is just defensive
        pass
    PREFLIGHT_FLAG.touch()


def open_accessibility_pane() -> None:
    """Used by support tooling or manual debug — opens the right pane."""
    osa(
        'tell application "System Preferences" to activate\n'
        'tell application "System Preferences" to reveal '
        'anchor "Privacy_Accessibility" of pane id '
        '"com.apple.preference.security"'
    )


# ── main ──────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", buffering=1) as f:
        f.write(f"[launcher {time.strftime('%H:%M:%S')}] {msg}\n")


def main() -> int:
    APP_SUPPORT.mkdir(parents=True, exist_ok=True)
    _log("launcher start")

    ok, detail = is_runtime_ready()
    if not ok:
        _log(f"first runtime check: NOT ready ({detail.strip()[:200]})")
        if not install_runtime():
            return 1
        # Retry the verification a few times — pyobjc-heavy installs can
        # take a beat for the file-system metadata to settle on a cold
        # filesystem cache.
        for attempt in range(3):
            ok, detail = is_runtime_ready()
            if ok:
                _log(f"runtime ready after attempt {attempt + 1}")
                break
            _log(f"post-install check {attempt + 1} failed: {detail.strip()[:300]}")
            time.sleep(1.0)
        if not ok:
            # Last-ditch: the import didn't pass our explicit check, but
            # pip exited 0 and state.json was written. Try to start the
            # server anyway and surface its real stderr if it crashes.
            _log("post-install check failed three times; "
                 "starting server anyway to see its real error.")

    permission_preflight()

    proc = start_server()
    threading.Thread(target=wait_and_open, daemon=True).start()

    # Give the server 5 s to either become healthy or die loudly.
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        try:
            with urllib.request.urlopen(URL + "/api/health", timeout=0.4):
                _log("server healthy")
                break
        except Exception:
            time.sleep(0.3)

    if proc.poll() is not None and proc.returncode != 0:
        try:
            tail = "\n".join(LOG_FILE.read_text().splitlines()[-25:])
        except OSError:
            tail = "(log unreadable)"
        alert("Harry could not start",
              f"The server exited with code {proc.returncode}.\\n\\n"
              f"Last log lines:\\n{tail[:600]}\\n\\n"
              f"Full log: ~/Library/Application Support/Harry/harry.log")
        return proc.returncode

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return proc.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
