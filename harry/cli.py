"""`harry` — launch the desktop app.

Starts the FastAPI server in the foreground, opens the UI in the user's
default browser as soon as the server reports healthy. Equivalent to
running `python -m harry.server` plus a polite browser nudge.
"""
from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.request
import webbrowser


def _wait_and_open(url: str, timeout: float = 8.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=0.5):
                webbrowser.open(url)
                return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.25)


def main() -> int:
    host = os.getenv("HARRY_HOST", "127.0.0.1")
    port = int(os.getenv("HARRY_PORT", "7424"))
    url = f"http://{host}:{port}"
    print(f"Harry · launching at {url}")
    threading.Thread(target=_wait_and_open, args=(url,), daemon=True).start()
    from harry.server import main as serve
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
