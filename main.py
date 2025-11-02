# main.py

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
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from ui_mainwindow import MainWindow
from database import DatabaseManager

def create_simple_icon():
    """
    Create a simple colored icon without using base64.
    
    Returns:
        QIcon object
    """
    # Create a simple 64x64 pixmap with a colored circle
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background circle
    painter.setBrush(QColor(74, 144, 226))  # Blue color
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    
    # Draw inner circle
    painter.setBrush(QColor(255, 255, 255))
    painter.drawEllipse(20, 20, 24, 24)
    
    painter.end()
    
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
    app_icon = create_simple_icon()
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