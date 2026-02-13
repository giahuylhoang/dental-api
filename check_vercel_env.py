#!/usr/bin/env python3
"""
Check if GOOGLE_SERVICE_ACCOUNT_JSON is set in Vercel.

This helps debug why calendar service isn't working in production.
"""

import subprocess
import sys
import json

def check_vercel_env():
    """Check Vercel environment variables."""
    print("🔍 Checking Vercel environment variables...\n")
    
    try:
        # Try to pull environment variables
        result = subprocess.run(
            ["vercel", "env", "pull", ".env.vercel", "--yes"],
            capture_output=True,
            text=True,
            cwd="dental-api"
        )
        
        if result.returncode == 0:
            print("✅ Successfully pulled Vercel environment variables\n")
            
            # Check the file
            from pathlib import Path
            env_file = Path("dental-api/.env.vercel")
            
            if env_file.exists():
                from dotenv import load_dotenv
                import os
                load_dotenv(env_file)
                
                sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
                
                if sa_json:
                    print("✅ GOOGLE_SERVICE_ACCOUNT_JSON found in Vercel!")
                    print(f"   Length: {len(sa_json)} characters\n")
                    
                    # Try to parse it
                    try:
                        sa_data = json.loads(sa_json)
                        email = sa_data.get('client_email', 'NOT FOUND')
                        project_id = sa_data.get('project_id', 'NOT FOUND')
                        
                        print("✅ JSON is valid!")
                        print(f"   Service Account Email: {email}")
                        print(f"   Project ID: {project_id}\n")
                        
                        return True
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON is invalid: {e}\n")
                        return False
                else:
                    print("❌ GOOGLE_SERVICE_ACCOUNT_JSON NOT found in Vercel!\n")
                    print("📝 To fix this:")
                    print("   1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables")
                    print("   2. Add GOOGLE_SERVICE_ACCOUNT_JSON")
                    print("   3. Paste your service account JSON (single line)")
                    print("   4. Select 'Production' environment")
                    print("   5. Redeploy your application")
                    return False
            else:
                print("⚠️  .env.vercel file not created")
                return False
        else:
            print("❌ Failed to pull Vercel environment variables")
            print(f"   Error: {result.stderr}\n")
            print("💡 Make sure you're logged in to Vercel:")
            print("   vercel login")
            return False
            
    except FileNotFoundError:
        print("❌ Vercel CLI not found")
        print("\nInstall it with:")
        print("   npm install -g vercel")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("Vercel Environment Variable Check")
    print("=" * 60)
    print()
    
    success = check_vercel_env()
    
    if not success:
        print("\n📋 Manual Check:")
        print("   1. Go to: https://vercel.com/dashboard")
        print("   2. Select your project: dental-api-ochre")
        print("   3. Go to Settings → Environment Variables")
        print("   4. Look for GOOGLE_SERVICE_ACCOUNT_JSON")
        print("   5. If missing, add it with your service account JSON")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
