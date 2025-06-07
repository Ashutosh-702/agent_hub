#!/usr/bin/env python3
"""
Desktop Shortcut Creator for SDR Workflow GUI

Creates platform-specific shortcuts for easy access to the GUI application.
"""

import os
import sys
import platform
from pathlib import Path

def create_windows_shortcut():
    """Create Windows .bat file and desktop shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "SDR Workflow.lnk")
        target = sys.executable
        wDir = os.path.dirname(os.path.abspath(__file__))
        arguments = os.path.join(wDir, "run_gui.py")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = target
        shortcut.save()
        
        print(f"✅ Windows shortcut created: {path}")
        return True
    except ImportError:
        print("❌ Windows shortcut creation requires pywin32 and winshell")
        print("Install with: pip install pywin32 winshell")
        return False
    except Exception as e:
        print(f"❌ Error creating Windows shortcut: {e}")
        return False

def create_macos_app():
    """Create macOS .app bundle"""
    try:
        app_name = "SDR Workflow"
        app_path = f"{app_name}.app"
        
        # Create app bundle structure
        os.makedirs(f"{app_path}/Contents/MacOS", exist_ok=True)
        os.makedirs(f"{app_path}/Contents/Resources", exist_ok=True)
        
        # Create Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>sdr_workflow</string>
    <key>CFBundleIdentifier</key>
    <string>com.sdrtools.workflow</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>SDRT</string>
</dict>
</plist>"""
        
        with open(f"{app_path}/Contents/Info.plist", "w") as f:
            f.write(info_plist)
        
        # Create executable script
        script_path = f"{app_path}/Contents/MacOS/sdr_workflow"
        script_content = f"""#!/bin/bash
cd "{os.path.dirname(os.path.abspath(__file__))}/../../.."
{sys.executable} run_gui.py
"""
        
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ macOS app bundle created: {app_path}")
        print(f"💡 You can now drag {app_path} to your Applications folder")
        return True
        
    except Exception as e:
        print(f"❌ Error creating macOS app: {e}")
        return False

def create_linux_desktop():
    """Create Linux .desktop file"""
    try:
        desktop_file = """[Desktop Entry]
Version=1.0
Type=Application
Name=SDR Workflow
Comment=Advanced GUI for SDR Workflow
Exec={python} {script}
Icon={icon}
Path={path}
Terminal=false
Categories=Office;Productivity;
"""
        
        script_path = os.path.abspath("run_gui.py")
        work_dir = os.path.dirname(script_path)
        
        desktop_content = desktop_file.format(
            python=sys.executable,
            script=script_path,
            icon=os.path.join(work_dir, "icon.png"),  # You can add an icon file
            path=work_dir
        )
        
        # Save to desktop
        desktop_dir = os.path.expanduser("~/Desktop")
        if os.path.exists(desktop_dir):
            desktop_file_path = os.path.join(desktop_dir, "SDR_Workflow.desktop")
            with open(desktop_file_path, "w") as f:
                f.write(desktop_content)
            os.chmod(desktop_file_path, 0o755)
            print(f"✅ Linux desktop file created: {desktop_file_path}")
        
        # Also save to applications
        apps_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(apps_dir, exist_ok=True)
        apps_file_path = os.path.join(apps_dir, "sdr-workflow.desktop")
        with open(apps_file_path, "w") as f:
            f.write(desktop_content)
        
        print(f"✅ Linux application entry created: {apps_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Linux desktop file: {e}")
        return False

def create_launch_script():
    """Create a simple launch script for any platform"""
    try:
        if platform.system() == "Windows":
            script_name = "launch_sdr_gui.bat"
            script_content = f"""@echo off
cd /d "{os.path.dirname(os.path.abspath(__file__))}"
"{sys.executable}" run_gui.py
pause
"""
        else:
            script_name = "launch_sdr_gui.sh"
            script_content = f"""#!/bin/bash
cd "{os.path.dirname(os.path.abspath(__file__))}"
{sys.executable} run_gui.py
"""
        
        with open(script_name, "w") as f:
            f.write(script_content)
        
        if platform.system() != "Windows":
            os.chmod(script_name, 0o755)
        
        print(f"✅ Launch script created: {script_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating launch script: {e}")
        return False

def main():
    """Create platform-appropriate shortcuts"""
    print("🚀 SDR Workflow GUI - Desktop Shortcut Creator")
    print("=" * 50)
    
    system = platform.system()
    print(f"Detected platform: {system}")
    print()
    
    success = False
    
    if system == "Darwin":  # macOS
        print("Creating macOS app bundle...")
        success = create_macos_app()
    elif system == "Windows":
        print("Creating Windows shortcut...")
        success = create_windows_shortcut()
    elif system == "Linux":
        print("Creating Linux desktop file...")
        success = create_linux_desktop()
    else:
        print(f"Unknown platform: {system}")
    
    # Always create a simple launch script as fallback
    print("\nCreating universal launch script...")
    script_success = create_launch_script()
    
    print("\n" + "=" * 50)
    if success or script_success:
        print("✅ Shortcut creation completed!")
        print("\n📋 Available ways to launch the GUI:")
        print("   1. Double-click the created shortcut/app")
        print("   2. Run: python run_gui.py")
        print("   3. Run: python sdr_gui.py")
        if script_success:
            script_name = "launch_sdr_gui.bat" if system == "Windows" else "launch_sdr_gui.sh"
            print(f"   4. Double-click: {script_name}")
    else:
        print("❌ Shortcut creation failed, but you can still run:")
        print("   python run_gui.py")

if __name__ == "__main__":
    main() 