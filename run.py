#!/usr/bin/env python3
"""
Quick launcher for the Crypto Backtesting System
Automatically installs dependencies if needed
"""

import subprocess
import sys
import os

def check_and_install_packages():
    """Check and install required packages"""
    print("🔧 Checking dependencies...")
    
    required = [
        'backtrader',
        'pandas',
        'numpy',
        'ccxt',
        'matplotlib',
        'requests',
        'python-dateutil'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n📦 Installing missing packages: {', '.join(missing)}")
        print("This may take a minute on first run...\n")
        
        for package in missing:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        
        print("\n✅ All packages installed!")
    else:
        print("✅ All dependencies ready!")
    
    return True

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║        CRYPTO BACKTESTING SYSTEM PRO v3.0            ║
    ║                                                        ║
    ║         Professional Trading Strategy Tester          ║
    ║              With Leverage & Risk Management          ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_and_install_packages():
        print("❌ Failed to install dependencies")
        input("Press Enter to exit...")
        return
    
    # Launch the main application
    print("\n🚀 Launching backtesting system...\n")
    
    try:
        subprocess.run([sys.executable, 'backtest_pro.py'])
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
