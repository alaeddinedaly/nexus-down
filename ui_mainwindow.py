# ui_mainwindow.py

"""
NexusDown - Simplified Main Window UI
=====================================
Contains the simplified main window UI with clean design.
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
from utils import format_bytes, format_speed, get_filename_from_url, calculate_eta


class MainWindow(QMainWindow):
    """
    Main application window with simplified clean design.
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
        Setup the user interface with simplified styling.
        """
        self.setWindowTitle("NexusDown - Download Manager")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 550)
        
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
        
        # Apply simplified theme
        self.apply_simplified_theme()
    
    def create_header(self, layout):
        """
        Create simplified header.
        """
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # App title
        title_label = QLabel("NexusDown")
        title_label.setObjectName("appTitle")
        title_font = QFont("Segoe UI", 20, QFont.Bold)
        title_label.setFont(title_font)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
    
    def create_toolbar(self):
        """
        Create simplified toolbar.
        """
        toolbar = QToolBar()
        toolbar.setObjectName("modernToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setContentsMargins(10, 8, 10, 8)
        self.addToolBar(toolbar)
        
        # Add Download button
        add_action = QAction("+ Add Download", self)
        add_action.setObjectName("addButton")
        add_action.triggered.connect(self.show_add_download_dialog)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Control buttons
        pause_action = QAction("Pause", self)
        pause_action.triggered.connect(self.pause_selected)
        toolbar.addAction(pause_action)
        
        resume_action = QAction("Resume", self)
        resume_action.triggered.connect(self.resume_selected)
        toolbar.addAction(resume_action)
        
        cancel_action = QAction("Cancel", self)
        cancel_action.triggered.connect(self.cancel_selected)
        toolbar.addAction(cancel_action)
        
        toolbar.addSeparator()
        
        # Utility buttons
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected)
        toolbar.addAction(remove_action)
        
        folder_action = QAction("Open Folder", self)
        folder_action.triggered.connect(self.open_download_folder)
        toolbar.addAction(folder_action)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
        toolbar.addWidget(spacer)
        
        # Settings button
        settings_action = QAction("Settings", self)
        settings_action.setObjectName("settingsButton")
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)
    
    def create_table(self):
        """
        Create downloads table with simplified styling.
        """
        self.downloads_table = QTableWidget()
        self.downloads_table.setObjectName("modernTable")
        self.downloads_table.setColumnCount(8)
        self.downloads_table.setHorizontalHeaderLabels([
            "Filename", "Progress", "Size", "Speed", "Time Left", "Status", "Date", "ID"
        ])
        
        # Set column widths
        header = self.downloads_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Filename
        header.setSectionResizeMode(1, QHeaderView.Fixed)     # Progress
        header.setSectionResizeMode(2, QHeaderView.Fixed)     # Size
        header.setSectionResizeMode(3, QHeaderView.Fixed)     # Speed
        header.setSectionResizeMode(4, QHeaderView.Fixed)     # Time Left
        header.setSectionResizeMode(5, QHeaderView.Fixed)     # Status
        header.setSectionResizeMode(6, QHeaderView.Fixed)     # Date
        header.setSectionResizeMode(7, QHeaderView.Fixed)     # ID
        
        self.downloads_table.setColumnWidth(1, 160)  # Progress
        self.downloads_table.setColumnWidth(2, 100)  # Size
        self.downloads_table.setColumnWidth(3, 110)  # Speed
        self.downloads_table.setColumnWidth(4, 100)  # Time Left
        self.downloads_table.setColumnWidth(5, 100)  # Status
        self.downloads_table.setColumnWidth(6, 140)  # Date
        self.downloads_table.setColumnWidth(7, 60)   # ID
        
        # Hide ID column
        self.downloads_table.setColumnHidden(7, True)
        
        # Table settings
        self.downloads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloads_table.setSelectionMode(QTableWidget.SingleSelection)
        self.downloads_table.setAlternatingRowColors(True)
        self.downloads_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.downloads_table.setShowGrid(False)
        self.downloads_table.verticalHeader().setVisible(False)
        self.downloads_table.verticalHeader().setDefaultSectionSize(50)
        
        # Context menu
        self.downloads_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.downloads_table.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_status_bar(self):
        """
        Create simplified status bar.
        """
        status_bar = QStatusBar()
        status_bar.setObjectName("modernStatusBar")
        self.setStatusBar(status_bar)
        
        # Status container
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(10, 3, 10, 3)
        status_layout.setSpacing(15)
        
        # Speed label
        self.speed_label = QLabel("Speed: 0 B/s")
        self.speed_label.setObjectName("statusLabel")
        
        # Active downloads label
        self.active_label = QLabel("Active: 0")
        self.active_label.setObjectName("statusLabel")
        
        status_layout.addWidget(self.speed_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.active_label)
        status_layout.addStretch()
        
        status_bar.addPermanentWidget(status_container)
    
    def apply_simplified_theme(self):
        """
        Apply simplified clean dark theme.
        """
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #1e1e2e;
            }
            
            /* Header */
            #header {
                background-color: #2a2a3e;
                border-bottom: 2px solid #4a90e2;
            }
            
            #appTitle {
                color: #ffffff;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #2a2a3e;
                border: none;
                border-bottom: 1px solid #3a3a4e;
                padding: 5px;
                spacing: 5px;
            }
            
            QToolBar::separator {
                background-color: #3a3a4e;
                width: 1px;
                margin: 5px 8px;
            }
            
            QToolBar QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 13px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #3a3a4e;
            }
            
            QToolBar QToolButton:pressed {
                background-color: #4a4a5e;
            }
            
            QToolBar QToolButton#addButton {
                background-color: #4a90e2;
                color: #ffffff;
                font-weight: 600;
            }
            
            QToolBar QToolButton#addButton:hover {
                background-color: #5aa0f2;
            }
            
            QToolBar QToolButton#settingsButton {
                background-color: #3a3a4e;
            }
            
            /* Table */
            #modernTable {
                background-color: #2a2a3e;
                border: none;
                color: #e0e0e0;
                font-size: 13px;
            }
            
            #modernTable::item {
                padding: 10px 6px;
                border: none;
            }
            
            #modernTable::item:selected {
                background-color: #3a4a5e;
            }
            
            #modernTable::item:hover {
                background-color: #323244;
            }
            
            #modernTable::item:alternate {
                background-color: #262636;
            }
            
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #b0b0b0;
                padding: 10px 6px;
                border: none;
                border-bottom: 2px solid #4a90e2;
                font-weight: 600;
                font-size: 12px;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #3a3a4e;
                border-radius: 4px;
                background-color: #1e1e2e;
                text-align: center;
                height: 20px;
                color: #e0e0e0;
                font-weight: 600;
                font-size: 11px;
            }
            
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 3px;
            }
            
            /* Status Bar */
            #modernStatusBar {
                background-color: #1e1e2e;
                border-top: 1px solid #3a3a4e;
                color: #e0e0e0;
            }
            
            #statusLabel {
                color: #b0b0b0;
                font-size: 12px;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background-color: #2a2a3e;
                width: 10px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3a3a4e;
                border-radius: 5px;
                min-height: 25px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a5e;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #2a2a3e;
                height: 10px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #3a3a4e;
                border-radius: 5px;
                min-width: 25px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #4a4a5e;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Context Menu */
            QMenu {
                background-color: #2a2a3e;
                border: 1px solid #3a3a4e;
                border-radius: 6px;
                padding: 5px;
            }
            
            QMenu::item {
                color: #e0e0e0;
                padding: 6px 25px 6px 10px;
                border-radius: 3px;
            }
            
            QMenu::item:selected {
                background-color: #3a4a5e;
            }
            
            QMenu::separator {
                height: 1px;
                background-color: #3a3a4e;
                margin: 4px 6px;
            }
        """)
    
    def show_add_download_dialog(self):
        """Show add download dialog."""
        dialog = AddDownloadDialog(self, self.db_manager)
        if dialog.exec_():
            url, save_path = dialog.get_data()
            self.add_download(url, save_path)
    
    def show_settings_dialog(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self, self.db_manager)
        if dialog.exec_():
            max_concurrent = int(self.db_manager.get_setting('max_concurrent_downloads') or '3')
            self.download_manager.set_max_concurrent(max_concurrent)
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
    
    def add_download(self, url: str, save_path: str):
        """Add a new download."""
        try:
            filename = get_filename_from_url(url)
            filepath = os.path.join(save_path, filename)
            
            if os.path.exists(filepath):
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"File '{filename}' already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Get file size
            filesize = 0
            try:
                response = requests.head(url, timeout=10)
                if 'Content-Length' in response.headers:
                    filesize = int(response.headers['Content-Length'])
            except:
                pass
            
            # Add to database
            download_id = self.db_manager.add_download(url, filename, filepath, filesize)
            
            # Add to download manager with optimized settings
            chunk_size = int(self.db_manager.get_setting('chunk_size') or '8192')
            num_connections = int(self.db_manager.get_setting('num_connections') or '8')
            task = self.download_manager.add_download(download_id, url, filepath, chunk_size, num_connections)
            
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
        """Add download to table."""
        row = self.downloads_table.rowCount()
        self.downloads_table.insertRow(row)
        
        # Filename
        self.downloads_table.setItem(row, 0, QTableWidgetItem(filename))
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        self.downloads_table.setCellWidget(row, 1, progress_bar)
        
        # Size
        size_text = format_bytes(filesize) if filesize > 0 else "Unknown"
        self.downloads_table.setItem(row, 2, QTableWidgetItem(size_text))
        
        # Speed
        self.downloads_table.setItem(row, 3, QTableWidgetItem("0 B/s"))
        
        # Time Left
        self.downloads_table.setItem(row, 4, QTableWidgetItem("--"))
        
        # Status
        self.downloads_table.setItem(row, 5, QTableWidgetItem(status.upper()))
        
        # Date
        date_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.downloads_table.setItem(row, 6, QTableWidgetItem(date_text))
        
        # ID (hidden)
        self.downloads_table.setItem(row, 7, QTableWidgetItem(str(download_id)))
    
    def load_downloads(self):
        """Load downloads from database."""
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
            
            self.downloads_table.setItem(row, 0, QTableWidgetItem(filename))
            
            # Progress
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            if filesize > 0:
                progress = int((downloaded / filesize) * 100)
                progress_bar.setValue(progress)
            self.downloads_table.setCellWidget(row, 1, progress_bar)
            
            # Size
            size_text = format_bytes(filesize) if filesize > 0 else "Unknown"
            self.downloads_table.setItem(row, 2, QTableWidgetItem(size_text))
            
            # Speed & Time
            self.downloads_table.setItem(row, 3, QTableWidgetItem("0 B/s"))
            self.downloads_table.setItem(row, 4, QTableWidgetItem("--"))
            
            # Status
            self.downloads_table.setItem(row, 5, QTableWidgetItem(status.upper()))
            
            # Date
            date_obj = datetime.fromisoformat(download['created_date'])
            date_text = date_obj.strftime("%Y-%m-%d %H:%M")
            self.downloads_table.setItem(row, 6, QTableWidgetItem(date_text))
            
            # ID
            self.downloads_table.setItem(row, 7, QTableWidgetItem(str(download_id)))
            
            # Resume incomplete downloads
            if status in ['downloading', 'paused', 'pending']:
                url = download['url']
                filepath = download['filepath']
                chunk_size = int(self.db_manager.get_setting('chunk_size') or '8192')
                num_connections = int(self.db_manager.get_setting('num_connections') or '8')
                
                task = self.download_manager.add_download(download_id, url, filepath, chunk_size, num_connections)
                task.progress_updated.connect(self.on_progress_updated)
                task.status_changed.connect(self.on_status_changed)
                task.download_completed.connect(self.on_download_completed)
                task.download_failed.connect(self.on_download_failed)
                
                if status == 'paused':
                    task.pause()
    
    def update_table(self):
        """Update table with current download info."""
        total_speed = 0.0
        active_count = 0
        
        for row in range(self.downloads_table.rowCount()):
            download_id_item = self.downloads_table.item(row, 7)
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
                    
                    # Calculate and display time left
                    if speed > 0 and task.total_bytes > 0:
                        eta = calculate_eta(task.downloaded_bytes, task.total_bytes, speed)
                        time_item = self.downloads_table.item(row, 4)
                        if time_item:
                            time_item.setText(eta)
            else:
                # Clear time left for non-active downloads
                time_item = self.downloads_table.item(row, 4)
                if time_item:
                    time_item.setText("--")
        
        # Update status bar
        self.speed_label.setText(f"Speed: {format_speed(total_speed)}")
        self.active_label.setText(f"Active: {active_count}")
    
    @pyqtSlot(int, int, float)
    def on_progress_updated(self, download_id: int, downloaded: int, speed: float):
        """Handle progress update signal."""
        self.db_manager.update_download_progress(download_id, downloaded, speed)
        
        for row in range(self.downloads_table.rowCount()):
            id_item = self.downloads_table.item(row, 7)
            if id_item and int(id_item.text()) == download_id:
                speed_item = self.downloads_table.item(row, 3)
                if speed_item:
                    speed_item.setText(format_speed(speed))
                break
    
    @pyqtSlot(int, str)
    def on_status_changed(self, download_id: int, status: str):
        """Handle status change signal."""
        self.db_manager.update_download_status(download_id, status)
        
        for row in range(self.downloads_table.rowCount()):
            id_item = self.downloads_table.item(row, 7)
            if id_item and int(id_item.text()) == download_id:
                status_item = self.downloads_table.item(row, 5)
                if status_item:
                    status_item.setText(status.upper())
                break
    
    @pyqtSlot(int)
    def on_download_completed(self, download_id: int):
        """Handle download completion signal."""
        download = self.db_manager.get_download(download_id)
        if download:
            filename = download['filename']
            
            if self.db_manager.get_setting('enable_notifications') == 'true':
                QMessageBox.information(
                    self, "Download Complete",
                    f"Download completed: {filename}"
                )
            
            self.statusBar().showMessage(f"✓ Download completed: {filename}")
    
    @pyqtSlot(int, str)
    def on_download_failed(self, download_id: int, error: str):
        """Handle download failure signal."""
        download = self.db_manager.get_download(download_id)
        if download:
            filename = download['filename']
            QMessageBox.warning(
                self, "Download Failed",
                f"Download failed: {filename}\nError: {error}"
            )
    
    def pause_selected(self):
        """Pause selected download."""
        row = self.downloads_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a download to pause.")
            return
        
        download_id = int(self.downloads_table.item(row, 7).text())
        status_item = self.downloads_table.item(row, 5)
        
        if status_item:
            current_status = status_item.text().lower()
            if current_status == 'downloading' or current_status == 'pending':
                self.download_manager.pause_download(download_id)
                self.statusBar().showMessage(f"Download paused")
            else:
                QMessageBox.information(self, "Cannot Pause", f"Cannot pause a download with status: {current_status}")
    
    def resume_selected(self):
        """Resume selected download."""
        row = self.downloads_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a download to resume.")
            return
        
        download_id = int(self.downloads_table.item(row, 7).text())
        status_item = self.downloads_table.item(row, 5)
        
        if status_item:
            current_status = status_item.text().lower()
            if current_status == 'paused' or current_status == 'failed':
                self.download_manager.resume_download(download_id)
                self.statusBar().showMessage(f"Download resumed")
            else:
                QMessageBox.information(self, "Cannot Resume", f"Cannot resume a download with status: {current_status}")
    
    def cancel_selected(self):
        """Cancel selected download."""
        row = self.downloads_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Please select a download to cancel.")
            return
        
        download_id = int(self.downloads_table.item(row, 7).text())
        status_item = self.downloads_table.item(row, 5)
        
        if status_item:
            current_status = status_item.text().lower()
            if current_status in ['completed', 'cancelled']:
                QMessageBox.information(self, "Cannot Cancel", f"Download is already {current_status}.")
                return
        
        reply = QMessageBox.question(
            self, "Cancel Download",
            "Are you sure you want to cancel this download?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download_manager.cancel_download(download_id)
            self.statusBar().showMessage(f"Download cancelled")
    
    def remove_selected(self):
        """Remove selected download from list."""
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 7).text())
        
        reply = QMessageBox.question(
            self, "Remove Download",
            "Remove this download from the list?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download_manager.cancel_download(download_id)
            self.db_manager.delete_download(download_id)
            self.downloads_table.removeRow(row)
    
    def open_download_folder(self):
        """Open download folder of selected item."""
        row = self.downloads_table.currentRow()
        if row < 0:
            return
        
        download_id = int(self.downloads_table.item(row, 7).text())
        download = self.db_manager.get_download(download_id)
        
        if download:
            folder = os.path.dirname(download['filepath'])
            if os.path.exists(folder):
                os.startfile(folder) if os.name == 'nt' else os.system(f'xdg-open "{folder}"')
    
    def show_context_menu(self, position):
        """Show context menu for table."""
        menu = QMenu()
        
        pause_action = menu.addAction("Pause")
        resume_action = menu.addAction("Resume")
        cancel_action = menu.addAction("Cancel")
        menu.addSeparator()
        remove_action = menu.addAction("Remove")
        folder_action = menu.addAction("Open Folder")
        
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
        """Handle window close event."""
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
        
        self.db_manager.close()
        event.accept()