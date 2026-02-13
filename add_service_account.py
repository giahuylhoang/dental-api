#!/usr/bin/env python3
"""
Helper script to add GOOGLE_SERVICE_ACCOUNT_JSON to .env.local file.

Usage:
    python add_service_account.py
    
    Then paste your service account JSON when prompted.
"""

import json
import os
from pathlib import Path

def load_service_account_from_file():
    """Load service account JSON from a file."""
    print("📁 Load from file")
    print("   Enter the path to your service account JSON file:")
    file_path = input("   Path: ").strip().strip('"').strip("'")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return json.dumps(data, separators=(',', ':'))
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def get_service_account_from_input():
    """Get service account JSON from user input."""
    print("\n📝 Paste your service account JSON")
    print("   (You can paste it as multi-line JSON, it will be converted)")
    print("   Press Enter, then paste JSON, then press Ctrl+D (Mac/Linux) or Ctrl+Z+Enter (Windows)")
    print("   Or type 'file' to load from a file")
    print()
    
    lines = []
    try:
        while True:
            line = input()
            if line.lower().strip() == 'file':
                return load_service_account_from_file()
            lines.append(line)
    except EOFError:
        pass
    
    json_str = '\n'.join(lines)
    
    # Validate JSON
    try:
        data = json.loads(json_str)
        # Convert to compact single-line format
        return json.dumps(data, separators=(',', ':'))
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None

def add_to_env_file(sa_json):
    """Add GOOGLE_SERVICE_ACCOUNT_JSON to .env.local file."""
    env_file = Path('.env.local')
    
    # Read existing content
    existing_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            existing_content = f.read()
    
    # Check if already exists
    if 'GOOGLE_SERVICE_ACCOUNT_JSON' in existing_content:
        print("\n⚠️  GOOGLE_SERVICE_ACCOUNT_JSON already exists in .env.local")
        response = input("   Replace it? (y/n): ").strip().lower()
        if response != 'y':
            print("   Cancelled.")
            return False
        
        # Remove old entry
        lines = existing_content.split('\n')
        new_lines = []
        skip_next = False
        for line in lines:
            if line.startswith('GOOGLE_SERVICE_ACCOUNT_JSON='):
                skip_next = True
                continue
            if skip_next and line.strip() == '':
                skip_next = False
                continue
            new_lines.append(line)
        existing_content = '\n'.join(new_lines)
    
    # Add new entry
    new_entry = f"\nGOOGLE_SERVICE_ACCOUNT_JSON='{sa_json}'\n"
    
    # Write to file
    with open(env_file, 'w') as f:
        f.write(existing_content.rstrip() + new_entry)
    
    print(f"\n✅ Added GOOGLE_SERVICE_ACCOUNT_JSON to {env_file}")
    return True

def main():
    """Main function."""
    print("=" * 60)
    print("Add Google Service Account JSON to .env.local")
    print("=" * 60)
    print()
    
    # Get service account JSON
    sa_json = get_service_account_from_input()
    
    if not sa_json:
        print("\n❌ Failed to get service account JSON")
        return 1
    
    # Validate it's a service account
    try:
        data = json.loads(sa_json)
        if data.get('type') != 'service_account':
            print("⚠️  Warning: JSON doesn't appear to be a service account")
            print(f"   Found type: {data.get('type')}")
            response = input("   Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return 1
    except:
        pass
    
    # Add to .env.local
    if add_to_env_file(sa_json):
        print("\n✅ Success! You can now test with:")
        print("   python test_google_service_account.py")
        return 0
    else:
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
