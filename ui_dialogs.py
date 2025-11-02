"""
NexusDown - Modern UI Dialogs
==============================
Contains dialog windows with modern dark theme styling.
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSpinBox, QCheckBox, QGroupBox,
    QFormLayout, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import DatabaseManager


class AddDownloadDialog(QDialog):
    """
    Dialog for adding a new download with modern styling.
    """
    
    def __init__(self, parent=None, db_manager=None):
        """
        Initialize add download dialog.
        
        Args:
            parent: Parent widget
            db_manager: Database manager instance
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
    
    def setup_ui(self):
        """
        Setup the user interface.
        """
        self.setWindowTitle("Add New Download")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMinimumHeight(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Add New Download")
        title.setObjectName("dialogTitle")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # URL input
        url_layout = QVBoxLayout()
        url_layout.setSpacing(8)
        url_label = QLabel("Download URL")
        url_label.setObjectName("fieldLabel")
        self.url_input = QLineEdit()
        self.url_input.setObjectName("modernInput")
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        self.url_input.setMinimumHeight(40)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Save location
        save_layout = QVBoxLayout()
        save_layout.setSpacing(8)
        save_label = QLabel("Save Location")
        save_label.setObjectName("fieldLabel")
        
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.save_input = QLineEdit()
        self.save_input.setObjectName("modernInput")
        self.save_input.setMinimumHeight(40)
        
        # Get default folder from settings
        default_folder = self.db_manager.get_setting('default_download_folder')
        if default_folder:
            self.save_input.setText(default_folder)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseButton")
        browse_btn.setMinimumHeight(40)
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(self.browse_folder)
        
        input_row.addWidget(self.save_input)
        input_row.addWidget(browse_btn)
        
        save_layout.addWidget(save_label)
        save_layout.addLayout(input_row)
        layout.addLayout(save_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setMinimumWidth(110)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("Add Download")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setDefault(True)
        ok_btn.setMinimumHeight(42)
        ok_btn.setMinimumWidth(140)
        ok_btn.clicked.connect(self.accept_download)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # Apply modern theme
        self.apply_modern_theme()
    
    def apply_modern_theme(self):
        """
        Apply modern dark theme.
        """
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d29;
            }
            
            #dialogTitle {
                color: #e2e8f0;
                margin-bottom: 10px;
            }
            
            #fieldLabel {
                color: #94a3b8;
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            #modernInput {
                background-color: #252836;
                border: 2px solid #3d4159;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 14px;
            }
            
            #modernInput:focus {
                border: 2px solid #667eea;
                background-color: #2a2f42;
            }
            
            #browseButton {
                background-color: #252836;
                border: 2px solid #3d4159;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            
            #browseButton:hover {
                background-color: #2d3142;
                border-color: #667eea;
            }
            
            #primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            
            #primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c93f0, stop:1 #8b5cad);
            }
            
            #primaryButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6cd8, stop:1 #6a4291);
            }
            
            #cancelButton {
                background-color: #252836;
                border: 2px solid #3d4159;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 600;
            }
            
            #cancelButton:hover {
                background-color: #2d3142;
                border-color: #4a5069;
            }
        """)
    
    def browse_folder(self):
        """
        Open folder browser dialog.
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.save_input.text() or os.path.expanduser('~')
        )
        
        if folder:
            self.save_input.setText(folder)
    
    def accept_download(self):
        """
        Validate and accept download.
        """
        url = self.url_input.text().strip()
        save_path = self.save_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL.")
            return
        
        if not save_path:
            QMessageBox.warning(self, "Error", "Please select a save location.")
            return
        
        if not os.path.exists(save_path):
            QMessageBox.warning(self, "Error", "Selected folder does not exist.")
            return
        
        self.accept()
    
    def get_data(self):
        """
        Get entered data.
        
        Returns:
            Tuple of (url, save_path)
        """
        return self.url_input.text().strip(), self.save_input.text().strip()


