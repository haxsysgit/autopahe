#!/usr/bin/env python3
"""
AutoPahe Installation Script
Automated setup for AutoPahe anime downloader with Playwright browser support.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and handle errors gracefully."""
    print(f"🔧 {description}...")
    print(f"   Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("   Please ensure you have the required package manager installed.")
        return False


def check_uv_available():
    """Check if UV package manager is available."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    """Main setup function."""
    print("🎬 AutoPahe Installation Script")
    print("=" * 50)
    print("This script will set up AutoPahe with all required dependencies.")
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Choose installation method
    use_uv = check_uv_available()
    
    if use_uv:
        print("✅ UV package manager found - using UV for installation")
        success = run_command(
            ["uv", "sync"],
            "Installing dependencies with UV"
        )
        if success:
            success = run_command(
                ["uv", "run", "playwright", "install", "chromium"],
                "Installing Playwright browsers"
            )
    else:
        print("⚠️  UV not found - using pip for installation")
        print("   Consider installing UV for faster dependency management:")
        print("   https://docs.astral.sh/uv/getting-started/installation/")
        print()
        
        # Try pip with --user flag if system installation fails
        success = run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Installing dependencies with pip"
        )
        
        if not success:
            print("🔄 Trying user-level installation...")
            success = run_command(
                [sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"],
                "Installing dependencies with pip (user-level)"
            )
        
        if success:
            success = run_command(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                "Installing Playwright browsers"
            )
    
    print()
    if success:
        print("🎉 Installation completed successfully!")
        print()
        print("📋 NEXT STEPS:")
        print("   • Run 'autopahe' to start using the application")
        print("   • Or use 'uv run autopahe' if you installed with UV")
        print("   • Check README.md for usage instructions")
        print()
        print("💡 TIPS:")
        print("   • If you encounter issues, set AUTOPAHE_SKIP_AUTO_INSTALL=1")
        print("   • For help: https://github.com/haxsysgit/autopahe/issues")
    else:
        print("❌ Installation failed. Please check the error messages above.")
        print()
        print("📋 MANUAL SETUP:")
        print("   1. Install dependencies:")
        if use_uv:
            print("      uv sync")
        else:
            print("      pip install -r requirements.txt")
        print("   2. Install Playwright browsers:")
        print("      playwright install chromium")
        print()
        print("For additional help, visit:")
        print("   https://github.com/haxsysgit/autopahe/issues")


if __name__ == "__main__":
    main()
