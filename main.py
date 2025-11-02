"""
NexusDown - Modern Internet Download Manager
============================================
This is the main entry point for the NexusDown application.
It initializes the application, database, and main window.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from ui_mainwindow import MainWindow
from database import DatabaseManager
import base64

# App icon as base64 (SVG converted to PNG base64)
APP_ICON_BASE64 = """
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
"""

def create_app_icon():
    """
    Create application icon from base64 data.
    
    Returns:
        QIcon object
    """
    # Decode base64 icon
    icon_data = base64.b64decode(APP_ICON_BASE64)
    
    # Create pixmap from data
    pixmap = QPixmap()
    pixmap.loadFromData(icon_data)
    
    return QIcon(pixmap)

def main():
    """
    Main function to start the application.
    """
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("NexusDown")
    app.setOrganizationName("NexusDown")
    
    # Set application icon
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Create and show main window
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()