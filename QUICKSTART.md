# Quick Start Guide

Get started with SVN External Manager in 3 easy steps!

## Step 1: Install Dependencies

### Linux/macOS
```bash
./run.sh
```

### Windows
```cmd
run.bat
```

Or manually:
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Start the Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

## Step 3: Configure & Use

1. Open `http://localhost:5000` in your browser
2. Click the Settings icon (⚙️)
3. Set your SVN working copy path
4. Click "Refresh" to load externals
5. Click "View Log" on any external to see its changelog

## That's It! 🎉

You're now ready to manage your SVN externals!

## Need Help?

- Read the full [README.md](README.md) for detailed documentation
- Check the [Troubleshooting](README.md#troubleshooting) section
- View the API documentation for programmatic access

## Features to Try

- 🔍 Use the search box to find specific externals
- 📋 Click "Copy Changelog" to copy formatted logs
- 🔄 Enable auto-refresh in settings for automatic updates
- 📝 Try different changelog formats (Plain, Markdown, Commit)

Enjoy! 🚀
