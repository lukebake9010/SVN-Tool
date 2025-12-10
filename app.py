"""
SVN External Manager - Flask Web Application
A web-based tool for managing SVN externals with changelog viewing and copying.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from svn_manager import SVNManager
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration file path
CONFIG_FILE = 'config.json'

# Global SVN manager instance
svn_manager = None


def load_config():
    """Load configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Migrate old config format to new format
                if 'working_copy_path' in config and 'projects_directory' not in config:
                    # Old format: single working_copy_path
                    old_path = config['working_copy_path']
                    config['active_working_copy_path'] = old_path
                    # Try to determine projects directory from old path
                    if os.path.isdir(old_path):
                        config['projects_directory'] = os.path.dirname(old_path)
                    del config['working_copy_path']
                    save_config(config)
                return config
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def discover_working_copies(directory):
    """
    Scan directory for SVN working copies.

    Args:
        directory: Path to scan for working copies

    Returns:
        List of dicts with 'name' and 'path' for each discovered working copy
    """
    working_copies = []

    if not os.path.isdir(directory):
        return working_copies

    try:
        # Scan immediate subdirectories
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)

            # Skip if not a directory
            if not os.path.isdir(full_path):
                continue

            # Check if this directory has a .svn subdirectory
            svn_dir = os.path.join(full_path, '.svn')
            if os.path.isdir(svn_dir):
                working_copies.append({
                    'name': entry,
                    'path': full_path
                })

        # Sort by name
        working_copies.sort(key=lambda x: x['name'].lower())

    except (OSError, PermissionError) as e:
        print(f"Error scanning directory {directory}: {e}")

    return working_copies


def get_svn_manager():
    """Get or create SVN manager instance."""
    global svn_manager

    if svn_manager is None:
        config = load_config()
        working_copy = config.get('active_working_copy_path', os.getcwd())
        svn_manager = SVNManager(working_copy)

    return svn_manager


# Routes

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Check if SVN is available and get basic status."""
    manager = get_svn_manager()

    return jsonify({
        'svn_available': manager.check_svn_available(),
        'working_copy': manager.working_copy_path,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current configuration."""
    config = load_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def api_set_config():
    """Update configuration."""
    data = request.json
    config = load_config()
    config.update(data)

    if save_config(config):
        return jsonify({'success': True, 'config': config})
    else:
        return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500


@app.route('/api/working-copy', methods=['POST'])
def api_set_working_copy():
    """Set the working copy path (legacy endpoint for backward compatibility)."""
    data = request.json
    path = data.get('path')

    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400

    # Expand user path
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    manager = get_svn_manager()

    if manager.set_working_copy(path):
        # Save to config
        config = load_config()
        config['active_working_copy_path'] = path
        save_config(config)

        return jsonify({
            'success': True,
            'path': path
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid SVN working copy path'
        }), 400


@app.route('/api/working-copy/info')
def api_working_copy_info():
    """Get information about the current working copy."""
    manager = get_svn_manager()
    info = manager.get_working_copy_info()

    return jsonify(info)


@app.route('/api/working-copies', methods=['GET'])
def api_get_working_copies():
    """Get all discovered working copies from the projects directory."""
    config = load_config()
    projects_dir = config.get('projects_directory')

    if not projects_dir:
        return jsonify({
            'success': True,
            'working_copies': [],
            'projects_directory': None,
            'active_path': config.get('active_working_copy_path')
        })

    # Expand user path
    projects_dir = os.path.expanduser(projects_dir)
    projects_dir = os.path.abspath(projects_dir)

    working_copies = discover_working_copies(projects_dir)

    return jsonify({
        'success': True,
        'working_copies': working_copies,
        'projects_directory': projects_dir,
        'active_path': config.get('active_working_copy_path')
    })


@app.route('/api/working-copies/projects-directory', methods=['POST'])
def api_set_projects_directory():
    """Set the projects directory and discover working copies."""
    data = request.json
    path = data.get('path')

    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400

    # Expand user path
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    if not os.path.isdir(path):
        return jsonify({
            'success': False,
            'error': 'Path is not a valid directory'
        }), 400

    # Save to config
    config = load_config()
    config['projects_directory'] = path
    save_config(config)

    # Discover working copies
    working_copies = discover_working_copies(path)

    return jsonify({
        'success': True,
        'projects_directory': path,
        'working_copies': working_copies
    })


