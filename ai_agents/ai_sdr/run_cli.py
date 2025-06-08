#!/usr/bin/env python3
"""
SDR CLI Application Launcher

Simple launcher script for the SDR CLI application.
"""

import sys
import os
from pathlib import Path

# Get the script directory and add to Python path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent  # agent_hub root
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(script_dir))

# Change to the SDR directory for relative imports
os.chdir(script_dir)

try:
    from cli_app import main
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)
except Exception as e:
    print(f"Error launching CLI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)