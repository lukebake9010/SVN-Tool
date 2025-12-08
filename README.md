# SVN External Manager - Web GUI Application

A modern, web-based tool for managing SVN externals with a focus on quickly viewing and copying changelogs. This application provides a clean, intuitive interface for browsing externals, viewing their status, and accessing detailed changelog information.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

### 🎯 Core Functionality

- **Dashboard View**: Auto-detect and display all SVN externals from your working copy
- **Smart Filtering**: Sort and filter externals by name, status, revision, or URL
- **Status Tracking**: Real-time status indicators (Clean, Modified, Error, Missing)
- **Instant Search**: Quickly find specific externals with live search

### 📊 Changelog Management

- **One-Click Changelog**: View detailed commit history for any external
- **Multiple Formats**: Export changelogs in Plain Text, Markdown, or Commit Format
- **Copy to Clipboard**: Instantly copy formatted changelogs with a single click
- **Manual Lookup**: Fetch logs for custom URL and revision ranges

### ⚙️ Configuration

- **Working Copy Selection**: Easily switch between different SVN working copies
- **Auto-Refresh**: Optionally auto-refresh externals at configurable intervals
- **Persistent Settings**: All preferences are saved automatically

### 🎨 User Experience

- **Modern UI**: Clean, responsive design that works on desktop and mobile
- **Dark Header**: Easy-on-the-eyes interface with professional styling
- **Toast Notifications**: Non-intrusive feedback for all operations
- **Keyboard Shortcuts**: Efficient navigation and actions

## Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Changelog Viewer
![Changelog](docs/screenshots/changelog.png)

## Installation

### Prerequisites

- Python 3.7 or higher
- Subversion (SVN) command-line client
- A valid SVN working copy

### Step 1: Install SVN

Make sure you have Subversion installed and accessible from your command line:

```bash
# Check if SVN is installed
svn --version

# If not installed:
# Ubuntu/Debian
sudo apt-get install subversion

# macOS (with Homebrew)
brew install subversion

# Windows
# Download from https://tortoisesvn.net/
```

### Step 2: Clone or Download

```bash
git clone <repository-url>
cd SVN-Tool
```

### Step 3: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python app.py
```

The application will start on `http://localhost:5000`. Open this URL in your web browser.

```
======================================================================
SVN External Manager - Web Application
======================================================================
Starting server at http://localhost:5000
Press Ctrl+C to stop
======================================================================
```

### First Time Setup

1. **Set Working Copy Path**
   - Click the Settings icon (⚙️) in the header
   - Enter the path to your SVN working copy
   - Click "Set Path"

2. **Load Externals**
   - Click the "Refresh" button to scan for externals
   - All externals will be displayed in the table

3. **View Changelog**
   - Click "View Log" on any external
   - Select your preferred format (Plain, Markdown, or Commit)
   - Click "Copy Changelog" to copy to clipboard

### Features Guide

#### Dashboard

- **Search**: Type in the search box to filter externals by name, path, or URL
- **Filters**: Toggle checkboxes to show/hide externals by status
- **Sorting**: Click column headers to sort the table
- **Refresh**: Click the refresh button to reload externals

#### Viewing Changelogs

1. Click "View Log" button on any external row
2. The changelog modal will open showing all commits
3. Use the format dropdown to change the output format:
   - **Plain Text**: Simple, readable format
   - **Markdown**: Formatted with Markdown headers
   - **Commit Format**: Compact format suitable for commit messages
4. Click "Copy Changelog" to copy to clipboard

#### Settings

Access settings by clicking the gear icon (⚙️):

- **Working Copy Path**: Set or change your SVN working copy location
- **Auto-Refresh**: Enable automatic refreshing of externals
  - Set refresh interval (10-3600 seconds)
- **Default Format**: Choose default changelog format

## API Documentation

The application provides a REST API for programmatic access.

### Endpoints

#### Get Status
```
GET /api/status
```
Returns SVN availability and working copy information.

#### Get Externals
```
GET /api/externals
```
Returns all externals from the working copy.

