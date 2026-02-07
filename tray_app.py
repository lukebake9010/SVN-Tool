"""
SVN External Manager - System Tray Application

Runs the Flask server entirely in the background with a system tray icon.
No console window is shown. Launched via pythonw (run_tray.bat).

Tray menu:
  - Open in Browser
  - Restart Server
  - Quit
"""

import sys
import os
import threading
import webbrowser
import logging

import pystray
from PIL import Image, ImageDraw, ImageFont
from werkzeug.serving import make_server

from app import app

HOST = '0.0.0.0'
PORT = 5000
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'svn_tool.log')


def _create_icon_image():
    """Create a simple tray icon: blue circle with white 'S'."""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=(41, 128, 185),
                 outline=(30, 100, 150), width=2)

    # "S" label
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except (OSError, IOError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "S", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), "S", fill='white', font=font)

    return img


class SVNTrayApp:
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.icon = None
        self._setup_logging()

    # ── logging ──────────────────────────────────────────────

    def _setup_logging(self):
        log_fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # File handler – all output goes here (no console)
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setFormatter(log_fmt)
        root.addHandler(fh)

        # Capture werkzeug request logs too
        logging.getLogger('werkzeug').setLevel(logging.INFO)

    # ── server lifecycle ─────────────────────────────────────

    def _start_server(self):
        try:
            self.server = make_server(HOST, PORT, app)
            self.server_thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.server_thread.start()
            logging.info('Server started on http://localhost:%s', PORT)
        except OSError as exc:
            logging.error('Failed to start server: %s', exc)

    def _stop_server(self):
        if self.server:
            logging.info('Stopping server...')
            self.server.shutdown()
            self.server = None
            self.server_thread = None
            logging.info('Server stopped')

    def _restart_server(self):
        logging.info('Restarting server...')
        self._stop_server()
        self._start_server()

    # ── menu actions ─────────────────────────────────────────

    def _open_browser(self):
        webbrowser.open(f'http://localhost:{PORT}')

    def _quit(self):
        logging.info('Shutting down SVN Tool...')
        self._stop_server()
        if self.icon:
            self.icon.stop()

    # ── tray menu ────────────────────────────────────────────

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem('Open in Browser', lambda: self._open_browser(),
                             default=True),
            pystray.MenuItem('Restart Server', lambda: self._restart_server()),
            pystray.MenuItem('Quit', lambda: self._quit()),
        )

    # ── entry point ──────────────────────────────────────────

    def run(self):
        self._start_server()
        self._open_browser()

        self.icon = pystray.Icon(
            'SVN Tool',
            _create_icon_image(),
            'SVN Tool',
            menu=self._build_menu(),
        )

        logging.info('SVN Tool tray app running')
        self.icon.run()  # blocks until icon.stop()


if __name__ == '__main__':
    SVNTrayApp().run()
