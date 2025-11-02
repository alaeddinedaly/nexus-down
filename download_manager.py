"""
Download Manager Module
=======================
Handles actual file downloads with multi-threading support,
pause/resume functionality, and progress tracking.
"""

import os
import time
import requests
from threading import Thread, Lock
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal

class DownloadTask(QObject):
    """
    Represents a single download task with pause/resume capability.
    """
    
    # Signals for UI updates
    progress_updated = pyqtSignal(int, int, float)  # download_id, downloaded_bytes, speed
    status_changed = pyqtSignal(int, str)  # download_id, status
    download_completed = pyqtSignal(int)  # download_id
    download_failed = pyqtSignal(int, str)  # download_id, error_message
    
    def __init__(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192):
        """
        Initialize download task.
        
        Args:
            download_id: Unique download identifier
            url: URL to download from
            filepath: Full path where file will be saved
            chunk_size: Size of chunks to download (bytes)
        """
        super().__init__()
        self.download_id = download_id
        self.url = url
        self.filepath = filepath
        self.chunk_size = chunk_size
        
        self.is_paused = False
        self.is_cancelled = False
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.thread = None
        self.lock = Lock()
        
        # For resume capability
        self.temp_filepath = filepath + ".idmtemp"
    
    def start(self):
        """
        Start the download in a separate thread.
        """
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = Thread(target=self._download, daemon=True)
        self.thread.start()
    
    def pause(self):
        """
        Pause the download.
        """
        with self.lock:
            self.is_paused = True
            self.status_changed.emit(self.download_id, 'paused')
    
    def resume(self):
        """
        Resume the download.
        """
        with self.lock:
            self.is_paused = False
        
        # Restart download if thread is not alive
        if not self.thread or not self.thread.is_alive():
            self.status_changed.emit(self.download_id, 'downloading')
            self.start()
    
    def cancel(self):
        """
        Cancel the download.
        """
        with self.lock:
            self.is_cancelled = True
            self.is_paused = False
        
        # Clean up temp file
        if os.path.exists(self.temp_filepath):
            try:
                os.remove(self.temp_filepath)
            except:
                pass
        
        self.status_changed.emit(self.download_id, 'cancelled')
    
    def _download(self):
        """
        Internal method to perform the actual download.
        """
        try:
            # Check if we're resuming a download
            resume_header = {}
            if os.path.exists(self.temp_filepath):
                self.downloaded_bytes = os.path.getsize(self.temp_filepath)
                resume_header = {'Range': f'bytes={self.downloaded_bytes}-'}
            
            # Send request
            response = requests.get(self.url, headers=resume_header, stream=True, timeout=30)
            
            # Get total file size
            if 'Content-Length' in response.headers:
                content_length = int(response.headers['Content-Length'])
                self.total_bytes = self.downloaded_bytes + content_length
            elif 'Content-Range' in response.headers:
                # For resumed downloads
                content_range = response.headers['Content-Range']
                self.total_bytes = int(content_range.split('/')[-1])
            
            # Check if resume is supported
            if response.status_code == 416:  # Range Not Satisfiable
                # File already completely downloaded
                self.downloaded_bytes = self.total_bytes
                self._finalize_download()
                return
            
            # Open file for writing (append mode if resuming)
            mode = 'ab' if self.downloaded_bytes > 0 else 'wb'
            
            with open(self.temp_filepath, mode) as f:
                self.status_changed.emit(self.download_id, 'downloading')
                
                start_time = time.time()
                last_update_time = start_time
                last_downloaded = self.downloaded_bytes
                
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    # Check for cancellation
                    with self.lock:
                        if self.is_cancelled:
                            return
                    
                    # Wait while paused
                    while self.is_paused:
                        time.sleep(0.1)
                        with self.lock:
                            if self.is_cancelled:
                                return
                    
                    if chunk:
                        f.write(chunk)
                        self.downloaded_bytes += len(chunk)
                        
                        # Update progress every 0.5 seconds
                        current_time = time.time()
                        if current_time - last_update_time >= 0.5:
                            time_diff = current_time - last_update_time
                            bytes_diff = self.downloaded_bytes - last_downloaded
                            speed = bytes_diff / time_diff if time_diff > 0 else 0
                            
                            self.progress_updated.emit(
                                self.download_id,
                                self.downloaded_bytes,
                                speed
                            )
                            
                            last_update_time = current_time
                            last_downloaded = self.downloaded_bytes
            
            # Download completed successfully
            self._finalize_download()
            
        except requests.exceptions.RequestException as e:
            self.download_failed.emit(self.download_id, str(e))
            self.status_changed.emit(self.download_id, 'failed')
        except Exception as e:
            self.download_failed.emit(self.download_id, str(e))
            self.status_changed.emit(self.download_id, 'failed')
    
    def _finalize_download(self):
        """
        Finalize download by renaming temp file to final filename.
        """
        try:
            # Rename temp file to actual file
            if os.path.exists(self.temp_filepath):
                if os.path.exists(self.filepath):
                    os.remove(self.filepath)
                os.rename(self.temp_filepath, self.filepath)
            
            self.status_changed.emit(self.download_id, 'completed')
            self.download_completed.emit(self.download_id)
        except Exception as e:
            self.download_failed.emit(self.download_id, f"Failed to finalize: {str(e)}")
            self.status_changed.emit(self.download_id, 'failed')


