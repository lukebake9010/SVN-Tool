"""
SVN Manager Module
Handles all SVN operations including listing externals, detecting changes, and fetching logs.
"""

import subprocess
import re
import os
import shlex
import urllib.parse
import posixpath
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
            # Get working (current) externals
            working_externals = self._get_externals_from_propget(self.working_copy_path, pristine=False)

            # Get pristine (BASE) externals for comparison
            base_externals = self._get_externals_from_propget(self.working_copy_path, pristine=True)

            # Create a lookup for base externals by parent_path + name
            base_lookup = {}
            for ext in base_externals:
                key = f"{ext['parent_path']}:{ext['name']}"
                base_lookup[key] = ext

            # Process working externals and detect changes
            for external in working_externals:
                key = f"{external['parent_path']}:{external['name']}"
                base_external = base_lookup.get(key)

                # Determine status based on definition changes
                external['status'], external['change_details'] = self._get_external_status(external, base_external)
                externals.append(external)

        except subprocess.SubprocessError as e:
            print(f"Error getting externals: {e}")

        return externals

    def _get_externals_from_propget(self, path: str, pristine: bool = False) -> List[Dict]:
        """
        Get externals from svn propget command.

        Args:
            path: Path to query
            pristine: If True, get BASE (pristine) version, otherwise get working version

        Returns:
            List of external definitions
        """
        externals = []
        cmd = [self.svn_command, "propget", "svn:externals", "-R", path]

        # Add -r BASE to get pristine version
        if pristine:
            cmd.extend(["-r", "BASE"])

        try:
            result = subprocess.run(
                cmd,
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
                    external_info = self._parse_external_definition(external_def, current_path)
                    if external_info:
                        externals.append(external_info)

        except subprocess.SubprocessError as e:
            print(f"Error getting externals from propget: {e}")

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

        if len(parts) < 1:
            return None

        revision = None
        url = None
        local_path = None

        # First pass: extract revision flags and collect non-revision parts
        non_revision_parts = []
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
                non_revision_parts.append(part)
                i += 1

        # Second pass: determine URL and local_path from non-revision parts
        if len(non_revision_parts) == 0:
            return None
        elif len(non_revision_parts) == 1:
            # Only one part, must be URL
            url = non_revision_parts[0]
        else:
            # Two or more parts: determine which is URL and which is local_path
            # Check if first part looks like a URL
            first_is_url = (non_revision_parts[0].startswith('http://') or
                           non_revision_parts[0].startswith('https://') or
                           non_revision_parts[0].startswith('svn://') or
                           non_revision_parts[0].startswith('svn+ssh://') or
                           non_revision_parts[0].startswith('file://') or
                           non_revision_parts[0].startswith('^/'))

            if first_is_url:
                # New format: [-r REV] URL local_path
                url = non_revision_parts[0]
                local_path = non_revision_parts[1] if len(non_revision_parts) > 1 else None
            else:
                # Old format: local_path [-r REV] URL
                local_path = non_revision_parts[0]
                url = non_revision_parts[1] if len(non_revision_parts) > 1 else None

        if not url:
            return None

        # Check for peg revision format (URL@REV)
        # This takes precedence over -r flag if both are present
        if '@' in url:
            # Split URL and peg revision
            parts = url.rsplit('@', 1)
            if len(parts) == 2 and parts[1].isdigit():
                url = parts[0]
                revision = parts[1]

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

    def _get_external_status(self, working_external: Dict, base_external: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """
        Get the status of an external by comparing working vs BASE definition.

        Args:
            working_external: The current (working) external definition
            base_external: The pristine (BASE) external definition, or None if newly added

        Returns:
            Tuple of (status, change_details)
            status: 'changed', 'new', 'clean', 'missing', or 'error'
            change_details: Dict with old/new values if changed, None otherwise
        """
        try:
            full_path = os.path.join(self.working_copy_path, working_external['path'])

            # Check if external is newly added (not in BASE)
            if base_external is None:
                # Check if the directory exists
                if not os.path.exists(full_path):
                    return 'missing', None
                return 'new', {
                    'type': 'added',
                    'message': 'External definition added'
                }

            # Compare working vs base definitions
            changes = {}
            has_changes = False

            # Check revision change
            if working_external['revision'] != base_external['revision']:
                changes['revision'] = {
                    'old': base_external['revision'],
                    'new': working_external['revision']
                }
                has_changes = True

            # Check URL change
            if working_external['url'] != base_external['url']:
                changes['url'] = {
                    'old': base_external['url'],
                    'new': working_external['url']
                }
                has_changes = True

            # Check path change (though this is unlikely as we match by path)
            if working_external['path'] != base_external['path']:
                changes['path'] = {
                    'old': base_external['path'],
                    'new': working_external['path']
                }
                has_changes = True

            if has_changes:
                return 'changed', changes

            # No changes detected in definition
            # Check if path exists
            if not os.path.exists(full_path):
                return 'missing', None

            return 'clean', None

        except Exception as e:
            print(f"Error getting external status: {e}")
            return 'error', None

    def get_changed_externals(self) -> List[Dict]:
        """
        Get list of externals that have been modified (definition changes).
        Returns externals with 'changed' or 'new' status.
        """
        all_externals = self.get_externals()

        # Filter to only those with changed or new status
        changed = [
            ext for ext in all_externals
            if ext['status'] in ['changed', 'new']
        ]

        return changed

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by resolving '..' and '.' path elements.
        SVN does not accept URLs with '..' elements, so we need to resolve them.

        Args:
            url: The URL to normalize

        Returns:
            Normalized URL with '..' elements resolved
        """
        try:
            # Parse the URL
            parsed = urllib.parse.urlparse(url)

            # Normalize the path using posixpath (URLs always use forward slashes)
            # posixpath.normpath will resolve '..' and '.' elements
            normalized_path = posixpath.normpath(parsed.path)

            # Reconstruct the URL with the normalized path
            normalized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                normalized_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            return normalized
        except Exception as e:
            print(f"Error normalizing URL: {e}")
            # If normalization fails, return the original URL
            return url

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

            # Normalize URL to resolve '..' elements that SVN doesn't accept
            normalized_url = self._normalize_url(url)
            if normalized_url != url:
                print(f"Normalized URL: {url} -> {normalized_url}")

            cmd = [self.svn_command, "log", f"-r{old_rev}:{new_rev}", normalized_url]
            if format_type == 'xml':
                cmd.append('--xml')

            print(f"Executing SVN log command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_copy_path
            )

            if result.returncode != 0:
                print(f"SVN log command failed with code {result.returncode}")
                print(f"stderr: {result.stderr}")
                print(f"stdout: {result.stdout}")
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
