#!/usr/bin/env python3
"""
SDR Workflow GUI Launcher

Simple launcher script for the SDR workflow GUI application.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sdr_gui import main
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error launching GUI: {e}")
    sys.exit(1) 