"""
SVN External Manager - System Tray Application
Runs the Flask server as a background process with a system tray icon.
No console windows are created or shown.

Architecture (Windows):
  - Main thread: pystray event loop (required for tray icon message pump)
  - Daemon thread: Flask/werkzeug HTTP server
  - pywebview: launched as a separate pythonw process to avoid main-thread conflicts
"""

import os
import sys
import subprocess
import threading
import webbrowser
import logging

from PIL import Image, ImageDraw, ImageFont
import pystray
from werkzeug.serving import make_server

# Ensure we're running from the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Logging setup (critical for pythonw where stdout/stderr are lost) ---
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tray_app.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
log = logging.getLogger('tray_app')

# Also capture unhandled exceptions to the log
def _excepthook(exc_type, exc_value, exc_tb):
    log.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
sys.excepthook = _excepthook

from app import app

HOST = '127.0.0.1'
PORT = 5000
URL = f'http://{HOST}:{PORT}'


class TrayApp:
    """System tray application wrapping the Flask server."""

    def __init__(self):
        self.server = None
        self.server_thread = None
        self.icon = None
        self._webview_proc = None

    # --- Icon ---

    def create_icon_image(self):
        """Generate a simple tray icon with Pillow."""
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dark blue circle
        draw.ellipse([2, 2, size - 2, size - 2], fill='#1a73e8')

        # Draw "S" for SVN
        try:
            font = ImageFont.truetype("arial.ttf", 38)
        except (IOError, OSError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), "S", font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2
        y = (size - th) // 2 - bbox[1]
        draw.text((x, y), "S", fill='white', font=font)

        return img

    # --- Flask server ---

    def start_server(self):
        """Start the Flask server in a daemon thread."""
        self.server = make_server(HOST, PORT, app)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
            name='flask-server',
        )
        self.server_thread.start()
        log.info(f"Flask server started on {URL}")

    def stop_server(self):
        """Shut down the Flask server."""
        if self.server:
            self.server.shutdown()
            log.info("Flask server stopped")

    # --- Window management ---

    def _find_pythonw(self):
        """Find pythonw.exe in the current environment."""
        # If we're in a venv, use its pythonw
        venv_pythonw = os.path.join(sys.prefix, 'Scripts', 'pythonw.exe')
        if os.path.isfile(venv_pythonw):
            return venv_pythonw
        # Fall back to the one next to our current interpreter
        base_pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if os.path.isfile(base_pythonw):
            return base_pythonw
        return 'pythonw.exe'

    def open_window(self, _icon=None, _item=None):
        """Open a pywebview window in a separate process.

        pywebview requires the main thread on Windows, but pystray already
        owns it. Spawning a small helper process avoids the conflict entirely.
        """
        # If a webview process is already running, don't spawn another
        if self._webview_proc is not None and self._webview_proc.poll() is None:
            log.info("Webview process already running, skipping")
            return

        helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_webview_window.py')
        if not os.path.isfile(helper):
            log.warning("_webview_window.py not found, falling back to browser")
            self.open_browser()
            return

        try:
            pythonw = self._find_pythonw()
            flags = {}
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                flags['creationflags'] = subprocess.CREATE_NO_WINDOW
            self._webview_proc = subprocess.Popen(
                [pythonw, helper, URL],
                **flags,
            )
            log.info(f"Launched webview process (pid={self._webview_proc.pid})")
        except Exception:
            log.exception("Failed to launch webview process, falling back to browser")
            self.open_browser()

    def open_browser(self, _icon=None, _item=None):
        """Open the web UI in the default browser."""
        webbrowser.open(URL)
        log.info("Opened browser")

    # --- Lifecycle ---

    def quit_app(self, _icon=None, _item=None):
        """Clean shutdown: server, webview process, tray icon."""
        log.info("Shutting down...")

        self.stop_server()

        # Terminate the webview helper process if running
        if self._webview_proc is not None and self._webview_proc.poll() is None:
            self._webview_proc.terminate()
            log.info("Terminated webview process")

        if self.icon:
            self.icon.stop()

    def build_menu(self):
        """Build the system tray context menu."""
        webview_helper = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '_webview_window.py'
        )
        has_webview = os.path.isfile(webview_helper)

        items = []
        if has_webview:
            try:
                import webview  # noqa: F401
                items.append(pystray.MenuItem('Open Window', self.open_window, default=True))
            except ImportError:
                has_webview = False

        items.extend([
            pystray.MenuItem('Open in Browser', self.open_browser,
                             default=not has_webview),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.quit_app),
        ])
        return pystray.Menu(*items)

    def run(self):
        """Main entry point: start server, create tray icon, run event loop."""
        log.info("Starting SVN External Manager tray app")

        self.start_server()

        image = self.create_icon_image()
        menu = self.build_menu()

        self.icon = pystray.Icon(
            'svn-external-manager',
            image,
            'SVN External Manager',
            menu=menu,
        )

        # Open browser/window once the tray icon is ready
        def on_ready(icon):
            try:
                self.open_window()
            except Exception:
                log.exception("Error in on_ready, falling back to browser")
                self.open_browser()

        log.info("Starting tray icon event loop")
        self.icon.run(setup=on_ready)


def main():
    try:
        tray = TrayApp()
        tray.run()
    except Exception:
        log.critical("Fatal error in main()", exc_info=True)
        raise


if __name__ == '__main__':
    main()
