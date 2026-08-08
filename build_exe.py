import os
import sys
import subprocess
import customtkinter

def build():
    # Kill any currently running CamShow.exe process to release file lock
    try:
        subprocess.run(["taskkill", "/F", "/IM", "CamShow.exe"], capture_output=True)
    except Exception:
        pass

    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"CustomTkinter path: {ctk_path}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=CamShow",
        "--onefile",
        "--noconsole",
        f"--add-data={ctk_path};customtkinter/",
        "main.py"
    ]

    print("Running PyInstaller command:")
    print(" ".join(cmd))

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode == 0:
        print("\n==========================================")
        print(" SUCCESS: CamShow.exe built successfully!")
        print(f" Executable located at: {os.path.abspath('dist/CamShow.exe')}")
        print("==========================================\n")
    else:
        print("\n==========================================")
        print(f" ERROR: PyInstaller build failed with code {result.returncode}")
        print("==========================================\n")

if __name__ == "__main__":
    build()
