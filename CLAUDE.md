# CLAUDE.md - AI Assistant Guide for SVN External Manager

**Last Updated:** 2025-12-08
**Version:** 1.0.0

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Codebase Structure](#codebase-structure)
- [Core Components](#core-components)
- [Development Workflow](#development-workflow)
- [Key Conventions](#key-conventions)
- [API Patterns](#api-patterns)
- [Frontend Architecture](#frontend-architecture)
- [SVN Integration](#svn-integration)
- [Testing Strategy](#testing-strategy)
- [Common Tasks](#common-tasks)

## Project Overview

**SVN External Manager** is a Flask-based web application that provides a modern interface for managing SVN externals. The primary use case is quickly viewing and copying changelogs for external dependencies.

### Key Features
- Auto-detection and display of all SVN externals from a working copy
- Real-time status tracking (Clean, Modified, Error, Missing, New, Changed)
- Changelog viewing with multiple export formats (Plain, Markdown, Commit)
- One-click copy to clipboard functionality
- External definition change detection (compares working vs BASE)

### Technology Stack
- **Backend:** Python 3.7+, Flask 3.0.0, Flask-CORS 4.0.0
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3
- **External Dependency:** Subversion (svn) command-line client
- **Data Format:** JSON for config, XML parsing for SVN logs

## Architecture

### High-Level Design
```
┌─────────────────┐
│   Web Browser   │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/JSON API
         ▼
┌─────────────────┐
│  Flask Server   │
│    (app.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  SVN Manager    │◄────►│ SVN CLI      │
│ (svn_manager.py)│      │ (subprocess) │
└─────────────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  config.json    │
│  (persistence)  │
└─────────────────┘
```

### Design Principles
1. **Separation of Concerns:** SVN operations isolated in `svn_manager.py`
2. **Stateless API:** Each API call is independent
3. **Global State Management:** Single SVN manager instance per server lifecycle
4. **Configuration Persistence:** JSON-based config auto-saves on changes
5. **Error Handling:** Graceful degradation with informative error messages

## Codebase Structure

```
SVN-Tool/
├── app.py                      # Flask application and API routes
├── svn_manager.py              # SVN operations and business logic
├── requirements.txt            # Python dependencies
├── config.json                 # Runtime configuration (auto-generated)
├── run.sh / run.bat           # Quick start scripts
├── test_external_detection.py  # Test script for change detection
├── debug_externals.py          # Debug/development utility
├── templates/
│   └── index.html             # Single-page application HTML
├── static/
│   ├── css/
│   │   └── style.css          # Application styles (~850 lines)
│   └── js/
│       └── app.js             # Frontend application logic (~750 lines)
├── README.md                   # User documentation
├── QUICKSTART.md              # Quick start guide
└── CLAUDE.md                  # This file (AI assistant guide)
```

### File Line Counts
- `svn_manager.py`: 450 lines (core SVN logic)
- `app.py`: 289 lines (Flask routes and API)
- `static/js/app.js`: 757 lines (frontend JavaScript)
- `static/css/style.css`: 851 lines (styling)
- `templates/index.html`: 279 lines (HTML structure)

## Core Components

### 1. SVN Manager (`svn_manager.py`)

**Purpose:** Encapsulates all SVN command-line interactions and business logic.

**Key Methods:**
- `get_externals()` - Main method: retrieves and analyzes all externals
- `_get_externals_from_propget()` - Fetches externals via `svn propget`
- `_parse_external_definition()` - Parses external definition strings
- `_get_external_status()` - Compares working vs BASE to detect changes
- `get_changed_externals()` - Filters externals with 'changed' or 'new' status
- `get_log()` - Fetches SVN log between revisions
- `parse_log_xml()` - Parses SVN XML log output
- `format_changelog()` - Formats logs in plain/markdown/commit format

**Critical Implementation Details:**

#### External Definition Parsing
Supports multiple SVN external formats:
```
# Old format
local_path -r123 https://example.com/repo

# New format
-r123 https://example.com/repo local_path

# Peg revision format (takes precedence)
https://example.com/repo@123 local_path

# URL with spaces (quoted)
"https://example.com/path%20with%20spaces" local_path
```

Uses `shlex.split()` for proper quote handling and `urllib.parse.unquote()` for URL decoding.

#### Change Detection Algorithm
1. Fetch working externals (current state in WC)
2. Fetch BASE externals (pristine/committed state)
3. Compare by `parent_path:name` key
4. Detect changes in: revision, URL, or path
5. Classify as: 'changed', 'new', 'clean', 'missing', or 'error'

**Status Values:**
- `clean`: No changes, directory exists
- `changed`: Definition modified (revision/URL/path change)
- `new`: External added (not in BASE)
- `missing`: Directory doesn't exist
- `error`: Exception during status check

### 2. Flask Application (`app.py`)

**Purpose:** HTTP server providing REST API and serving frontend.

**Key Routes:**

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serve main HTML page |
| `/api/status` | GET | Check SVN availability and WC path |
| `/api/config` | GET/POST | Get/update configuration |
| `/api/working-copy` | POST | Set working copy path |
| `/api/working-copy/info` | GET | Get WC SVN info |
| `/api/externals` | GET | List all externals |
| `/api/changed-externals` | GET | List only changed externals |
| `/api/log` | GET | Fetch changelog (query params: url, old_rev, new_rev, format) |
| `/api/log/format` | POST | Reformat existing log entries |

**Global State:**
- `svn_manager`: Single instance, initialized on first use
- `CONFIG_FILE`: Path to `config.json`

**Configuration Management:**
- `load_config()`: Read config from JSON file
- `save_config()`: Write config to JSON file
- Auto-creates config file if missing

### 3. Frontend (`static/js/app.js`)

**Purpose:** Single-page application handling UI interactions.

**Global State:**
```javascript
externalsData = [];      // Full list of externals
filteredData = [];       // Filtered/sorted view
currentSort = {};        // Current sort state
autoRefreshInterval;     // Auto-refresh timer
currentChangelog = {};   // Currently displayed changelog
```

**Key Functions:**
- `initializeApp()`: Entry point, sets up listeners
- `loadExternals()`: Fetch and display externals
- `filterExternals()`: Apply search and status filters
- `sortTable()`: Column-based sorting
- `viewChangelog()`: Open changelog modal for external
- `copyChangelog()`: Copy formatted changelog to clipboard
- `saveSettings()`: Persist configuration

**UI Patterns:**
- Toast notifications for user feedback
- Modal dialogs for settings and changelogs
- Real-time search filtering
- Status badges with color coding

## Development Workflow

### Git Branch Strategy

Based on recent commit history:
- `main`: Production-ready code
- Feature branches: `claude/<description>-<session-id>`
- PR workflow: Features merged via pull requests

### Recent Development History
```
07804b2 - Merge PR #2 (external change detection fix)
7da2322 - Add peg revision format support (URL@REV)
54a2d06 - Fix revision parsing with debug logging
9d01e29 - Add automatic changelog for external changes
b129247 - Fix external change detection (working vs BASE)
7eaa1c2 - Merge PR #1 (initial web GUI)
6997707 - Fix external parsing for spaces and URL encoding
78afb4c - Add initial SVN External Manager
```

### Development Commands

**Start Development Server:**
```bash
python app.py
# Server runs on http://localhost:5000 in debug mode
```

**Test External Detection:**
```bash
python test_external_detection.py
# Demonstrates change detection functionality
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
# or use run.sh / run.bat for automated setup
```

### Debug Mode Features
- Auto-reload on code changes (Flask debug=True)
- Detailed error messages in browser
- Console logging for SVN commands

## Key Conventions

### Code Style

**Python:**
- PEP 8 compliant
- Docstrings for all classes and public methods
- Type hints preferred (List[Dict], Optional[str], etc.)
- Exception handling with specific catches

**JavaScript:**
- ES6+ features (arrow functions, const/let, template literals)
- JSDoc comments for complex functions
- camelCase for variables and functions
- Event delegation where appropriate

### Naming Conventions

**Python:**
- Functions/methods: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

**JavaScript:**
- Functions: `camelCase`
- Constants: `camelCase` or `UPPER_CASE`
- DOM IDs: `camelCase` with type suffix (e.g., `refreshBtn`, `searchInput`)

### Error Handling Patterns

**Backend:**
```python
try:
    result = subprocess.run(...)
    if result.returncode != 0:
        return None  # Graceful failure
except subprocess.SubprocessError as e:
    print(f"Error: {e}")  # Log for debugging
    return None
```

**API Responses:**
```python
# Success
return jsonify({'success': True, 'data': ...})

# Error
return jsonify({'success': False, 'error': 'message'}), 400
```

**Frontend:**
```javascript
fetch('/api/endpoint')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Handle success
        } else {
            showToast(data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Network error', 'error');
    });
```

## API Patterns

### Request/Response Format

All API endpoints return JSON with this structure:

**Success Response:**
```json
{
    "success": true,
    "data": { ... },
    "timestamp": "2025-12-08T12:00:00"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Error description"
}
```

### Query Parameters vs Request Body

- **GET requests:** Use query parameters
  ```
  /api/log?url=https://...&old_rev=123&new_rev=456&format=plain
  ```

- **POST requests:** Use JSON body
  ```json
  POST /api/working-copy
  { "path": "/path/to/working/copy" }
  ```

### Status Codes
- `200`: Success
- `400`: Bad request (missing params, invalid input)
- `404`: Not found
- `500`: Internal server error

## Frontend Architecture

### Data Flow

1. User interaction triggers event listener
2. JavaScript function fetches data via API
3. Response parsed and validated
4. DOM updated with new data
5. Toast notification confirms action

### State Management

**Global Variables:**
- Avoid excessive global state
- Use closure for modal-specific state
- Clear state when closing modals

**DOM Updates:**
- Batch DOM operations for performance
- Use `innerHTML` for table rows (safe, controlled data)
- Clear tables before repopulating

### Modal Pattern

```javascript
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    // Clear modal state here
}
```

### Toast Notification Pattern

```javascript
showToast('Message', 'success');  // Green
showToast('Message', 'error');    // Red
showToast('Message', 'info');     // Blue
```

## SVN Integration

### Command Execution Pattern

All SVN commands follow this pattern:

```python
try:
    result = subprocess.run(
        [self.svn_command, "subcommand", ...args],
        capture_output=True,
        text=True,
        timeout=30,  # Prevent hanging
        cwd=self.working_copy_path  # Context
    )

    if result.returncode != 0:
        # Log stderr for debugging
        print(f"SVN error: {result.stderr}")
        return None

    return result.stdout

except subprocess.SubprocessError as e:
    print(f"Error: {e}")
    return None
```

### Key SVN Commands Used

**Get externals (working):**
```bash
svn propget svn:externals -R <path>
```

**Get externals (pristine/BASE):**
```bash
svn propget svn:externals -R -r BASE <path>
```

**Get changelog:**
```bash
svn log -r<old>:<new> <url> --xml
```

**Get working copy info:**
```bash
svn info <path>
```

### Parsing Strategies

**Property Output:**
- Format: `path - definition`
- Multi-line definitions continue without `path -` prefix
- Track `current_path` across lines

**External Definitions:**
- Use `shlex.split()` for proper quote handling
- Extract `-r` flags first
- Determine URL vs local_path by URL pattern matching
- Support both old and new format
- Handle peg revisions (`@REV`) with priority over `-r`

**XML Logs:**
- Use `xml.etree.ElementTree`
- Extract: revision, author, date, message
- Parse ISO 8601 dates to readable format

## Testing Strategy

### Manual Testing

**Test Script:** `test_external_detection.py`

**Purpose:**
- Verify external detection works
- Demonstrate change detection
- Validate status classification

**Test Cases:**
1. No externals found
2. Clean externals (no changes)
3. Changed revision
4. Changed URL
5. New external added
6. Missing external directory

### Testing Workflow

1. Set up test working copy with externals
2. Run `python test_external_detection.py`
3. Modify external definition
4. Run test again to see change detection
5. Verify changelog fetching via web UI

### Debug Utilities

**`debug_externals.py`:**
- Development/troubleshooting script
- Check external parsing edge cases

**Console Logging:**
```python
print(f"Executing SVN log command: {' '.join(cmd)}")
print(f"SVN log command failed with code {result.returncode}")
```

## Common Tasks

### Adding a New API Endpoint

1. **Define route in `app.py`:**
   ```python
   @app.route('/api/new-endpoint', methods=['GET'])
   def api_new_endpoint():
       manager = get_svn_manager()
       try:
           result = manager.new_method()
           return jsonify({'success': True, 'data': result})
       except Exception as e:
           return jsonify({'success': False, 'error': str(e)}), 500
   ```

2. **Implement logic in `svn_manager.py`:**
   ```python
   def new_method(self) -> Optional[Dict]:
       """Method description."""
       try:
           # Implementation
           return result
       except subprocess.SubprocessError as e:
           print(f"Error: {e}")
           return None
   ```

3. **Call from frontend in `app.js`:**
   ```javascript
   function callNewEndpoint() {
       fetch('/api/new-endpoint')
           .then(response => response.json())
           .then(data => {
               if (data.success) {
                   // Handle data
               }
           });
   }
   ```

### Adding a New External Format

1. **Update `_parse_external_definition()` in `svn_manager.py`**
2. **Add parsing logic for new format**
3. **Add test case in `test_external_detection.py`**
4. **Document format in code comments**

### Adding a New Changelog Format

1. **Update `format_changelog()` in `svn_manager.py`:**
   ```python
   elif format_type == 'new_format':
       output = ""
       for log in logs:
           output += f"Custom format: {log['revision']}\n"
       return output
   ```

2. **Add option to format dropdown in `index.html`:**
   ```html
   <option value="new_format">New Format</option>
   ```

3. **Update frontend default format handling**

### Modifying Status Detection

Status logic is in `_get_external_status()`:

1. **Add new status type:**
   - Update return values
   - Add to status badge CSS
   - Update filter checkboxes in UI

2. **Modify comparison logic:**
   - Change detection in `changes` dict
   - Update `has_changes` condition

### Debugging SVN Issues

1. **Enable verbose logging:**
   ```python
   print(f"Executing: {' '.join(cmd)}")
   print(f"Result: {result.stdout}")
   ```

2. **Test SVN command manually:**
   ```bash
   svn propget svn:externals -R /path/to/wc
   ```

3. **Check working copy path:**
   ```python
   manager = SVNManager("/explicit/path")
   info = manager.get_working_copy_info()
   print(info)
   ```

## Important Notes for AI Assistants

### Do's ✓

1. **Always read existing code before modifying**
   - Understand patterns before suggesting changes
   - Match existing code style

2. **Test SVN integration changes carefully**
   - SVN behavior varies across versions
   - External formats have multiple valid syntaxes

3. **Preserve backward compatibility**
   - Config file format
   - API response structure
   - External definition parsing

4. **Use subprocess with timeouts**
   - Prevents hanging on network issues
   - Always catch `subprocess.SubprocessError`

5. **Validate user input**
   - Check paths exist before setting
   - Validate revision numbers
   - Sanitize URLs

6. **Maintain separation of concerns**
   - SVN logic in `svn_manager.py`
   - API routes in `app.py`
   - UI logic in `app.js`

### Don'ts ✗

1. **Don't bypass SVN Manager**
   - Always use `svn_manager.py` for SVN operations
   - Never call subprocess directly from `app.py`

2. **Don't break the config format**
   - `config.json` is user-facing
   - Changes need migration logic

3. **Don't assume SVN URL format**
   - Support http://, https://, svn://, svn+ssh://, file://, ^/
   - Handle URL encoding properly

4. **Don't ignore error cases**
   - SVN commands can fail (network, permissions, etc.)
   - Always return meaningful error messages

5. **Don't add heavy dependencies**
   - Keep requirements minimal
   - Prefer stdlib where possible

6. **Don't modify global state carelessly**
   - `svn_manager` instance is shared
   - Config changes must be persisted

### Common Pitfalls

1. **External definition parsing edge cases:**
   - Quoted paths with spaces
   - URL encoding (%20)
   - Peg revisions (@REV)
   - Both old and new formats

2. **Change detection accuracy:**
   - Must compare working vs BASE (not WC status)
   - Key by `parent_path:name`
   - Handle missing externals in BASE (new externals)

3. **Frontend state management:**
   - Clear modal state on close
   - Reset sort/filter state appropriately
   - Handle empty/error states

4. **SVN command timeouts:**
   - Network operations can hang
   - Always use timeout parameter
   - Provide feedback to user

### Quick Reference: Key Files to Modify

| Task | Files to Modify |
|------|----------------|
| Add SVN operation | `svn_manager.py` |
| Add API endpoint | `app.py` |
| Change UI behavior | `static/js/app.js` |
| Update styles | `static/css/style.css` |
| Modify page structure | `templates/index.html` |
| Change config schema | `app.py` (load/save) + migration |
| Add changelog format | `svn_manager.py` (format_changelog) + `index.html` (dropdown) |

---

## Changelog

### v1.0.0 (2025-12-08)
- Initial CLAUDE.md creation
- Documented complete codebase structure
- Added development workflows and conventions
- Included SVN integration patterns
- Added troubleshooting guide for AI assistants

---

**For questions or clarifications, refer to:**
- `README.md` - User-facing documentation
- `QUICKSTART.md` - Quick start guide
- Inline code comments in source files
- Recent commit messages for context on changes
