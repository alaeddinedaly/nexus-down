"""
NexusDown - Modern Main Window UI
==================================
Contains the redesigned main window UI with modern dark theme.
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QProgressBar, QHeaderView, QMenu, QAction, QLabel
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QFont
from datetime import datetime
import requests

from database import DatabaseManager
from download_manager import DownloadManager
from ui_dialogs import AddDownloadDialog, SettingsDialog
from utils import format_bytes, format_speed, get_filename_from_url


class MainWindow(QMainWindow):
    """
    Main application window with modern dark theme.
    """
    
    def __init__(self):
        """
        Initialize main window.
        """
        super().__init__()
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.download_manager = DownloadManager()
        
        # Load max concurrent setting
        max_concurrent = int(self.db_manager.get_setting('max_concurrent_downloads') or '3')
        self.download_manager.set_max_concurrent(max_concurrent)
        
        # Setup UI
        self.setup_ui()
        self.load_downloads()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_table)
        self.update_timer.start(500)  # Update every 500ms
    
    def setup_ui(self):
        """
        Setup the user interface with modern styling.
        """
        self.setWindowTitle("NexusDown - Modern Download Manager")
        self.setGeometry(100, 100, 1300, 750)
        self.setMinimumSize(1000, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create header
        self.create_header(layout)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create download table
        self.create_table()
        layout.addWidget(self.downloads_table)
        
        # Create status bar
        self.create_status_bar()
        
        # Apply modern dark theme
        self.apply_modern_theme()
    
    def create_header(self, layout):
        """
        Create modern header with app name and gradient.
        """
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)
        
        # App title
        title_label = QLabel("NEXUSDOWN")
        title_label.setObjectName("appTitle")
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title_label.setFont(title_font)
        
        # Subtitle
        subtitle_label = QLabel("Modern Download Manager")
        subtitle_label.setObjectName("appSubtitle")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(subtitle_font)
        
        # Title container
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        layout.addWidget(header)
    
    def create_toolbar(self):
        """
        Create modern toolbar with styled action buttons.
        """
        toolbar = QToolBar()
        toolbar.setObjectName("modernToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setContentsMargins(15, 10, 15, 10)
        self.addToolBar(toolbar)
        
        # Add Download button
        add_action = QAction("  Add Download", self)
        add_action.setObjectName("addButton")
        add_action.triggered.connect(self.show_add_download_dialog)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Pause button
        pause_action = QAction("  Pause", self)
        pause_action.triggered.connect(self.pause_selected)
        toolbar.addAction(pause_action)
        
        # Resume button
        resume_action = QAction("  Resume", self)
        resume_action.triggered.connect(self.resume_selected)
        toolbar.addAction(resume_action)
        
        # Cancel button
        cancel_action = QAction("  Cancel", self)
        cancel_action.triggered.connect(self.cancel_selected)
        toolbar.addAction(cancel_action)
        
        toolbar.addSeparator()
        
        # Remove button
        remove_action = QAction("  Remove", self)
        remove_action.triggered.connect(self.remove_selected)
        toolbar.addAction(remove_action)
        
        # Open Folder button
        folder_action = QAction("  Open Folder", self)
        folder_action.triggered.connect(self.open_download_folder)
        toolbar.addAction(folder_action)
        
        # Add stretch to push settings to right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
        toolbar.addWidget(spacer)
        
        # Settings button
        settings_action = QAction("  Settings", self)
        settings_action.setObjectName("settingsButton")
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)
    
    def create_table(self):
        """
        Create downloads table with modern styling.
        """
        self.downloads_table = QTableWidget()
        self.downloads_table.setObjectName("modernTable")
        self.downloads_table.setColumnCount(7)
        self.downloads_table.setHorizontalHeaderLabels([
            "Filename", "Progress", "Size", "Speed", "Status", "Date", "ID"
        ])
        
        # Set column widths
        header = self.downloads_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Filename
        header.setSectionResizeMode(1, QHeaderView.Fixed)     # Progress
        header.setSectionResizeMode(2, QHeaderView.Fixed)     # Size
        header.setSectionResizeMode(3, QHeaderView.Fixed)     # Speed
        header.setSectionResizeMode(4, QHeaderView.Fixed)     # Status
        header.setSectionResizeMode(5, QHeaderView.Fixed)     # Date
        header.setSectionResizeMode(6, QHeaderView.Fixed)     # ID
        
        self.downloads_table.setColumnWidth(1, 180)  # Progress
        self.downloads_table.setColumnWidth(2, 110)  # Size
        self.downloads_table.setColumnWidth(3, 130)  # Speed
        self.downloads_table.setColumnWidth(4, 120)  # Status
        self.downloads_table.setColumnWidth(5, 160)  # Date
        self.downloads_table.setColumnWidth(6, 60)   # ID
        
        # Hide ID column (used internally)
        self.downloads_table.setColumnHidden(6, True)
        
        # Table settings
        self.downloads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloads_table.setSelectionMode(QTableWidget.SingleSelection)
        self.downloads_table.setAlternatingRowColors(True)
        self.downloads_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.downloads_table.setShowGrid(False)
        self.downloads_table.verticalHeader().setVisible(False)
        
        # Set row height
        self.downloads_table.verticalHeader().setDefaultSectionSize(55)
        
        # Context menu
        self.downloads_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.downloads_table.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_status_bar(self):
        """
        Create modern status bar.
        """
        status_bar = QStatusBar()
        status_bar.setObjectName("modernStatusBar")
        self.setStatusBar(status_bar)
        
        # Container for status items
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(15, 5, 15, 5)
        status_layout.setSpacing(20)
        
        # Total speed label
        speed_icon = QLabel("⚡")
        speed_icon.setStyleSheet("font-size: 16px;")
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setObjectName("speedLabel")
        
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(5)
        speed_layout.addWidget(speed_icon)
        speed_layout.addWidget(self.speed_label)
        
        # Active downloads label
        active_icon = QLabel("📥")
        active_icon.setStyleSheet("font-size: 16px;")
        self.active_label = QLabel("0 Active")
        self.active_label.setObjectName("activeLabel")
        
        active_layout = QHBoxLayout()
        active_layout.setSpacing(5)
        active_layout.addWidget(active_icon)
        active_layout.addWidget(self.active_label)
        
        status_layout.addLayout(speed_layout)
        status_layout.addLayout(active_layout)
        status_layout.addStretch()
        
        status_bar.addPermanentWidget(status_container)
    
    def apply_modern_theme(self):
        """
        Apply modern dark theme with gradients and accents.
        """
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #1a1d29;
            }
            
            /* Header with Gradient */
            #header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
            
            #appTitle {
                color: #ffffff;
                letter-spacing: 2px;
            }
            
            #appSubtitle {
                color: rgba(255, 255, 255, 0.8);
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #252836;
                border: none;
                border-bottom: 1px solid #2d3142;
                padding: 8px;
                spacing: 8px;
            }
            
            QToolBar::separator {
                background-color: #3d4159;
                width: 1px;
                margin: 8px 10px;
            }
            
            QToolBar QToolButton {
                background-color: transparent;
                color: #e2e8f0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            
            QToolBar QToolButton:hover {
                background-color: rgba(102, 126, 234, 0.15);
                color: #667eea;
            }
            
            QToolBar QToolButton:pressed {
                background-color: rgba(102, 126, 234, 0.25);
            }
            
            QToolBar QToolButton#addButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                font-weight: 600;
            }
            
            QToolBar QToolButton#addButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c93f0, stop:1 #8b5cad);
            }
            
            QToolBar QToolButton#settingsButton {
                background-color: rgba(72, 187, 120, 0.15);
                color: #48bb78;
            }
            
            QToolBar QToolButton#settingsButton:hover {
                background-color: rgba(72, 187, 120, 0.25);
            }
            
            /* Table */
            #modernTable {
                background-color: #252836;
                border: none;
                border-radius: 0px;
                gridline-color: transparent;
                color: #e2e8f0;
                font-size: 13px;
            }
            
            #modernTable::item {
                padding: 12px 8px;
                border: none;
            }
            
            #modernTable::item:selected {
                background-color: rgba(102, 126, 234, 0.2);
                color: #ffffff;
            }
            
            #modernTable::item:hover {
                background-color: rgba(102, 126, 234, 0.1);
            }
            
            QHeaderView::section {
                background-color: #1a1d29;
                color: #94a3b8;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #667eea;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: rgba(102, 126, 234, 0.1);
                text-align: center;
                height: 24px;
                color: #e2e8f0;
                font-weight: 600;
                font-size: 11px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
            }
            
            /* Status Bar */
            #modernStatusBar {
                background-color: #1a1d29;
                border-top: 1px solid #2d3142;
                color: #e2e8f0;
            }
            
            #speedLabel, #activeLabel {
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background-color: #252836;
                width: 12px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3d4159;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #4a5069;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #252836;
                height: 12px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #3d4159;
                border-radius: 6px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #4a5069;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Context Menu */
            QMenu {
                background-color: #252836;
                border: 1px solid #3d4159;
                border-radius: 8px;
                padding: 8px;
            }
            
            QMenu::item {
                color: #e2e8f0;
                padding: 8px 30px 8px 12px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background-color: rgba(102, 126, 234, 0.2);
            }
            
            QMenu::separator {
                height: 1px;
                background-color: #3d4159;
                margin: 6px 8px;
            }
        """)
    
    def show_add_download_dialog(self):
        """
        Show add download dialog.
        """
        dialog = AddDownloadDialog(self, self.db_manager)
        if dialog.exec_():
            url, save_path = dialog.get_data()
            self.add_download(url, save_path)
    
    def show_settings_dialog(self):
        """
        Show settings dialog.
        """
        dialog = SettingsDialog(self, self.db_manager)
        if dialog.exec_():
            # Reload settings
            max_concurrent = int(self.db_manager.get_setting('max_concurrent_downloads') or '3')
            self.download_manager.set_max_concurrent(max_concurrent)
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
    
    def add_download(self, url: str, save_path: str):
        """
        Add a new download.
        
        Args:
            url: Download URL
            save_path: Directory to save file
        """
        try:
            # Get filename from URL
            filename = get_filename_from_url(url)
            filepath = os.path.join(save_path, filename)
            
            # Check if file exists
            if os.path.exists(filepath):
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"File '{filename}' already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Get file size (optional)
            filesize = 0
            try:
                response = requests.head(url, timeout=10)
                if 'Content-Length' in response.headers:
                    filesize = int(response.headers['Content-Length'])
            except:
                pass
            
            # Add to database
            download_id = self.db_manager.add_download(url, filename, filepath, filesize)
            
            # Add to download manager
            chunk_size = int(self.db_manager.get_setting('chunk_size') or '8192')
            task = self.download_manager.add_download(download_id, url, filepath, chunk_size)
            
            # Connect signals
            task.progress_updated.connect(self.on_progress_updated)
            task.status_changed.connect(self.on_status_changed)
            task.download_completed.connect(self.on_download_completed)
            task.download_failed.connect(self.on_download_failed)
            
            # Add to table
            self.add_download_to_table(download_id, filename, filesize, "pending")
            
            self.statusBar().showMessage(f"Download added: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add download: {str(e)}")
    
    def add_download_to_table(self, download_id: int, filename: str, filesize: int, status: str):
        """
        Add download to table.
        """
        row = self.downloads_table.rowCount()
        self.downloads_table.insertRow(row)
        
        # Filename
        filename_item = QTableWidgetItem(filename)
        filename_item.setFont(QFont("Segoe UI", 11))
        self.downloads_table.setItem(row, 0, filename_item)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        self.downloads_table.setCellWidget(row, 1, progress_bar)
        
        # Size
        size_text = format_bytes(filesize) if filesize > 0 else "Unknown"
        size_item = QTableWidgetItem(size_text)
        self.downloads_table.setItem(row, 2, size_item)
        
        # Speed
        speed_item = QTableWidgetItem("0 B/s")
        self.downloads_table.setItem(row, 3, speed_item)
        
        # Status
        status_item = QTableWidgetItem(status.upper())
        self.downloads_table.setItem(row, 4, status_item)
        
        # Date
        date_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        date_item = QTableWidgetItem(date_text)
        self.downloads_table.setItem(row, 5, date_item)
        
        # ID (hidden)
        self.downloads_table.setItem(row, 6, QTableWidgetItem(str(download_id)))
    
    def load_downloads(self):
        """
        Load downloads from database.
        """
        downloads = self.db_manager.get_all_downloads()
        
        for download in downloads:
            download_id = download['id']
            filename = download['filename']
            filesize = download['filesize']
            status = download['status']
            downloaded = download['downloaded']
            
            # Add to table
            row = self.downloads_table.rowCount()
            self.downloads_table.insertRow(row)
            
            # Filename
            filename_item = QTableWidgetItem(filename)
            filename_item.setFont(QFont("Segoe UI", 11))
            self.downloads_table.setItem(row, 0, filename_item)
            
            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            if filesize > 0:
                progress = int((downloaded / filesize) * 100)
                progress_bar.setValue(progress)
            self.downloads_table.setCellWidget(row, 1, progress_bar)
            
            # Size
            size_text = format_bytes(filesize) if filesize > 0 else "Unknown"
            self.downloads_table.setItem(row, 2, QTableWidgetItem(size_text))
            
            # Speed
            self.downloads_table.setItem(row, 3, QTableWidgetItem("0 B/s"))
            
            # Status
            status_item = QTableWidgetItem(status.upper())
            self.downloads_table.setItem(row, 4, status_item)
            
            # Date
            date_obj = datetime.fromisoformat(download['created_date'])
            date_text = date_obj.strftime("%Y-%m-%d %H:%M")
            self.downloads_table.setItem(row, 5, QTableWidgetItem(date_text))
            
            # ID (hidden)
            self.downloads_table.setItem(row, 6, QTableWidgetItem(str(download_id)))
            
            # Resume incomplete downloads
            if status in ['downloading', 'paused', 'pending']:
                url = download['url']
                filepath = download['filepath']
                chunk_size = int(self.db_manager.get_setting('chunk_size') or '8192')
                
                task = self.download_manager.add_download(download_id, url, filepath, chunk_size)
                task.progress_updated.connect(self.on_progress_updated)
                task.status_changed.connect(self.on_status_changed)
                task.download_completed.connect(self.on_download_completed)
                task.download_failed.connect(self.on_download_failed)
                
                if status == 'paused':
                    task.pause()
    
    def update_table(self):
        """
        Update table with current download info.
        """
        total_speed = 0.0
        active_count = 0
        
        for row in range(self.downloads_table.rowCount()):
            download_id_item = self.downloads_table.item(row, 6)
            if not download_id_item:
                continue
            
            download_id = int(download_id_item.text())
            task = self.download_manager.get_download(download_id)
            
            if task and task.thread and task.thread.is_alive() and not task.is_paused:
                active_count += 1
                
                # Update progress
                progress_bar = self.downloads_table.cellWidget(row, 1)
                if progress_bar and task.total_bytes > 0:
                    progress = int((task.downloaded_bytes / task.total_bytes) * 100)
                    progress_bar.setValue(progress)
                
                # Update database
                download_data = self.db_manager.get_download(download_id)
                if download_data:
                    speed = download_data['speed']
                    total_speed += speed
        
        # Update status bar
        self.speed_label.setText(format_speed(total_speed))
        self.active_label.setText(f"{active_count} Active")
    
    @pyqtSlot(int, int, float)
    def on_progress_updated(self, download_id: int, downloaded: int, speed: float):
        """
        Handle progress update signal.
        """
        self.db_manager.update_download_progress(download_id, downloaded, speed)
        
        # Find row
        for row in range(self.downloads_table.rowCount()):
            id_item = self.downloads_table.item(row, 6)
            if id_item and int(id_item.text()) == download_id:
                # Update speed
                speed_item = self.downloads_table.item(row, 3)
                if speed_item:
                    speed_item.setText(format_speed(speed))
                break
    
    @pyqtSlot(int, str)
    def on_status_changed(self, download_id: int, status: str):
        """
        Handle status change signal.
        """
        self.db_manager.update_download_status(download_id, status)
        
        # Find row and update status
        for row in range(self.downloads_table.rowCount()):
            id_item = self.downloads_table.item(row, 6)
            if id_item and int(id_item.text()) == download_id:
                status_item = self.downloads_table.item(row, 4)
                if status_item:
                    status_item.setText(status.upper())
                break
    
    @pyqtSlot(int)
    def on_download_completed(self, download_id: int):
        """
        Handle download completion signal.
        """
        download = self.db_manager.get_download(download_id)
        if download:
            filename = download['filename']
            
            # Show notification if enabled
            if self.db_manager.get_setting('enable_notifications') == 'true':
                QMessageBox.information(
                    self, "Download Complete",
                    f"Download completed: {filename}"
                )
            
            self.statusBar().showMessage(f"✓ Download completed: {filename}")
    
    @pyqtSlot(int, str)
    def on_download_failed(self, download_id: int, error: str):
        """
        Handle download failure signal.
        """
        download = self.db_manager.get_download(download_id)
        if download:
            filename = download['filename']
            QMessageBox.warning(
                self, "Download Failed",
                f"Download failed: {filename}\nError: {error}"
            )
    
    def pause_selected(self):
        """
        Pause selected download.
        """
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 6).text())
        self.download_manager.pause_download(download_id)
    
    def resume_selected(self):
        """
        Resume selected download.
        """
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 6).text())
        self.download_manager.resume_download(download_id)
    
    def cancel_selected(self):
        """
        Cancel selected download.
        """
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 6).text())
        
        reply = QMessageBox.question(
            self, "Cancel Download",
            "Are you sure you want to cancel this download?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download_manager.cancel_download(download_id)
    
    def remove_selected(self):
        """
        Remove selected download from list.
        """
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 6).text())
        
        reply = QMessageBox.question(
            self, "Remove Download",
            "Remove this download from the list?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Cancel if active
            self.download_manager.cancel_download(download_id)
            
            # Remove from database
            self.db_manager.delete_download(download_id)
            
            # Remove from table
            self.downloads_table.removeRow(row)
    
    def open_download_folder(self):
        """
        Open download folder of selected item.
        """
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 6).text())
        download = self.db_manager.get_download(download_id)
        
        if download:
            folder = os.path.dirname(download['filepath'])
            if os.path.exists(folder):
                os.startfile(folder) if os.name == 'nt' else os.system(f'xdg-open "{folder}"')
    
    def show_context_menu(self, position):
        """
        Show context menu for table.
        """
        menu = QMenu()
        
        pause_action = menu.addAction("⏸  Pause")
        resume_action = menu.addAction("▶  Resume")
        cancel_action = menu.addAction("⏹  Cancel")
        menu.addSeparator()
        remove_action = menu.addAction("🗑  Remove")
        folder_action = menu.addAction("📁  Open Folder")
        
        action = menu.exec_(self.downloads_table.viewport().mapToGlobal(position))
        
        if action == pause_action:
            self.pause_selected()
        elif action == resume_action:
            self.resume_selected()
        elif action == cancel_action:
            self.cancel_selected()
        elif action == remove_action:
            self.remove_selected()
        elif action == folder_action:
            self.open_download_folder()
    
    def closeEvent(self, event):
        """
        Handle window close event.
        """
        # Ask for confirmation if there are active downloads
        active_count = sum(
            1 for task in self.download_manager.active_downloads.values()
            if task.thread and task.thread.is_alive() and not task.is_paused
        )
        
        if active_count > 0:
            reply = QMessageBox.question(
                self, "Exit",
                f"There are {active_count} active download(s). Exit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Close database connection
        self.db_manager.close()
        event.accept()