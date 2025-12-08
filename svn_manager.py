"""
SVN Manager Module
Handles all SVN operations including listing externals, detecting changes, and fetching logs.
"""

import subprocess
import re
import os
import shlex
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class SVNManager:
    """Manages SVN operations for external management."""

    def __init__(self, working_copy_path: str = None):
        """Initialize SVN Manager with optional working copy path."""
        self.working_copy_path = working_copy_path or os.getcwd()
        self.svn_command = "svn"

    def set_working_copy(self, path: str) -> bool:
        """Set the working copy path."""
        if not os.path.exists(path):
            return False
        if not os.path.isdir(os.path.join(path, ".svn")):
            return False
        self.working_copy_path = path
        return True

    def check_svn_available(self) -> bool:
        """Check if SVN command is available."""
        try:
            result = subprocess.run(
                [self.svn_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_externals(self) -> List[Dict]:
        """
        Get all SVN externals from the working copy.
        Returns a list of external definitions with their properties.
        """
        externals = []

        try:
            # Get all directories with svn:externals property
            result = subprocess.run(
                [self.svn_command, "propget", "svn:externals", "-R", self.working_copy_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_copy_path
            )

            if result.returncode != 0:
                return []

            # Parse the output
            current_path = None
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                # Line format: "path - external_definition"
                # or just "external_definition" if continuing from previous
                if ' - ' in line:
                    parts = line.split(' - ', 1)
                    current_path = parts[0].strip()
                    external_def = parts[1].strip() if len(parts) > 1 else ""
                else:
                    external_def = line.strip()

                if external_def and current_path:
                    # Parse external definition
                    # Format can be:
                    # local_path [-r REV] URL
                    # or
                    # [-r REV] URL local_path
                    external_info = self._parse_external_definition(external_def, current_path)
                    if external_info:
                        externals.append(external_info)

            # Get status for each external
            for external in externals:
                external['status'] = self._get_external_status(external)

        except subprocess.SubprocessError as e:
            print(f"Error getting externals: {e}")

        return externals

    def _parse_external_definition(self, definition: str, parent_path: str) -> Optional[Dict]:
        """Parse an SVN external definition string with support for spaces and quoted paths."""
        try:
            # Use shlex to properly handle quoted strings
            # This preserves quoted paths and URLs with spaces
            parts = shlex.split(definition)
        except ValueError:
            # If shlex fails (e.g., unmatched quotes), fall back to simple split
            # but preserve %20 and other URL encoding
            parts = definition.split()

        if len(parts) < 2:
            return None

        revision = None
        url = None
        local_path = None

        # Check for -r or -rREV flag
        i = 0
        while i < len(parts):
            part = parts[i]
            if part == '-r' and i + 1 < len(parts):
                revision = parts[i + 1]
                i += 2
            elif part.startswith('-r'):
                revision = part[2:]
                i += 1
            else:
                # First non-revision part
                if url is None:
                    # Could be URL or local_path
                    # Check if it looks like a URL
                    if (part.startswith('http://') or part.startswith('https://') or
                        part.startswith('svn://') or part.startswith('svn+ssh://') or
                        part.startswith('file://') or part.startswith('^/')):
                        url = part
                        # Next part is local_path if exists
                        if i + 1 < len(parts):
                            local_path = parts[i + 1]
                            i += 2
                        else:
                            # No local path specified, will derive from URL
                            i += 1
                    else:
                        # Old format: local_path [-r REV] URL
                        local_path = part
                        if i + 1 < len(parts):
                            url = parts[i + 1]
                            i += 2
                        else:
                            i += 1
                else:
                    i += 1

        if not url:
            return None

        # If no local_path found, use last component of URL
        if not local_path:
            # Decode %20 and other URL encoding for the local path
            decoded_url = urllib.parse.unquote(url)
            local_path = decoded_url.rstrip('/').split('/')[-1]

        # Decode URL-encoded spaces in local_path if present
        local_path = urllib.parse.unquote(local_path)

        full_path = os.path.join(parent_path, local_path) if parent_path != '.' else local_path

        return {
            'name': local_path,
            'path': full_path,
            'url': url,
            'revision': revision or 'HEAD',
            'parent_path': parent_path,
            'status': 'unknown'
        }

    def _get_external_status(self, external: Dict) -> str:
        """Get the status of an external (up-to-date, modified, etc.)."""
        try:
            full_path = os.path.join(self.working_copy_path, external['path'])

            # Check if path exists
            if not os.path.exists(full_path):
                return 'missing'

            # Get SVN status
            result = subprocess.run(
                [self.svn_command, "status", full_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.working_copy_path
            )

            if result.stdout.strip():
                return 'modified'

            return 'clean'

        except subprocess.SubprocessError:
            return 'error'

    def get_changed_externals(self) -> List[Dict]:
        """
        Detect externals with pending changes by checking svn:externals property modifications.
        """
        changed = []

        try:
            # Check for property changes
            result = subprocess.run(
                [self.svn_command, "diff", "--properties-only", self.working_copy_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_copy_path
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse diff output to find changed externals
                # This is a simplified version - real implementation would need more robust parsing
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'svn:externals' in line:
                        # Found a change in externals property
                        # Try to extract the details
                        path_match = re.search(r'Index: (.+)', '\n'.join(lines[max(0, i-5):i]))
                        if path_match:
                            changed.append({
                                'path': path_match.group(1),
                                'has_changes': True
                            })

        except subprocess.SubprocessError as e:
            print(f"Error checking for changed externals: {e}")

        return changed

    def get_log(self, url: str, old_rev: str, new_rev: str, format_type: str = 'xml') -> Optional[str]:
        """
        Get SVN log between two revisions for a given URL.

        Args:
            url: SVN URL
            old_rev: Starting revision
            new_rev: Ending revision
            format_type: Output format ('xml', 'text')

        Returns:
            Log output as string or None if error
        """
        try:
            # Handle HEAD revision
            if new_rev.upper() == 'HEAD':
                new_rev = 'HEAD'
            if old_rev.upper() == 'HEAD':
                old_rev = 'HEAD'

            cmd = [self.svn_command, "log", f"-r{old_rev}:{new_rev}", url]
            if format_type == 'xml':
                cmd.append('--xml')

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return None

            return result.stdout

        except subprocess.SubprocessError as e:
            print(f"Error getting log: {e}")
            return None

    def parse_log_xml(self, xml_string: str) -> List[Dict]:
        """Parse SVN log XML output into structured data."""
        try:
            root = ET.fromstring(xml_string)
            logs = []

            for logentry in root.findall('logentry'):
                revision = logentry.get('revision')
                author = logentry.findtext('author', 'unknown')
                date_str = logentry.findtext('date', '')
                msg = logentry.findtext('msg', '')

                # Parse date
                date_formatted = ''
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        date_formatted = date_str

                logs.append({
                    'revision': revision,
                    'author': author,
                    'date': date_formatted,
                    'message': msg.strip()
                })

            return logs

        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return []

    def format_changelog(self, logs: List[Dict], format_type: str = 'plain') -> str:
        """
        Format changelog in various formats.

        Args:
            logs: List of log entries
            format_type: 'plain', 'markdown', or 'commit'

        Returns:
            Formatted changelog string
        """
        if not logs:
            return "No changes found."

        if format_type == 'markdown':
            output = "# Changelog\n\n"
            for log in logs:
                output += f"## r{log['revision']} - {log['author']} - {log['date']}\n\n"
                output += f"{log['message']}\n\n"
                output += "---\n\n"
            return output

        elif format_type == 'commit':
            output = "Changes:\n"
            for log in logs:
                output += f"- r{log['revision']}: {log['message'].split(chr(10))[0]}\n"
            return output

        else:  # plain
            output = ""
            for log in logs:
                output += f"Revision: {log['revision']}\n"
                output += f"Author: {log['author']}\n"
                output += f"Date: {log['date']}\n"
                output += f"Message:\n{log['message']}\n"
                output += "-" * 70 + "\n\n"
            return output

    def get_working_copy_info(self) -> Dict:
        """Get information about the current working copy."""
        try:
            result = subprocess.run(
                [self.svn_command, "info", self.working_copy_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.working_copy_path
            )

            if result.returncode != 0:
                return {'error': 'Not a valid SVN working copy'}

            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            return info

        except subprocess.SubprocessError as e:
            return {'error': str(e)}
