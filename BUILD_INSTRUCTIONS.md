# NexusDown - Build Instructions

This guide will help you create a standalone `.exe` and installer for NexusDown.

## Prerequisites

1. **Python 3.8+** installed
2. **All dependencies** installed:

   ```bash
   pip install PyQt5 requests pyinstaller pillow
   ```

3. **Inno Setup** (for creating installer): Download from [https://jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)

## Quick Build (Recommended)

### Option 1: Just the EXE (No Installer)

1. Run the build script:

   ```bash
   build.bat
   ```

2. Your executable will be in: `dist\NexusDown.exe`

3. You can now run this EXE directly - no Python needed!

### Option 2: Full Installer

1. First, build the EXE:

   ```bash
   build.bat
   ```

2. Open `installer.iss` in Inno Setup

3. Click **Build > Compile** in Inno Setup

4. Your installer will be in: `installer_output\NexusDown-Setup-1.0.0.exe`

## Manual Build Steps

If the automated script doesn't work, follow these steps:

### Step 1: Create Icon

```bash
python create_icon.py
```

### Step 2: Build EXE

```bash
pyinstaller --clean NexusDown.spec
```

### Step 3: Test the EXE

```bash
dist\NexusDown.exe
```

### Step 4: Create Installer (Optional)

1. Install Inno Setup
2. Open `installer.iss`
3. Compile the script

## File Structure

After building, your project should look like this:

```
nexusdown/
├── main.py
├── database.py
├── download_manager.py
├── ui_mainwindow.py
├── ui_dialogs.py
├── utils.py
├── NexusDown.spec          # PyInstaller config
├── version_info.txt        # Version info
├── icon.ico                # Application icon
├── create_icon.py          # Icon generator
├── build.bat               # Build script
├── installer.iss           # Inno Setup script
├── LICENSE.txt             # License file
├── build/                  # Build cache (created by PyInstaller)
├── dist/
│   └── NexusDown.exe      # ✓ Your standalone executable!
└── installer_output/
    └── NexusDown-Setup-1.0.0.exe  # ✓ Your installer!
```

## Troubleshooting

### "PyInstaller not found"

```bash
pip install pyinstaller
```

### "Failed to create icon"

```bash
pip install pillow
python create_icon.py
```

### "ModuleNotFoundError" when running EXE

Add the missing module to `hiddenimports` in `NexusDown.spec`:

```python
hiddenimports=[
    'PyQt5.QtCore',
    'your_missing_module',
],
```

### EXE is too large (>100MB)

This is normal for PyQt5 applications. To reduce size:

- Use UPX compression (already enabled in spec file)
- Remove unused dependencies
- Consider using PyQt5-slim if available

### Antivirus flags the EXE

This is common with PyInstaller executables. Solutions:

- Sign your executable with a code signing certificate
- Submit as false positive to antivirus vendors
- Build on a clean system

## Distribution

### Single EXE Distribution

Simply share `dist\NexusDown.exe` - users can run it directly!

### Installer Distribution

Share `installer_output\NexusDown-Setup-1.0.0.exe`:

- Professional installation experience
- Creates Start Menu shortcuts
- Handles updates cleanly
- Users can uninstall easily

## Updates

To release a new version:

1. Update version in `version_info.txt`
2. Update version in `installer.iss`
3. Rebuild: `build.bat`
4. Recompile installer in Inno Setup
5. Distribute new installer

## Notes

- **Database location**: The app creates `idm_database.db` in the same folder as the EXE
- **Downloads folder**: Default is user's `Downloads` folder
- **Temp files**: Download temp files (`.idmtemp`) are stored with the downloads
- **No installation required**: The EXE is portable and can run from any location

## Advanced: One-File vs One-Folder

Current configuration creates a **one-file** EXE (everything bundled).

To create a **one-folder** distribution (faster startup, smaller EXE):

In `NexusDown.spec`, change:

```python
exe = EXE(
    # ... other parameters ...
    # Remove these lines to create one-folder
    # a.binaries,
    # a.zipfiles,
    # a.datas,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexusDown',
)
```

Then the output will be in `dist\NexusDown\` folder.
