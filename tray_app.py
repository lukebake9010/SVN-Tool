"""
SVN External Manager - System Tray Application
Runs the Flask server as a background process with a system tray icon.
No console windows are created or shown.
"""

import os
import sys
import threading
import webbrowser
import signal

from PIL import Image, ImageDraw, ImageFont
import pystray
from werkzeug.serving import make_server

# Ensure we're running from the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app

HOST = '127.0.0.1'
PORT = 5000
URL = f'http://{HOST}:{PORT}'


class TrayApp:
    """System tray application wrapping the Flask server and pywebview window."""

    def __init__(self):
        self.server = None
        self.server_thread = None
        self.icon = None
        self.window = None
        self.webview_available = False

        try:
            import webview
            self.webview_available = True
        except ImportError:
            pass

    def create_icon_image(self):
        """Generate a simple tray icon with Pillow."""
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dark blue rounded-ish background
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

    def start_server(self):
        """Start the Flask server in a background thread."""
        self.server = make_server(HOST, PORT, app)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def stop_server(self):
        """Shut down the Flask server."""
        if self.server:
            self.server.shutdown()

    def open_window(self, _icon=None, _item=None):
        """Open or focus the pywebview window."""
        if not self.webview_available:
            self.open_browser()
            return

        import webview

        if self.window is None or self.window.uid is None:
            # Create a new window (runs in its own thread for pystray compat)
            def _create():
                self.window = webview.create_window(
                    'SVN External Manager',
                    URL,
                    width=1200,
                    height=800,
                    min_size=(800, 500),
                )
                webview.start()
                # webview.start() blocks until all windows close; clear ref
                self.window = None

            t = threading.Thread(target=_create, daemon=True)
            t.start()
        else:
            try:
                self.window.show()
                self.window.on_top = True
                self.window.on_top = False
            except Exception:
                pass

    def open_browser(self, _icon=None, _item=None):
        """Open the web UI in the default browser."""
        webbrowser.open(URL)

    def quit_app(self, _icon=None, _item=None):
        """Clean shutdown: server, webview, tray icon."""
        self.stop_server()

        if self.webview_available and self.window is not None:
            try:
                import webview
                for w in webview.windows:
                    w.destroy()
            except Exception:
                pass

        if self.icon:
            self.icon.stop()

    def build_menu(self):
        """Build the system tray context menu."""
        items = []
        if self.webview_available:
            items.append(pystray.MenuItem('Open Window', self.open_window, default=True))
        items.extend([
            pystray.MenuItem('Open in Browser', self.open_browser,
                             default=not self.webview_available),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.quit_app),
        ])
        return pystray.Menu(*items)

    def run(self):
        """Main entry point: start server, create tray icon, run event loop."""
        self.start_server()

        image = self.create_icon_image()
        self.icon = pystray.Icon(
            'svn-external-manager',
            image,
            'SVN External Manager',
            menu=self.build_menu(),
        )

        # Open the window/browser once the icon is ready
        def on_ready(icon):
            self.open_window()

        self.icon.run(setup=on_ready)


def main():
    app_instance = TrayApp()
    app_instance.run()


if __name__ == '__main__':
    main()
