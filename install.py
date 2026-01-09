"""Install Claude Pulse to run on Windows startup (without building exe)."""

import os
import sys
import winreg
import shutil
from pathlib import Path

APP_NAME = "Claude Pulse"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_pythonw_path():
    """Get path to pythonw.exe (no console window)."""
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, 'pythonw.exe')
    if os.path.exists(pythonw):
        return pythonw
    return sys.executable


def add_to_startup_registry():
    """Add Claude Pulse to Windows startup via registry."""
    pythonw = get_pythonw_path()
    launcher = os.path.join(SCRIPT_DIR, 'launcher.py')

    # Command to run
    command = f'"{pythonw}" "{launcher}"'

    try:
        # Open the registry key for current user startup
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # Set the value
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)

        print(f"✅ Added to Windows startup registry")
        print(f"   Command: {command}")
        return True

    except Exception as e:
        print(f"❌ Failed to add to registry: {e}")
        return False


def remove_from_startup_registry():
    """Remove Claude Pulse from Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)

        print(f"✅ Removed from Windows startup")
        return True

    except FileNotFoundError:
        print(f"ℹ️  {APP_NAME} was not in startup")
        return True
    except Exception as e:
        print(f"❌ Failed to remove from registry: {e}")
        return False


def check_startup_status():
    """Check if Claude Pulse is set to run on startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )

        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)

        print(f"✅ {APP_NAME} is set to run on startup")
        print(f"   Command: {value}")
        return True

    except FileNotFoundError:
        print(f"❌ {APP_NAME} is NOT set to run on startup")
        return False
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False


def create_batch_launcher():
    """Create a batch file to launch Claude Pulse."""
    batch_path = os.path.join(SCRIPT_DIR, 'ClaudePulse.bat')
    pythonw = get_pythonw_path()
    launcher = os.path.join(SCRIPT_DIR, 'launcher.py')

    content = f'''@echo off
start "" "{pythonw}" "{launcher}"
'''

    with open(batch_path, 'w') as f:
        f.write(content)

    print(f"✅ Created batch launcher: {batch_path}")
    return batch_path


def create_vbs_launcher():
    """Create a VBS file to launch silently (no console flash)."""
    vbs_path = os.path.join(SCRIPT_DIR, 'ClaudePulse.vbs')
    pythonw = get_pythonw_path()
    launcher = os.path.join(SCRIPT_DIR, 'launcher.py')

    content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{pythonw}"" ""{launcher}""", 0, False
'''

    with open(vbs_path, 'w') as f:
        f.write(content)

    print(f"✅ Created VBS launcher: {vbs_path}")
    return vbs_path


def main():
    """Main installation menu."""
    print("=" * 50)
    print("Claude Pulse Installer")
    print("=" * 50)
    print()
    print("Options:")
    print("  1. Install (add to Windows startup)")
    print("  2. Uninstall (remove from Windows startup)")
    print("  3. Check status")
    print("  4. Create launcher files")
    print("  5. Run now")
    print("  6. Exit")
    print()

    while True:
        choice = input("Enter choice (1-6): ").strip()

        if choice == '1':
            print()
            add_to_startup_registry()
            create_vbs_launcher()
            print()
            print("Claude Pulse will now start automatically when you log in.")
            print("To start it now, run: python launcher.py")

        elif choice == '2':
            print()
            remove_from_startup_registry()

        elif choice == '3':
            print()
            check_startup_status()

        elif choice == '4':
            print()
            create_batch_launcher()
            create_vbs_launcher()

        elif choice == '5':
            print()
            print("Starting Claude Pulse...")
            os.system(f'start "" "{get_pythonw_path()}" "{os.path.join(SCRIPT_DIR, "launcher.py")}"')
            print("Claude Pulse started in background.")

        elif choice == '6':
            break

        else:
            print("Invalid choice. Please enter 1-6.")

        print()


if __name__ == "__main__":
    main()
