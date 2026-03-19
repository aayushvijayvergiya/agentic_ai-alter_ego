#!/usr/bin/env python3
"""Deployment preparation script for Hugging Face Spaces."""

import os
import sys
from pathlib import Path


def check_files():
    """Check if all required files exist for deployment."""
    required_files = [
        "app.py",
        "requirements.txt", 
        "README.md",
        "src/alter_ego/__init__.py",
        "static/summary.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✅ All required files present")
    return True


def check_env_vars():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables (required for deployment):")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nYou'll need to set these in your Hugging Face Space settings.")
    else:
        print("✅ Required environment variables are set")
    
    return len(missing_vars) == 0


def main():
    """Main deployment check function."""
    print("🚀 Hugging Face Deployment Preparation Check")
    print("=" * 50)
    
    files_ok = check_files()
    env_ok = check_env_vars()
    
    print("\n📋 Deployment Checklist:")
    print("=" * 30)
    
    if files_ok:
        print("✅ Files: Ready")
    else:
        print("❌ Files: Missing files")
    
    if env_ok:
        print("✅ Environment: Configured")
    else:
        print("⚠️  Environment: Need to set vars in HF Space")
    
    print("\n🎯 Next Steps:")
    print("1. Run: uv run gradio deploy")
    print("2. Set OPENAI_API_KEY in your Hugging Face Space settings")
    print("3. (Optional) Set PUSHOVER_USER and PUSHOVER_TOKEN for notifications")
    
    if files_ok:
        print("\n✅ Ready for deployment!")
        return 0
    else:
        print("\n❌ Fix missing files before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())