# NexusDown - Modern Download Manager

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-orange)

**A sleek, modern download manager with a beautiful dark theme**

</div>

---

## 🎨 Design Philosophy

**NexusDown** features a premium, modern dark interface inspired by 2025 design trends:

### Color Palette

- **Primary Dark**: `#1a1d29` - Deep navy background
- **Secondary Dark**: `#252836` - Elevated surfaces
- **Accent Gradient**: `#667eea` → `#764ba2` - Purple-blue gradient for CTAs
- **Success Green**: `#48bb78` - Positive actions
- **Text Primary**: `#e2e8f0` - High contrast text
- **Text Secondary**: `#94a3b8` - Muted labels

### Typography

- **Primary Font**: Segoe UI (System fallback: System Default)
- **Title Weight**: Bold (700)
- **Body Weight**: Regular (400) / Semibold (600)

### Visual Elements

- **Border Radius**: 6-12px for modern, friendly feel
- **Gradients**: Linear gradients on primary buttons and header
- **Shadows**: Subtle elevation through color layering
- **Spacing**: Generous padding (15-25px) for breathing room
- **Animations**: Smooth hover transitions on interactive elements

---

## 🌟 Features

- **Multi-threaded Downloads**: Download multiple files simultaneously
- **Pause & Resume**: Pause and resume downloads at any time
- **Download Queue**: Intelligent queue management with configurable concurrent downloads
- **Progress Tracking**: Real-time gradient progress bars and download speed monitoring
- **Download History**: SQLite database stores all download metadata
- **Modern UI**: Sleek dark theme with gradient accents and smooth animations
- **Customizable Settings**: Configure max concurrent downloads, default folder, chunk size
- **Notifications**: Get notified when downloads complete
- **Resume Support**: Automatically resume interrupted downloads

---

## 📋 Requirements

- Python 3.7 or higher
- PyQt5
- requests

---

## 🚀 Installation

### Step 1: Clone or Download the Project

```bash
git clone https://github.com/alaeddinedaly/nexus-down.git
cd nexusdown
```

### Step 2: Install Dependencies

```bash
pip install PyQt5 requests
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python main.py
```

---

## 📁 Project Structure

```
nexusdown/
│
├── main.py                 # Application entry point (with embedded icon)
├── database.py             # SQLite database manager
├── download_manager.py     # Download task and manager classes
├── ui_mainwindow.py        # Main window UI (REDESIGNED)
├── ui_dialogs.py           # Dialog windows (REDESIGNED)
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🎮 Usage

### Adding a Download

1. Click the gradient **"Add Download"** button in the toolbar
2. Enter the URL of the file you want to download
3. Select the destination folder (or use the default)
4. Click **"Add Download"** to start

### Managing Downloads

- **Pause**: Select a download and click **"Pause"**
- **Resume**: Select a paused download and click **"Resume"**
- **Cancel**: Select a download and click **"Cancel"**
- **Remove**: Select a download and click **"Remove"**
- **Open Folder**: Select a download and click **"Open Folder"**

### Settings

Click **"Settings"** (with green accent) to configure:

- **Max Concurrent Downloads**: 1-10 simultaneous downloads
- **Default Download Folder**: Where files are saved
- **Download Chunk Size**: 4KB - 64KB
- **Notifications**: Enable/disable completion notifications
- **Theme**: Dark (default) - Light coming soon

---

## 🎨 Design Changes from v1.0

### What's New in the Redesign:

#### 1. **App Rebranding**

- **New Name**: "NexusDown" - representing the nexus/connection point for downloads
- **Custom Icon**: Embedded base64 icon with download arrow symbolism
- **Branded Header**: Gradient header with app name and tagline

#### 2. **Color Scheme**

- Switched from light theme to modern dark palette
- Added purple-blue gradient accents (`#667eea` → `#764ba2`)
- Improved contrast ratios for WCAG compliance
- Consistent color hierarchy throughout

#### 3. **Typography**

- Segoe UI as primary font for modern Windows aesthetic
- Bold, uppercase labels for field names
- Larger font sizes for better readability
- Letter spacing on headers for premium feel

#### 4. **Component Redesign**

**Toolbar:**

- Transparent background with hover states
- Gradient "Add Download" button as primary CTA
- Green-accented Settings button
- Right-aligned settings for visual balance

**Table:**

- Removed grid lines for cleaner look
- Increased row height (55px) for spaciousness
- Gradient progress bars with rounded corners
- Uppercase status text for emphasis
- Smooth hover and selection states

**Dialogs:**

- Larger, more spacious layouts
- Rounded input fields (8px radius)
- Gradient primary buttons
- Proper visual hierarchy with field labels

**Status Bar:**

- Icon-enhanced labels (⚡ for speed, 📥 for active)
- Better spacing and alignment

#### 5. **Interactive Elements**

- Smooth hover transitions on all buttons
- Gradient effects on primary actions
- Custom scrollbar styling to match theme
- Modern context menus with rounded corners

#### 6. **Spacing & Layout**

- Generous padding (15-25px) throughout
- Consistent 8-12px spacing between elements
- Better vertical rhythm
- Balanced use of whitespace

---

## 📦 Packaging with PyInstaller

To create a standalone executable:

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Create Executable

**For Windows:**

```bash
pyinstaller --name="NexusDown" --windowed --onefile main.py
```

**For macOS:**

```bash
pyinstaller --name="NexusDown" --windowed --onefile main.py
```

**For Linux:**

```bash
pyinstaller --name="NexusDown" --windowed --onefile main.py
```

The executable will be in the `dist` folder.

---

## 🗄️ Database Schema

The application uses SQLite with two main tables:

### Downloads Table

- Complete download metadata and status tracking

### Settings Table

- User preferences and configuration

---

## 🔧 Customizing the Theme

All styling is contained in the `apply_modern_theme()` method in:

- `ui_mainwindow.py` - Main window styles
- `ui_dialogs.py` - Dialog styles

To customize colors, modify the QSS (Qt StyleSheet) code:

```python
# Example: Change accent color
# Replace #667eea with your color
background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #YOUR_COLOR_1, stop:1 #YOUR_COLOR_2);
```

---

## 🎯 Design Principles Used

1. **Contrast**: High contrast text on dark backgrounds for readability
2. **Consistency**: Unified color palette and spacing system
3. **Hierarchy**: Clear visual hierarchy through size, weight, and color
4. **Feedback**: Hover states and transitions for all interactive elements
5. **Minimalism**: Clean, uncluttered interface focusing on core functionality
6. **Modern**: Following 2025 design trends (gradients, dark mode, rounded corners)

---

## 🛠️ Troubleshooting

### Icon Not Showing

The icon is embedded as base64 in `main.py`. If it doesn't appear, check your PyQt5 installation.

### Theme Not Applied

Ensure you're using PyQt5 with Fusion style support. The application sets this automatically.

### High DPI Issues

The app enables high DPI scaling automatically. If text appears blurry, check your system scaling settings.

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 🔮 Future Enhancements

- [ ] Light theme implementation
- [ ] Custom theme creator
- [ ] Animated transitions between states
- [ ] Download categories with color coding
- [ ] System tray integration
- [ ] Browser extension
- [ ] Drag-and-drop URL support
- [ ] Advanced filtering and search

---

## 📸 Screenshots

### Main Window

_Modern dark interface with gradient header and sleek table_

### Add Download Dialog

_Spacious modal with clean input fields and gradient CTA_

### Settings Dialog

_Organized settings with grouped controls and modern styling_

---

**Made with ❤️ using Python and PyQt5**

_NexusDown - Where downloads connect_