class DownloadManager(QObject):
    """
    Manages multiple concurrent downloads.
    """
    
    # Signals
    download_added = pyqtSignal(int)  # download_id
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize download manager.
        
        Args:
            max_concurrent: Maximum number of concurrent downloads
        """
        super().__init__()
        self.max_concurrent = max_concurrent
        self.active_downloads = {}  # download_id -> DownloadTask
        self.download_queue = []  # List of download_ids waiting to start
        self.lock = Lock()
    
    def add_download(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192) -> DownloadTask:
        """
        Add a new download.
        
        Args:
            download_id: Unique download identifier
            url: URL to download from
            filepath: Full path where file will be saved
            chunk_size: Size of chunks to download (bytes)
            
        Returns:
            DownloadTask object
        """
        task = DownloadTask(download_id, url, filepath, chunk_size)
        
        with self.lock:
            self.active_downloads[download_id] = task
        
        # Connect completion signal to check queue
        task.download_completed.connect(self._on_download_completed)
        task.download_failed.connect(self._on_download_completed)
        
        self._start_next_download()
        self.download_added.emit(download_id)
        
        return task
    
    def _start_next_download(self):
        """
        Start next download from queue if slot available.
        """
        with self.lock:
            # Count currently downloading tasks
            downloading_count = sum(
                1 for task in self.active_downloads.values()
                if not task.is_paused and not task.is_cancelled and
                (task.thread and task.thread.is_alive())
            )
            
            # Start pending downloads up to max concurrent limit
            if downloading_count < self.max_concurrent:
                for download_id, task in self.active_downloads.items():
                    if not task.thread or not task.thread.is_alive():
                        if not task.is_paused and not task.is_cancelled:
                            task.start()
                            downloading_count += 1
                            if downloading_count >= self.max_concurrent:
                                break
    
    def _on_download_completed(self, download_id: int):
        """
        Callback when a download completes or fails.
        
        Args:
            download_id: Download ID
        """
        self._start_next_download()
    
    def pause_download(self, download_id: int):
        """
        Pause a download.
        
        Args:
            download_id: Download ID
        """
        with self.lock:
            if download_id in self.active_downloads:
                self.active_downloads[download_id].pause()
                self._start_next_download()
    
    def resume_download(self, download_id: int):
        """
        Resume a download.
        
        Args:
            download_id: Download ID
        """
        with self.lock:
            if download_id in self.active_downloads:
                self.active_downloads[download_id].resume()
    
    def cancel_download(self, download_id: int):
        """
        Cancel a download.
        
        Args:
            download_id: Download ID
        """
        with self.lock:
            if download_id in self.active_downloads:
                self.active_downloads[download_id].cancel()
                del self.active_downloads[download_id]
                self._start_next_download()
    
    def get_download(self, download_id: int) -> Optional[DownloadTask]:
        """
        Get download task by ID.
        
        Args:
            download_id: Download ID
            
        Returns:
            DownloadTask or None
        """
        with self.lock:
            return self.active_downloads.get(download_id)
    
    def set_max_concurrent(self, max_concurrent: int):
        """
        Set maximum concurrent downloads.
        
        Args:
            max_concurrent: Maximum number of concurrent downloads
        """
        with self.lock:
            self.max_concurrent = max_concurrent
        self._start_next_download()