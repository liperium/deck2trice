"""Build script for creating deck2trice-gui executable."""
import subprocess
import sys
from pathlib import Path

def build_exe():
    """Build the GUI executable using PyInstaller."""
    print("Building deck2trice-gui executable...")

    # Build command - use python -m to ensure proper execution
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",           # Single executable file
        "--windowed",          # No console window
        "--name", "deck2trice-gui",
        "--clean",             # Clean build cache
        "deck2trice/gui.py"
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, shell=True)

    if result.returncode == 0:
        exe_path = Path("dist") / "deck2trice-gui.exe"
        if exe_path.exists():
            print(f"\n✓ Success! Executable created at: {exe_path.absolute()}")
            print(f"  Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("\n✗ Build completed but executable not found")
    else:
        print("\n✗ Build failed")

if __name__ == "__main__":
    build_exe()
