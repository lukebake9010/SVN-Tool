#!/usr/bin/env python3
"""
Debug script to test external parsing with various formats.
"""

from svn_manager import SVNManager
import sys

# Test cases for different external definition formats
test_cases = [
    # Old format: local_path -r REV URL
    ("vendor/lib -r12345 https://example.com/repo/trunk", "."),

    # New format: -r REV URL local_path
    ("-r12345 https://example.com/repo/trunk vendor/lib", "."),

    # Without explicit revision (should be HEAD)
    ("https://example.com/repo/trunk vendor/lib", "."),

    # With spaces in path (quoted)
    ('"-r12345 https://example.com/repo/trunk vendor/my lib"', "."),

    # With -rREV (no space)
    ("-r12345 https://example.com/repo/trunk vendor/lib", "."),
    ("vendor/lib -r12345 https://example.com/repo/trunk", "."),
]

def test_parsing():
    """Test external definition parsing."""
    manager = SVNManager(".")

    print("=" * 70)
    print("External Definition Parsing Test")
    print("=" * 70)
    print()

    for i, (definition, parent_path) in enumerate(test_cases, 1):
        print(f"Test {i}: {definition}")
        result = manager._parse_external_definition(definition, parent_path)

        if result:
            print(f"  ✓ Parsed successfully:")
            print(f"    Name:     {result['name']}")
            print(f"    Path:     {result['path']}")
            print(f"    URL:      {result['url']}")
            print(f"    Revision: {result['revision']}")
        else:
            print(f"  ✗ Failed to parse")
        print()

    print("=" * 70)
    print()

    # If we're in an actual SVN working copy, try to get real externals
    print("Attempting to fetch real externals from current directory...")
    print()

    if manager.check_svn_available():
        externals = manager.get_externals()
        if externals:
            print(f"Found {len(externals)} external(s):")
            print()
            for ext in externals:
                print(f"External: {ext['name']}")
                print(f"  URL:      {ext['url']}")
                print(f"  Revision: {ext['revision']}")
                print(f"  Status:   {ext['status']}")
                if ext.get('change_details'):
                    print(f"  Changes:  {ext['change_details']}")
                print()
        else:
            print("No externals found or not in SVN working copy")
    else:
        print("SVN not available")

if __name__ == '__main__':
    test_parsing()
