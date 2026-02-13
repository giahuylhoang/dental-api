#!/usr/bin/env python3
"""
Get service account email from various sources.

This script helps you find the service account email address that you need
to share your Google Calendar with.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_env_file(file_path):
    """Check if service account JSON exists in an env file."""
    if not Path(file_path).exists():
        return None
    
    load_dotenv(file_path)
    sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if sa_json:
        try:
            sa_data = json.loads(sa_json)
            return sa_data.get('client_email')
        except:
            return None
    return None

def check_json_file(file_path):
    """Check if service account JSON exists as a file."""
    if not Path(file_path).exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            sa_data = json.load(f)
            return sa_data.get('client_email')
    except:
        return None

def main():
    """Find service account email from various sources."""
    print("🔍 Looking for service account email...\n")
    
    # Check various locations
    locations = [
        ("dental-api/.env.local", check_env_file),
        ("dental-api/.env", check_env_file),
        (".env.local", check_env_file),
        (".env", check_env_file),
        ("service-account.json", check_json_file),
        ("service_account.json", check_json_file),
        ("google-service-account.json", check_json_file),
        ("dental-api/service-account.json", check_json_file),
        ("dental-api/service_account.json", check_json_file),
    ]
    
    found_email = None
    found_location = None
    
    for location, check_func in locations:
        email = check_func(location)
        if email:
            found_email = email
            found_location = location
            break
    
    if found_email:
        print(f"✅ Found service account email!")
        print(f"   Location: {found_location}")
        print(f"   Email: {found_email}\n")
        print("📋 Next steps:")
        print("   1. Copy this email address")
        print("   2. Open Google Calendar: https://calendar.google.com/")
        print("   3. Go to Settings → Settings for my calendars")
        print("   4. Select your calendar")
        print("   5. Share with specific people → Add this email")
        print("   6. Give it 'Make changes to events' permission")
        print("   7. Click Send")
        return 0
    else:
        print("❌ Service account email not found in common locations.\n")
        print("📝 Options to find it:")
        print("\n1. If you have the JSON file downloaded:")
        print("   python3 get_service_account_email.py")
        print("   # Then paste the file path when prompted")
        
        print("\n2. Check Vercel environment variables:")
        print("   vercel env pull dental-api/.env.local")
        print("   python3 get_service_account_email.py")
        
        print("\n3. If you have the JSON file, provide the path:")
        file_path = input("\n   Enter path to service account JSON file (or press Enter to skip): ").strip()
        
        if file_path:
            email = check_json_file(file_path)
            if email:
                print(f"\n✅ Found email: {email}")
                print("\n📋 Share your calendar with this email address!")
                return 0
            else:
                print(f"\n❌ Could not read email from {file_path}")
                return 1
        
        print("\n💡 Tip: The service account email looks like:")
        print("   your-service-account@your-project-id.iam.gserviceaccount.com")
        return 1

if __name__ == "__main__":
    sys.exit(main())
