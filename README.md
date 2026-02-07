# SVN External Manager

A web-based tool for managing SVN externals. View external definitions, detect changes, and copy changelogs in multiple formats.

![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- Auto-detect and display all SVN externals from a working copy
- Change detection: compares working vs BASE definitions to flag changed, new, or missing externals
- Changelog viewer with Plain Text, Markdown, Commit, and TortoiseSVN formats
- One-click copy to clipboard
- Multiple working copy support via a projects directory (tab-based switching)
- TortoiseSVN properties dialog integration (Windows)
- Search, filter by status, and sort columns
- Auto-refresh at configurable intervals
- Persistent settings saved to `config.json`

## Prerequisites

- **Python 3.7+**
- **Subversion (SVN) command-line client** (`svn` must be on your PATH)
- An SVN working copy to point the tool at

### Installing SVN

```bash
# Check if SVN is already installed
svn --version

# Ubuntu/Debian
sudo apt-get install subversion

# macOS (Homebrew)
brew install subversion

# Windows - install TortoiseSVN (includes command-line tools)
# or use the standalone Subversion binaries
```

## Installation

### Quick start (recommended)

The startup scripts create a virtual environment, install dependencies, and launch the server automatically.

**Linux / macOS:**

```bash
git clone <repository-url>
cd SVN-Tool
chmod +x run.sh
./run.sh
```

**Windows:**

```cmd
git clone <repository-url>
cd SVN-Tool
run.bat
```

### Manual install

```bash
git clone <repository-url>
cd SVN-Tool

# Create and activate a virtual environment
python3 -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 app.py
```

> **Note:** On some systems the Python binary is named `python` instead of `python3`. Use whichever is available. The `run.sh` script uses `python3`; if your system only has `python`, edit the script or use the manual steps above.

The server starts on **http://localhost:5000**. It binds to `0.0.0.0`, so it is also reachable from other machines on the network. Keep this in mind if you are on a shared network -- this tool is intended for local use and has no authentication.

## Getting started

1. Open `http://localhost:5000` in a browser.
2. Click the **Settings** gear icon.
3. Set your **Projects Directory** (a folder containing one or more SVN working copies). Each subdirectory with a `.svn` folder will appear as a tab.
   - Alternatively, set a **Single Working Copy Path** if you only work with one checkout.
4. Click **Refresh** to scan for externals.
5. Click **View Log** on any external to see its changelog. Pick a format and click **Copy Changelog**.

## Configuration

Settings are persisted in `config.json` (auto-created, git-ignored). Current options:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `projects_directory` | string | — | Directory to scan for SVN working copies |
| `active_working_copy_path` | string | cwd | Currently active working copy |
| `auto_refresh` | bool | `false` | Enable periodic external refresh |
| `auto_refresh_interval` | int | `60` | Refresh interval in seconds (10-3600) |
| `default_format` | string | `"plain"` | Default changelog format |
| `truncate_tortoise_messages` | bool | `true` | Truncate TortoiseSVN format to first line / 240 chars |

## Changelog formats

| Format | Description |
|--------|-------------|
| **Plain Text** | Verbose: revision, author, date, and full message per entry |
| **Markdown** | Markdown-formatted with headers per revision |
| **Commit** | Compact one-liner per revision, suitable for commit messages |
| **TortoiseSVN** | Matches TortoiseSVN's log style (newest first, optional truncation) |

## External status values

| Status | Meaning |
|--------|---------|
| `clean` | Definition unchanged, directory exists |
| `changed` | Definition modified (revision, URL, or path differs from BASE) |
| `new` | External added (present in working copy but not in BASE) |
| `missing` | Directory does not exist on disk |
| `error` | Exception during status check |

## API reference

All endpoints return JSON. Success responses include `"success": true`; errors include `"success": false` and an `"error"` message.

### Status and config

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | SVN availability and working copy path |
| GET | `/api/config` | Current configuration |
| POST | `/api/config` | Update configuration (JSON body) |

### Working copies

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/working-copy` | Set working copy path (`{"path": "..."}`) |
| GET | `/api/working-copy/info` | SVN info for current working copy |
| GET | `/api/working-copies` | List discovered working copies |
| POST | `/api/working-copies/projects-directory` | Set projects directory (`{"path": "..."}`) |
| POST | `/api/working-copies/activate` | Switch active working copy (`{"path": "..."}`) |

### Externals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/externals` | List all externals |
| GET | `/api/changed-externals` | List externals with `changed` or `new` status |

### Changelog

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/log?url=...&old_rev=...&new_rev=...&format=...` | Fetch SVN log between two revisions |
| POST | `/api/log/format` | Re-format existing log entries (`{"logs": [...], "format": "..."}`) |

### TortoiseSVN (Windows)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tortoisesvn/available` | Check if TortoiseSVN is installed |
| POST | `/api/tortoisesvn/properties` | Open TortoiseSVN properties dialog (`{"parent_path": "...", "open_externals": true}`) |

## Project structure

```
SVN-Tool/
├── app.py                      # Flask routes and API
├── svn_manager.py              # SVN operations and business logic
├── requirements.txt            # Python dependencies (Flask, Flask-CORS, Werkzeug)
├── config.json                 # Runtime config (auto-generated, git-ignored)
├── run.sh                      # Linux/macOS startup script
├── run.bat                     # Windows startup script
├── templates/
│   └── index.html              # Single-page application
├── static/
│   ├── css/
│   │   └── style.css           # Styles
│   └── js/
│       └── app.js              # Frontend logic
├── test_external_detection.py  # Change detection test script
├── debug_externals.py          # Debug/development utility
├── CLAUDE.md                   # AI assistant guide
└── LICENSE                     # MIT license
```

## Troubleshooting

**"SVN Not Available" status badge**
Verify `svn --version` works in your terminal. If you installed SVN after starting the server, restart it.

**Empty externals list**
Check that the working copy path is correct and that `svn:externals` properties are set. Test manually: `svn propget svn:externals -R /path/to/wc`.

**`python3: command not found` (Linux/macOS)**
Some systems only have `python`. Edit `run.sh` to replace `python3` with `python`, or use the manual install steps with your available binary.

**`python: command not found` (Windows)**
Ensure Python is on your PATH. If you installed from python.org, check the "Add to PATH" option during installation.

**Port 5000 already in use**
Another process is using port 5000. Find it with `lsof -i :5000` (Linux/macOS) or `netstat -ano | findstr :5000` (Windows) and stop it, or change the port in `app.py`.

**Changelog fetch fails**
Verify network access to the SVN repository and that you have read permissions. Try a smaller revision range or specific revision numbers instead of `HEAD`.

## Development

The server runs in Flask debug mode (`debug=True`), so it auto-reloads on code changes.

- SVN operations: `svn_manager.py`
- API routes: `app.py`
- Frontend logic: `static/js/app.js`
- Styles: `static/css/style.css`
- Page structure: `templates/index.html`

Icons are loaded from Font Awesome via CDN (`index.html`).

## License

MIT -- see [LICENSE](LICENSE).