Response:
```json
{
  "success": true,
  "externals": [
    {
      "name": "external-name",
      "path": "path/to/external",
      "url": "https://svn.example.com/repo/path",
      "revision": "1234",
      "status": "clean"
    }
  ],
  "count": 1,
  "timestamp": "2025-12-08T12:00:00"
}
```

#### Get Changelog
```
GET /api/log?url=<url>&old_rev=<rev>&new_rev=<rev>&format=<format>
```

Parameters:
- `url`: SVN URL
- `old_rev`: Starting revision number
- `new_rev`: Ending revision number (or "HEAD")
- `format`: Output format (plain, markdown, commit)

Response:
```json
{
  "success": true,
  "logs": [
    {
      "revision": "1234",
      "author": "user",
      "date": "2025-12-08 12:00:00",
      "message": "Commit message"
    }
  ],
  "formatted": "Formatted changelog text",
  "format": "plain",
  "revision_range": "1234:1235"
}
```

#### Set Working Copy
```
POST /api/working-copy
Content-Type: application/json

{
  "path": "/path/to/working/copy"
}
```

#### Update Configuration
```
POST /api/config
Content-Type: application/json

{
  "auto_refresh": true,
  "auto_refresh_interval": 60,
  "default_format": "plain"
}
```

## Configuration

Configuration is stored in `config.json` (automatically created):

```json
{
  "working_copy_path": "/path/to/working/copy",
  "auto_refresh": false,
  "auto_refresh_interval": 60,
  "default_format": "plain"
}
```

## Project Structure

```
SVN-Tool/
├── app.py                 # Flask application
├── svn_manager.py         # SVN operations module
├── requirements.txt       # Python dependencies
├── config.json           # Configuration (auto-generated)
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file
```

## Development

### Running in Development Mode

The application runs in debug mode by default when started with `python app.py`. This enables:

- Auto-reload on code changes
- Detailed error messages
- Debug toolbar

### Adding Features

1. **Backend**: Modify `svn_manager.py` for SVN operations or `app.py` for API endpoints
2. **Frontend**: Edit `static/js/app.js` for JavaScript logic
3. **Styling**: Update `static/css/style.css` for appearance changes
4. **HTML**: Modify `templates/index.html` for structure changes

### Testing

```bash
# Test SVN integration
python -c "from svn_manager import SVNManager; m = SVNManager('/path/to/wc'); print(m.get_externals())"

# Test API endpoints
curl http://localhost:5000/api/status
curl http://localhost:5000/api/externals
```

## Troubleshooting

### SVN Not Available

**Problem**: "SVN Not Available" status badge

**Solution**:
- Verify SVN is installed: `svn --version`
- Ensure SVN is in your PATH
- Restart the application after installing SVN

### No Externals Found

**Problem**: Empty externals list

**Solution**:
- Verify you're pointing to a valid SVN working copy
- Check that the working copy has `svn:externals` properties
- Run `svn propget svn:externals -R .` manually to verify

### Cannot Load Changelog

**Problem**: Error loading changelog

**Solution**:
- Verify the SVN URL is accessible
- Check network connectivity
- Ensure you have permission to access the repository
- Try with specific revision numbers instead of "HEAD"

### Port Already in Use

**Problem**: "Address already in use" error

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000
# Or on Windows
netstat -ano | findstr :5000

# Kill the process or change the port in app.py
```

## Security Notes

- This application is designed for **local use only**
- Do not expose to the internet without proper authentication
- Be cautious with SVN credentials (use SSH keys when possible)
- The application does not store any passwords

## Performance Tips

1. **Large Working Copies**: Scanning many externals may take time. Use auto-refresh sparingly.
2. **Network**: Changelog fetching requires network access to SVN repository
3. **Revision Ranges**: Smaller revision ranges load faster

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Changelog

### Version 1.0.0 (2025-12-08)

- Initial release
- Dashboard with externals table
- Changelog viewer with multiple formats
- Copy to clipboard functionality
- Settings management
- Auto-refresh capability
- Responsive design
- Toast notifications

## Support

For issues, questions, or suggestions:

1. Check the Troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with detailed information

## Acknowledgments

- Built with Flask and modern web technologies
- Icons by Font Awesome
- Inspired by TortoiseSVN

---

**Made with ❤️ for SVN users who need quick access to external changelogs**
