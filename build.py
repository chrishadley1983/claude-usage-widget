"""Build script for Claude Pulse executable."""

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')
BUILD_DIR = os.path.join(BASE_DIR, 'build')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')


def create_icon():
    """Create the application icon if it doesn't exist."""
    ico_path = os.path.join(ASSETS_DIR, 'icon.ico')

    if os.path.exists(ico_path):
        print(f"Icon already exists at {ico_path}")
        return ico_path

    print("Creating application icon...")
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # Import and create the icon
    sys.path.insert(0, BASE_DIR)
    from tray.icon_renderer import create_logo_icon

    # Create icon at multiple sizes
    sizes = [16, 32, 48, 64, 128, 256]
    icons = [create_logo_icon(s) for s in sizes]

    # Save as ICO with multiple sizes
    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:]
    )

    print(f"Icon created at {ico_path}")
    return ico_path


def check_dependencies():
    """Check if required build dependencies are installed."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def build_executable():
    """Build the executable using PyInstaller."""
    print("\n=== Building Claude Pulse Executable ===\n")

    # Clean previous builds
    if os.path.exists(DIST_DIR):
        print("Cleaning previous dist folder...")
        shutil.rmtree(DIST_DIR)

    if os.path.exists(BUILD_DIR):
        print("Cleaning previous build folder...")
        shutil.rmtree(BUILD_DIR)

    # Run PyInstaller
    spec_file = os.path.join(BASE_DIR, 'claude_pulse.spec')
    print(f"Building from spec file: {spec_file}")

    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', spec_file, '--clean'],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        print("\n❌ Build failed!")
        return False

    exe_path = os.path.join(DIST_DIR, 'ClaudePulse.exe')
    if os.path.exists(exe_path):
        print(f"\n✅ Build successful!")
        print(f"   Executable: {exe_path}")
        print(f"   Size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
        return True
    else:
        print("\n❌ Build failed - executable not found!")
        return False


def create_startup_shortcut():
    """Create a Windows startup shortcut."""
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        print("\nTo create startup shortcut, install: pip install winshell pywin32")
        return False

    exe_path = os.path.join(DIST_DIR, 'ClaudePulse.exe')
    if not os.path.exists(exe_path):
        print("Executable not found. Build first!")
        return False

    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, 'Claude Pulse.lnk')

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = exe_path
    shortcut.WorkingDirectory = DIST_DIR
    shortcut.Description = "Claude Pulse - Usage Monitor"
    shortcut.save()

    print(f"\n✅ Startup shortcut created: {shortcut_path}")
    return True


def main():
    """Main build process."""
    print("=" * 50)
    print("Claude Pulse Build Script")
    print("=" * 50)

    # Check dependencies
    check_dependencies()

    # Create icon
    create_icon()

    # Build executable
    success = build_executable()

    if success:
        print("\n" + "=" * 50)
        print("Build Complete!")
        print("=" * 50)
        print("\nTo install:")
        print(f"  1. Copy {os.path.join(DIST_DIR, 'ClaudePulse.exe')} to your preferred location")
        print("  2. Run the executable")
        print("  3. (Optional) Add to Windows startup")
        print("\nTo add to startup manually:")
        print("  1. Press Win+R, type 'shell:startup', press Enter")
        print("  2. Create a shortcut to ClaudePulse.exe in that folder")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
