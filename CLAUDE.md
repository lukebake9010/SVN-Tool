# CLAUDE.md

Flask web app for viewing and copying SVN external changelogs. Python backend, vanilla JS frontend, no build step.

## Architecture

- `svn_manager.py` -- all SVN subprocess calls and business logic. Never call subprocess from `app.py`.
- `app.py` -- Flask routes and config persistence (`config.json`). Single global `svn_manager` instance.
- `static/js/app.js` -- SPA frontend. Fetches JSON from `/api/*`, updates DOM directly.
- `templates/index.html` -- page shell. Icons via Font Awesome CDN.
- `static/css/style.css` -- all styles.

## Commands

```bash
# Run dev server (debug mode, auto-reload)
python3 app.py

# Or use the startup script (creates venv + installs deps automatically)
./run.sh        # Linux/macOS
run.bat         # Windows

# Install deps manually
pip install -r requirements.txt
```

## Key patterns

**API responses** always return `{"success": true/false, ...}`. Errors include `"error": "message"` and an appropriate HTTP status (400/500).

**SVN commands** use `subprocess.run()` with `timeout=30` and `capture_output=True`. Always check `returncode != 0` and catch `SubprocessError`.

**Config** lives in `config.json` (git-ignored). Key fields: `projects_directory`, `active_working_copy_path`, `auto_refresh`, `auto_refresh_interval`, `default_format`, `truncate_tortoise_messages`. Old `working_copy_path` key is auto-migrated in `load_config()`.

**Change detection** compares `svn propget svn:externals -R` (working) vs `-r BASE` (pristine), keyed by `parent_path:name`. Statuses: `clean`, `changed`, `new`, `missing`, `error`.

**External definition parsing** (`_parse_external_definition`) handles old format, new format, peg revisions (`URL@REV`), quoted paths, and URL-encoded characters. Uses `shlex.split()`. Peg revision takes precedence over `-r` flag.

**Changelog formats**: plain, markdown, commit, tortoise. To add one: update `format_changelog()` in `svn_manager.py` and add an `<option>` in `index.html`.

## Things to watch out for

- SVN external definitions have many valid syntaxes -- test parsing changes against all formats (old, new, peg, quoted, URL-encoded).
- Config schema changes need migration logic in `load_config()` to avoid breaking existing users.
- The server binds to `0.0.0.0:5000` with no auth -- intended for local use only.
- `run.sh` uses `python3` for venv creation but `python` after activation (venv symlink). Some systems may not have `python3`.
- SVN URL schemes to support: `http://`, `https://`, `svn://`, `svn+ssh://`, `file://`, `^/`.
- Frontend uses `innerHTML` for table rows -- data comes from SVN (trusted), not user input.

## Where to make changes

| Task | Files |
|------|-------|
| SVN operation | `svn_manager.py` |
| API endpoint | `app.py` |
| UI behavior | `static/js/app.js` |
| Page structure | `templates/index.html` |
| Styles | `static/css/style.css` |
| Config schema | `app.py` (`load_config`/`save_config`) + migration |
| Changelog format | `svn_manager.py` (`format_changelog`) + `index.html` (dropdown) |
| Status type | `svn_manager.py` (`_get_external_status`) + `style.css` (badge) + `index.html` (filter checkbox) |
