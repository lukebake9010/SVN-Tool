#!/usr/bin/env python3
"""
Test script to verify external change detection functionality.
This demonstrates how the tool detects changes to external definitions.
"""

from svn_manager import SVNManager
import json

def test_external_detection():
    """Test external definition change detection."""
    print("=" * 70)
    print("SVN External Change Detection Test")
    print("=" * 70)
    print()

    # Initialize SVN manager with current directory
    manager = SVNManager(".")

    # Check if SVN is available
    if not manager.check_svn_available():
        print("❌ SVN is not available. Please install Subversion.")
        return

    print("✓ SVN is available")
    print()

    # Get all externals
    print("Fetching externals...")
    externals = manager.get_externals()

    if not externals:
        print("No externals found in the current working copy.")
        print()
        print("To test this functionality:")
        print("1. Modify an external's revision in the svn:externals property")
        print("2. Run this script again")
        print()
        print("Example:")
        print("  svn propset svn:externals '-r1234 https://example.com/repo external_dir' .")
        return

    print(f"Found {len(externals)} external(s)")
    print()

    # Display all externals with their status
    for ext in externals:
        print(f"External: {ext['name']}")
        print(f"  Path:     {ext['path']}")
        print(f"  URL:      {ext['url']}")
        print(f"  Revision: {ext['revision']}")
        print(f"  Status:   {ext['status']}")

        # Show change details if present
        if ext.get('change_details'):
            print(f"  Changes:")
            details = ext['change_details']
            if 'revision' in details:
                print(f"    - Revision: {details['revision']['old']} → {details['revision']['new']}")
            if 'url' in details:
                print(f"    - URL: {details['url']['old']} → {details['url']['new']}")
            if 'path' in details:
                print(f"    - Path: {details['path']['old']} → {details['path']['new']}")
        print()

    # Get changed externals
    print("-" * 70)
    changed = manager.get_changed_externals()

    if changed:
        print(f"✓ Found {len(changed)} external(s) with definition changes:")
        print()
        for ext in changed:
            print(f"  - {ext['name']} ({ext['status']})")
            if ext.get('change_details'):
                details = ext['change_details']
                if 'revision' in details:
                    print(f"    Revision changed: {details['revision']['old']} → {details['revision']['new']}")
    else:
        print("✓ No external definition changes detected")
        print()
        print("All externals are clean (no pending changes to external definitions)")

    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == '__main__':
    test_external_detection()
