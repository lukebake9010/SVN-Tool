"""
Standalone pywebview window process.
Launched by tray_app.py as a separate pythonw process so that pywebview
can own the main thread (required on Windows).

Usage: pythonw _webview_window.py <url>
"""

import sys

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    url = sys.argv[1]

    try:
        import webview
    except ImportError:
        sys.exit(1)

    webview.create_window(
        'SVN External Manager',
        url,
        width=1200,
        height=800,
        min_size=(800, 500),
    )
    webview.start()


if __name__ == '__main__':
    main()
