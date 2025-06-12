import sys
import os
from cx_Freeze import setup, Executable

# Dependencies - Add more specific package includes for tkinterdnd2
build_exe_options = {
    "packages": ["tkinter", "PIL", "pillow_heif", "tkinterdnd2"],
    "includes": ["tkinter", "tkinter.ttk", "PIL", "pillow_heif", "tkinterdnd2"],
    "include_files": ["app_icon.ico"],  # Include the icon file
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
            "image_converter.py",
            base=base,
            target_name="SimpleImageConverter.exe",
            icon="app_icon.ico"  # Will use this icon if it exists
        )
    ]
) 
