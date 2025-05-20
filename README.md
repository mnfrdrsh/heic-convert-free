# HEIC Convert Free

A Windows application that converts images, including HEIC/HEIF formats, to common image formats like PNG, JPEG, etc.

## Features

- Drag and drop interface for easy file selection
- Supports HEIC/HEIF conversion to common formats (including HEIC/HEIF)
- Creates a desktop shortcut for easy access
- Simple and intuitive user interface

## Requirements

- Python 3.7 or higher (64-bit recommended for Windows builds)
- Required Python packages (listed in `requirements.txt` - *Note: Will create requirements.txt later if needed*)
  - `Pillow` (for image handling)
  - `pillow-heif` (for HEIC/HEIF support)
  - `tkinterdnd2` (for drag and drop functionality)
  - `cx_Freeze` (for building the Windows executable)

## Getting Started

To get a copy of the project up and running on your local machine for development and building, follow these steps.

### Prerequisites

Make sure you have Python installed (3.7+ recommended).

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd bruh-just-convert # Or whatever your repo name is
   ```

2. Install the required dependencies. It's recommended to use a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate # On Windows
   # source .venv/bin/activate # On macOS/Linux
   
   pip install -r requirements.txt # Note: Will create requirements.txt later
   # OR manually install:
   pip install pillow pillow-heif tkinterdnd2 cx_Freeze
   ```

## Building the Windows Application

The simplest way to build the application is to run the included batch file:

```bat
build_windows_app.bat
```

This script automates the build process:
1. Installs/upgrades required dependencies using pip.
2. Creates the application icon (`app_icon.ico`).
3. Builds the standalone executable using `cx_Freeze`.
4. Creates a desktop shortcut pointing to the executable.

The executable will be created in a folder like `build\exe.win-amd64-3.x\` (the exact name depends on your Python version and architecture).

### Manual Build Process:

If you prefer to build manually:

1. Ensure dependencies are installed (see Installation section).
2. Create the application icon:
   ```bash
   python create_icon.py
   ```
3. Build the executable:
   ```bash
   python setup.py build_exe
   ```

The executable will be located in the `build\exe.*\` directory.

## Running the Application

After building, you can run the application by:

- Double-clicking the desktop shortcut created by `build_windows_app.bat`.
- Navigating to the build directory (`build\exe.*\`) and double-clicking `SimpleImageConverter.exe`.

## Manual Execution (without building executable)

If you just want to run the Python script directly (useful for development):

1. Ensure required dependencies are installed (see Installation section).
2. Run the script:
   ```bash
   python image_converter.py
   ```

## Notes for HEIC Support

For HEIC support, the `pillow-heif` package is required. It includes pre-built binaries for libheif on Windows, so `pip install pillow-heif` is usually sufficient.

## Contributing

Contributions are welcome! If you find a bug or want to suggest an enhancement, please open an issue or submit a pull request. Please follow the existing code style.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions or need assistance, you can reach out via [GitHub Issues](<repository_url>/issues).
