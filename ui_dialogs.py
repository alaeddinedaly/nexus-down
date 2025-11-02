# ui_dialogs.py

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
                background-color: #1e1e2e;
            }
            
            #dialogTitle {
                color: #e0e0e0;
                margin-bottom: 10px;
            }
            
            #fieldLabel {
                color: #b0b0b0;
                font-size: 13px;
                font-weight: 600;
            }
            
            #modernInput {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e0e0e0;
                font-size: 14px;
            }
            
            #modernInput:focus {
                border: 2px solid #4a90e2;
            }
            
            #browseButton {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 600;
            }
            
            #browseButton:hover {
                background-color: #3a3a4e;
                border-color: #4a90e2;
            }
            
            #primaryButton {
                background-color: #4a90e2;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            
            #primaryButton:hover {
                background-color: #5aa0f2;
            }
            
            #primaryButton:pressed {
                background-color: #3a80d2;
            }
            
            #cancelButton {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: 600;
            }
            
            #cancelButton:hover {
                background-color: #3a3a4e;
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
        self.setMinimumHeight(550)
        
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
        
        # Number of connections per download (NEW)
        self.num_connections_spin = QSpinBox()
        self.num_connections_spin.setObjectName("modernSpinBox")
        self.num_connections_spin.setMinimum(1)
        self.num_connections_spin.setMaximum(16)
        self.num_connections_spin.setValue(8)
        self.num_connections_spin.setMinimumHeight(40)
        self.num_connections_spin.setToolTip("More connections = faster downloads (recommended: 4-8)\nNote: HTTPS downloads automatically use fewer connections to avoid SSL errors")
        download_layout.addRow("Connections Per Download:", self.num_connections_spin)
        
        # Force single connection for large HTTPS files (NEW)
        self.force_single_https_check = QCheckBox("Use single connection for large HTTPS files")
        self.force_single_https_check.setObjectName("modernCheckBox")
        self.force_single_https_check.setChecked(True)
        self.force_single_https_check.setToolTip("Prevents SSL errors when downloading large HTTPS files (>500MB)")
        download_layout.addRow("", self.force_single_https_check)
        
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
        self.chunk_size_combo.addItems(["4 KB", "8 KB (Default)", "16 KB", "32 KB", "64 KB"])
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
                background-color: #1e1e2e;
            }
            
            #dialogTitle {
                color: #e0e0e0;
                margin-bottom: 10px;
            }
            
            #modernGroup {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                border-radius: 8px;
                font-weight: 600;
                color: #e0e0e0;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            #modernGroup::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #4a90e2;
            }
            
            QLabel {
                color: #b0b0b0;
                font-size: 13px;
            }
            
            #modernInput {
                background-color: #1e1e2e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e0e0e0;
                font-size: 13px;
            }
            
            #modernInput:focus {
                border: 2px solid #4a90e2;
            }
            
            #modernSpinBox {
                background-color: #1e1e2e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e0e0e0;
                font-size: 13px;
            }
            
            #modernSpinBox:focus {
                border: 2px solid #4a90e2;
            }
            
            #modernSpinBox::up-button, #modernSpinBox::down-button {
                background-color: #3a3a4e;
                border: none;
                width: 20px;
            }
            
            #modernSpinBox::up-button:hover, #modernSpinBox::down-button:hover {
                background-color: #4a90e2;
            }
            
            #modernComboBox {
                background-color: #1e1e2e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                padding: 10px 14px;
                color: #e0e0e0;
                font-size: 13px;
            }
            
            #modernComboBox:focus {
                border: 2px solid #4a90e2;
            }
            
            #modernComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            #modernComboBox QAbstractItemView {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                selection-background-color: #4a90e2;
                color: #e0e0e0;
            }
            
            #modernCheckBox {
                color: #e0e0e0;
                font-size: 13px;
                spacing: 8px;
            }
            
            #modernCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3a3a4e;
                border-radius: 4px;
                background-color: #1e1e2e;
            }
            
            #modernCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            
            #browseButton {
                background-color: #1e1e2e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 600;
            }
            
            #browseButton:hover {
                background-color: #2a2a3e;
                border-color: #4a90e2;
            }
            
            #primaryButton {
                background-color: #4a90e2;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            
            #primaryButton:hover {
                background-color: #5aa0f2;
            }
            
            #cancelButton {
                background-color: #2a2a3e;
                border: 2px solid #3a3a4e;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: 600;
            }
            
            #cancelButton:hover {
                background-color: #3a3a4e;
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
        
        # Number of connections
        num_connections = int(self.db_manager.get_setting('num_connections') or '8')
        self.num_connections_spin.setValue(num_connections)
        
        # Force single connection for HTTPS
        force_single = self.db_manager.get_setting('force_single_https')
        self.force_single_https_check.setChecked(force_single != 'false')  # Default to True
        
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
        self.db_manager.set_setting('num_connections', str(self.num_connections_spin.value()))
        self.db_manager.set_setting('force_single_https', 'true' if self.force_single_https_check.isChecked() else 'false')
        self.db_manager.set_setting('default_download_folder', folder)
        
        # Chunk size
        chunk_sizes = [4096, 8192, 16384, 32768, 65536]
        chunk_size = chunk_sizes[self.chunk_size_combo.currentIndex()]
        self.db_manager.set_setting('chunk_size', str(chunk_size))
        
        # Notifications
        enable_notifications = 'true' if self.enable_notifications_check.isChecked() else 'false'
        self.db_manager.set_setting('enable_notifications', enable_notifications)
        
        self.accept()