@echo off
echo Building Simple Image Converter for Windows...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Install required dependencies
echo Installing required dependencies...
python -m pip install --upgrade pip
python -m pip install pillow pillow-heif tkinterdnd2 cx_Freeze

REM Create the application icon
echo Creating application icon...
python create_icon.py

REM Build the Windows application
echo Building Windows application...
python setup.py build_exe

if %ERRORLEVEL% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo The executable can be found in the 'build\exe.*' folder.
echo.

REM Create desktop shortcut
echo Creating desktop shortcut...
set "BUILD_DIR="
for /d %%i in (build\exe.*) do set "BUILD_DIR=%%i"
if not defined BUILD_DIR (
    echo Could not find build directory.
    pause
    exit /b 1
)

set "EXECUTABLE=%CD%\%BUILD_DIR%\SimpleImageConverter.exe"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\Simple Image Converter.lnk"

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%SHORTCUT%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%EXECUTABLE%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%EXECUTABLE%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript /nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo Desktop shortcut created at: %SHORTCUT%
echo.

REM Ask if user wants to run the application
set /p runapp=Do you want to run the application now? (Y/N) 
if /i "%runapp%"=="Y" (
    start "" "%EXECUTABLE%"
)

pause 
