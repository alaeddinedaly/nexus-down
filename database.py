# database.py

"""
Database Manager Module
=======================
Handles all SQLite database operations for storing download history,
settings, and metadata.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    """
    Manages SQLite database operations for the download manager.
    """
    
    def __init__(self, db_path: str = "idm_database.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create database connection.
        
        Returns:
            SQLite connection object
        """
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def initialize_database(self):
        """
        Create necessary tables if they don't exist.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Downloads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                filesize INTEGER DEFAULT 0,
                downloaded INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_date TEXT NOT NULL,
                completed_date TEXT,
                speed REAL DEFAULT 0.0
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Initialize default settings if not exists
        default_settings = {
            'max_concurrent_downloads': '3',
            'default_download_folder': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'theme': 'dark',
            'enable_notifications': 'true',
            'chunk_size': '8192',
            'num_connections': '8',  # Number of parallel connections for speed
            'force_single_https': 'true'  # Force single connection for large HTTPS files to avoid SSL errors
        }
        
        for key, value in default_settings.items():
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
        
        conn.commit()
    
    def add_download(self, url: str, filename: str, filepath: str, filesize: int = 0) -> int:
        """
        Add a new download to the database.
        
        Args:
            url: Download URL
            filename: Name of the file
            filepath: Full path where file will be saved
            filesize: Total file size in bytes
            
        Returns:
            Download ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        created_date = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO downloads (url, filename, filepath, filesize, status, created_date)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (url, filename, filepath, filesize, created_date))
        
        conn.commit()
        return cursor.lastrowid
    
    def update_download_progress(self, download_id: int, downloaded: int, speed: float):
        """
        Update download progress.
        
        Args:
            download_id: Download ID
            downloaded: Bytes downloaded so far
            speed: Current download speed in bytes/sec
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE downloads SET downloaded = ?, speed = ? WHERE id = ?
        """, (downloaded, speed, download_id))
        
        conn.commit()
    
    def update_download_status(self, download_id: int, status: str):
        """
        Update download status.
        
        Args:
            download_id: Download ID
            status: New status (pending, downloading, paused, completed, failed, cancelled)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        completed_date = None
        if status == 'completed':
            completed_date = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE downloads SET status = ?, completed_date = ? WHERE id = ?
        """, (status, completed_date, download_id))
        
        conn.commit()
    
    def get_download(self, download_id: int) -> Optional[Dict]:
        """
        Get download by ID.
        
        Args:
            download_id: Download ID
            
        Returns:
            Download data as dictionary or None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM downloads WHERE id = ?", (download_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def get_all_downloads(self) -> List[Dict]:
        """
        Get all downloads.
        
        Returns:
            List of download dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM downloads ORDER BY created_date DESC")
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def delete_download(self, download_id: int):
        """
        Delete a download from database.
        
        Args:
            download_id: Download ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
        conn.commit()
    
    def get_setting(self, key: str) -> Optional[str]:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            
        Returns:
            Setting value or None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        return row['value'] if row else None
    
    def set_setting(self, key: str, value: str):
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        
        conn.commit()
    
    def close(self):
        """
        Close database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None