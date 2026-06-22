import os
import sys
import subprocess

def main():
    # Only run on Windows
    if sys.platform != "win32":
        print("Shortcuts are only supported on Windows.")
        return

    # Base paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_bat = os.path.join(current_dir, "run.bat")
    icon_path = os.path.join(current_dir, "icon.ico")
    
    # Check if target files exist
    if not os.path.exists(target_bat):
        print(f"Error: Target run.bat not found at {target_bat}")
        return
    if not os.path.exists(icon_path):
        print(f"Error: icon.ico not found at {icon_path}")
        return

    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop, "Neurocode Studio.lnk")

    # VBScript generator
    vbs_content = f"""
Set shell = CreateObject("WScript.Shell")
Set shortcut = shell.CreateShortcut("{shortcut_path.replace(chr(92), chr(92)*2)}")
shortcut.TargetPath = "{target_bat.replace(chr(92), chr(92)*2)}"
shortcut.WorkingDirectory = "{current_dir.replace(chr(92), chr(92)*2)}"
shortcut.IconLocation = "{icon_path.replace(chr(92), chr(92)*2)}"
shortcut.Description = "Launch Neurocode Studio"
shortcut.Save()
"""
    vbs_path = os.path.join(current_dir, "temp_shortcut.vbs")
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        subprocess.run(["wscript.exe", vbs_path], check=True)
        print(f"Desktop shortcut successfully created at: {shortcut_path}")
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
    finally:
        if os.path.exists(vbs_path):
            try:
                os.remove(vbs_path)
            except:
                pass

if __name__ == "__main__":
    main()