class SettingsDialog(QDialog):
    """
    Dialog for managing application settings with modern styling.
    """
    
    def __init__(self, parent=None, db_manager=None):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent widget
            db_manager: Database manager instance
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """
        Setup the user interface.
        """
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Settings")
        title.setObjectName("dialogTitle")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Download Settings Group
        download_group = QGroupBox("Download Settings")
        download_group.setObjectName("modernGroup")
        download_layout = QFormLayout(download_group)
        download_layout.setSpacing(15)
        download_layout.setContentsMargins(20, 25, 20, 20)
        
        # Max concurrent downloads
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setObjectName("modernSpinBox")
        self.max_concurrent_spin.setMinimum(1)
        self.max_concurrent_spin.setMaximum(10)
        self.max_concurrent_spin.setValue(3)
        self.max_concurrent_spin.setMinimumHeight(40)
        download_layout.addRow("Max Concurrent Downloads:", self.max_concurrent_spin)
        
        # Default download folder
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        self.folder_input = QLineEdit()
        self.folder_input.setObjectName("modernInput")
        self.folder_input.setMinimumHeight(40)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseButton")
        browse_btn.setMinimumHeight(40)
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_btn)
        download_layout.addRow("Default Download Folder:", folder_layout)
        
        # Chunk size
        self.chunk_size_combo = QComboBox()
        self.chunk_size_combo.setObjectName("modernComboBox")
        self.chunk_size_combo.addItems(["4 KB", "8 KB", "16 KB", "32 KB", "64 KB"])
        self.chunk_size_combo.setCurrentIndex(1)  # 8 KB default
        self.chunk_size_combo.setMinimumHeight(40)
        download_layout.addRow("Download Chunk Size:", self.chunk_size_combo)
        
        layout.addWidget(download_group)
        
        # Notification Settings Group
        notification_group = QGroupBox("Notifications")
        notification_group.setObjectName("modernGroup")
        notification_layout = QVBoxLayout(notification_group)
        notification_layout.setContentsMargins(20, 25, 20, 20)
        
        # Enable notifications
        self.enable_notifications_check = QCheckBox("Enable download completion notifications")
        self.enable_notifications_check.setObjectName("modernCheckBox")
        self.enable_notifications_check.setChecked(True)
        notification_layout.addWidget(self.enable_notifications_check)
        
        layout.addWidget(notification_group)
        
        # Theme Settings Group
        theme_group = QGroupBox("Appearance")
        theme_group.setObjectName("modernGroup")
        theme_layout = QFormLayout(theme_group)
        theme_layout.setSpacing(15)
        theme_layout.setContentsMargins(20, 25, 20, 20)
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("modernComboBox")
        self.theme_combo.addItems(["Dark (Default)", "Light (Coming Soon)"])
        self.theme_combo.setMinimumHeight(40)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setMinimumWidth(110)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setDefault(True)
        save_btn.setMinimumHeight(42)
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        # Apply modern theme
        self.apply_modern_theme()
    
    def apply_modern_theme(self):
        """
        Apply modern dark theme.
        """
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1d29;
            }
            
            #dialogTitle {
                color: #e2e8f0;
                margin-bottom: 10px;
            }
            
            #modernGroup {
                background-color: #252836;
                border: 2px solid #3d4159;
                border-radius: 12px;
                font-weight: 600;
                color: #e2e8f0;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            #modernGroup::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #667eea;
            }
            
            QLabel {
                color: #94a3b8;
                font-size: 13px;
            }
            
            #modernInput {
                background-color: #1a1d29;
                border: 2px solid #3d4159;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 13px;
            }
            
            #modernInput:focus {
                border: 2px solid #667eea;
            }
            
            #modernSpinBox {
                background-color: #1a1d29;
                border: 2px solid #3d4159;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 13px;
            }
            
            #modernSpinBox:focus {
                border: 2px solid #667eea;
            }
            
            #modernSpinBox::up-button, #modernSpinBox::down-button {
                background-color: #3d4159;
                border: none;
                width: 20px;
            }
            
            #modernSpinBox::up-button:hover, #modernSpinBox::down-button:hover {
                background-color: #667eea;
            }
            
            #modernComboBox {
                background-color: #1a1d29;
                border: 2px solid #3d4159;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 13px;
            }
            
            #modernComboBox:focus {
                border: 2px solid #667eea;
            }
            
            #modernComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            #modernComboBox QAbstractItemView {
                background-color: #252836;
                border: 2px solid #3d4159;
                selection-background-color: rgba(102, 126, 234, 0.3);
                color: #e2e8f0;
            }
            
            #modernCheckBox {
                color: #e2e8f0;
                font-size: 13px;
                spacing: 8px;
            }
            
            #modernCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3d4159;
                border-radius: 4px;
                background-color: #1a1d29;
            }
            
            #modernCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNEw2IDExLjMzMzNMMi42NjY2NyA4IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            #browseButton {
                background-color: #1a1d29;
                border: 2px solid #3d4159;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            
            #browseButton:hover {
                background-color: #252836;
                border-color: #667eea;
            }
            
            #primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            
            #primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c93f0, stop:1 #8b5cad);
            }
            
            #cancelButton {
                background-color: #252836;
                border: 2px solid #3d4159;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 600;
            }
            
            #cancelButton:hover {
                background-color: #2d3142;
                border-color: #4a5069;
            }
        """)
    
    def browse_folder(self):
        """
        Open folder browser dialog.
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Default Download Folder",
            self.folder_input.text() or os.path.expanduser('~')
        )
        
        if folder:
            self.folder_input.setText(folder)
    
    def load_settings(self):
        """
        Load settings from database.
        """
        # Max concurrent downloads
        max_concurrent = int(self.db_manager.get_setting('max_concurrent_downloads') or '3')
        self.max_concurrent_spin.setValue(max_concurrent)
        
        # Default folder
        default_folder = self.db_manager.get_setting('default_download_folder')
        if default_folder:
            self.folder_input.setText(default_folder)
        
        # Chunk size
        chunk_size = int(self.db_manager.get_setting('chunk_size') or '8192')
        chunk_index = {4096: 0, 8192: 1, 16384: 2, 32768: 3, 65536: 4}.get(chunk_size, 1)
        self.chunk_size_combo.setCurrentIndex(chunk_index)
        
        # Notifications
        enable_notifications = self.db_manager.get_setting('enable_notifications') == 'true'
        self.enable_notifications_check.setChecked(enable_notifications)
        
        # Theme (always dark for now)
        self.theme_combo.setCurrentIndex(0)
    
    def save_settings(self):
        """
        Save settings to database.
        """
        # Validate folder
        folder = self.folder_input.text().strip()
        if not os.path.exists(folder):
            QMessageBox.warning(self, "Error", "Selected folder does not exist.")
            return
        
        # Save settings
        self.db_manager.set_setting('max_concurrent_downloads', str(self.max_concurrent_spin.value()))
        self.db_manager.set_setting('default_download_folder', folder)
        
        # Chunk size
        chunk_sizes = [4096, 8192, 16384, 32768, 65536]
        chunk_size = chunk_sizes[self.chunk_size_combo.currentIndex()]
        self.db_manager.set_setting('chunk_size', str(chunk_size))
        
        # Notifications
        enable_notifications = 'true' if self.enable_notifications_check.isChecked() else 'false'
        self.db_manager.set_setting('enable_notifications', enable_notifications)
        
        # Theme
        self.db_manager.set_setting('theme', 'dark')
        
        self.accept()