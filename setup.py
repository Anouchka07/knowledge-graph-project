#!/usr/bin/env python3
"""
Setup script for Knowledge Graph Generator
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False
    return True

def check_api_key():
    """Check if Gemini API key is set."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️  GEMINI_API_KEY environment variable is not set.")
        print("Please set it using:")
        print("  PowerShell: $env:GEMINI_API_KEY = 'your_api_key_here'")
        print("  Command Prompt: set GEMINI_API_KEY=your_api_key_here")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    else:
        print("✅ GEMINI_API_KEY is set!")
        return True

def main():
    print("🚀 Setting up Knowledge Graph Generator...")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        return
    
    print("\n" + "=" * 50)
    
    # Check API key
    api_key_set = check_api_key()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    
    if api_key_set:
        print("You can now run: python main.py")
    else:
        print("Please set your GEMINI_API_KEY before running the script.")

if __name__ == "__main__":
    main()