@app.route('/api/working-copies/activate', methods=['POST'])
def api_activate_working_copy():
    """Switch to a different working copy."""
    data = request.json
    path = data.get('path')

    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400

    # Expand user path
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    # Update SVN manager
    global svn_manager
    manager = get_svn_manager()

    if manager.set_working_copy(path):
        # Save to config
        config = load_config()
        config['active_working_copy_path'] = path
        save_config(config)

        return jsonify({
            'success': True,
            'path': path
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid SVN working copy path'
        }), 400


@app.route('/api/externals')
def api_externals():
    """Get all SVN externals from the working copy."""
    manager = get_svn_manager()

    try:
        externals = manager.get_externals()
        return jsonify({
            'success': True,
            'externals': externals,
            'count': len(externals),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/changed-externals')
def api_changed_externals():
    """Get externals with pending changes."""
    manager = get_svn_manager()

    try:
        changed = manager.get_changed_externals()
        return jsonify({
            'success': True,
            'changed': changed,
            'count': len(changed)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/log', methods=['GET'])
def api_log():
    """
    Get SVN log between two revisions.

    Query parameters:
        url: SVN URL
        old_rev: Starting revision
        new_rev: Ending revision
        format: Output format (plain, markdown, commit)
    """
    url = request.args.get('url')
    old_rev = request.args.get('old_rev')
    new_rev = request.args.get('new_rev')
    format_type = request.args.get('format', 'plain')

    if not all([url, old_rev, new_rev]):
        return jsonify({
            'success': False,
            'error': 'Missing required parameters: url, old_rev, new_rev'
        }), 400

    manager = get_svn_manager()

    try:
        # Get log in XML format
        xml_log = manager.get_log(url, old_rev, new_rev, 'xml')

        if xml_log is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve log'
            }), 500

        # Parse XML
        logs = manager.parse_log_xml(xml_log)

        # Get truncation setting from config (default: True)
        config = load_config()
        truncate_messages = config.get('truncate_tortoise_messages', True)

        # Format according to requested type
        formatted = manager.format_changelog(logs, format_type, truncate_messages)

        return jsonify({
            'success': True,
            'logs': logs,
            'formatted': formatted,
            'format': format_type,
            'revision_range': f"{old_rev}:{new_rev}"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/log/format', methods=['POST'])
def api_format_log():
    """
    Format existing log entries.

    Body:
        logs: Array of log entries
        format: Output format (plain, markdown, commit)
    """
    data = request.json
    logs = data.get('logs', [])
    format_type = data.get('format', 'plain')

    manager = get_svn_manager()

    try:
        # Get truncation setting from config (default: True)
        config = load_config()
        truncate_messages = config.get('truncate_tortoise_messages', True)

        formatted = manager.format_changelog(logs, format_type, truncate_messages)

        return jsonify({
            'success': True,
            'formatted': formatted,
            'format': format_type
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tortoisesvn/available', methods=['GET'])
def api_tortoisesvn_available():
    """Check if TortoiseSVN is available on the system."""
    manager = get_svn_manager()

    try:
        is_available = manager.check_tortoisesvn_available()
        return jsonify({
            'success': True,
            'available': is_available
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tortoisesvn/properties', methods=['POST'])
def api_open_tortoisesvn_properties():
    """
    Open TortoiseSVN properties dialog for a specific path.

    Body:
        parent_path: The path of the folder containing svn:externals
    """
    data = request.json
    parent_path = data.get('parent_path')

    if not parent_path:
        return jsonify({
            'success': False,
            'error': 'parent_path is required'
        }), 400

    manager = get_svn_manager()

    try:
        success, message = manager.open_tortoisesvn_properties(parent_path)

        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("SVN External Manager - Web Application")
    print("=" * 70)
    print(f"Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
