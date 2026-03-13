import sys
import os
from cx_Freeze import setup, Executable

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
APP_ICON = os.path.join(ROOT_DIR, "app_icon.ico")

# Dependencies - Add more specific package includes for tkinterdnd2
build_exe_options = {
    "packages": ["tkinter", "PIL", "pillow_heif", "tkinterdnd2", "app"],
    "includes": ["tkinter", "tkinter.ttk", "PIL", "pillow_heif", "tkinterdnd2"],
    "include_files": [(APP_ICON, "app_icon.ico")] if os.path.exists(APP_ICON) else [],
    "excludes": []
}

# Base for GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Create an icon file for the application
shortcut_table = [
    # Shortcut parameters: name, target, arguments, description, hotkey, icon, iconindex, showcmd, wkdir
    ("DesktopShortcut",        # Shortcut name
     "DesktopFolder",          # Shortcut location
     "SimpleImageConverter",   # Target name (exe name)
     "[TARGETDIR]SimpleImageConverter.exe",  # Target
     "",                       # Arguments
     "Simple HEIC Image Converter",  # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     1,                        # ShowCmd (1=normal window)
     None),                    # WkDir
     
    ("StartMenuShortcut",      # Shortcut name
     "StartMenuFolder",        # Shortcut location
     "SimpleImageConverter",   # Target name
     "[TARGETDIR]SimpleImageConverter.exe",  # Target
     "",                       # Arguments  
     "Simple HEIC Image Converter",  # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     1,                        # ShowCmd
     None)                     # WkDir
]

# Create MSI installer table for shortcuts
msi_data = {"Shortcut": shortcut_table}

# Additional options
bdist_msi_options = {
    "data": msi_data,
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\SimpleImageConverter",
}

# Application details
setup(
    name="SimpleImageConverter",
    version="1.0",
    description="A simple image converter with HEIC support",
    options={
        "build_exe": build_exe_options,
    },
    executables=[
        Executable(
            os.path.join(ROOT_DIR, "image_converter.py"),
            base=base,
            target_name="SimpleImageConverter.exe",
            icon=APP_ICON if os.path.exists(APP_ICON) else None
        )
    ]
) 