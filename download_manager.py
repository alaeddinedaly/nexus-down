# download_manager.py

"""
Download Manager Module
=======================
Handles actual file downloads with multi-threading support,
pause/resume functionality, and progress tracking.
Optimized for maximum download speed with SSL error handling.
"""

import os
import time
import requests
from threading import Thread, Lock
from typing import Callable, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed

class DownloadTask(QObject):
    """
    Represents a single download task with pause/resume capability.
    Optimized for maximum speed using chunked parallel downloads.
    """
    
    # Signals for UI updates
    progress_updated = pyqtSignal(int, int, float)  # download_id, downloaded_bytes, speed
    status_changed = pyqtSignal(int, str)  # download_id, status
    download_completed = pyqtSignal(int)  # download_id
    download_failed = pyqtSignal(int, str)  # download_id, error_message
    
    def __init__(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192, 
                 num_connections: int = 8):
        """
        Initialize download task.
        
        Args:
            download_id: Unique download identifier
            url: URL to download from
            filepath: Full path where file will be saved
            chunk_size: Size of chunks to download (bytes)
            num_connections: Number of parallel connections (default 8 for max speed)
        """
        super().__init__()
        self.download_id = download_id
        self.url = url
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.num_connections = num_connections
        
        self.is_paused = False
        self.is_cancelled = False
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.thread = None
        self.progress_thread = None
        self.lock = Lock()
        
        # For resume capability
        self.temp_filepath = filepath + ".idmtemp"
        
        # Session for connection reuse
        self.session = None
        
        # Track if server supports range requests
        self.supports_resume = False
    
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
            if not self.is_paused and not self.is_cancelled:
                self.is_paused = True
                try:
                    self.status_changed.emit(self.download_id, 'paused')
                except RuntimeError:
                    pass
    
    def resume(self):
        """
        Resume the download.
        """
        with self.lock:
            if self.is_paused and not self.is_cancelled:
                self.is_paused = False
        
        # Restart download if thread is not alive
        if not self.thread or not self.thread.is_alive():
            try:
                self.status_changed.emit(self.download_id, 'downloading')
            except RuntimeError:
                pass
            self.start()
        else:
            try:
                self.status_changed.emit(self.download_id, 'downloading')
            except RuntimeError:
                pass
    
    def cancel(self):
        """
        Cancel the download.
        """
        with self.lock:
            self.is_cancelled = True
            self.is_paused = False
        
        # Wait for progress thread to finish
        if self.progress_thread and self.progress_thread.is_alive():
            self.progress_thread.join(timeout=1.0)
        
        # Close session if exists
        if self.session:
            try:
                self.session.close()
            except:
                pass
        
        # Wait for thread to finish with timeout
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # Clean up temp file
        try:
            if os.path.exists(self.temp_filepath):
                os.remove(self.temp_filepath)
            # Clean up part files
            for i in range(self.num_connections):
                part_file = f"{self.temp_filepath}.part{i}"
                if os.path.exists(part_file):
                    os.remove(part_file)
        except Exception as e:
            print(f"Error removing temp file: {e}")
        
        self.status_changed.emit(self.download_id, 'cancelled')
    
    def _check_resume_support(self):
        """
        Check if server supports range requests (parallel downloads).
        """
        try:
            response = requests.head(self.url, timeout=10, allow_redirects=True)
            
            # Check for Accept-Ranges header
            if 'Accept-Ranges' in response.headers and response.headers['Accept-Ranges'] != 'none':
                self.supports_resume = True
            
            # Get total file size
            if 'Content-Length' in response.headers:
                self.total_bytes = int(response.headers['Content-Length'])
            
            return self.supports_resume
        except:
            return False
    
    def _download_chunk(self, start: int, end: int, part_num: int, progress_callback, retry_count: int = 3) -> bool:
        """
        Download a specific chunk of the file with retry logic.
        
        Args:
            start: Start byte position
            end: End byte position
            part_num: Part number for temp file
            progress_callback: Callback to update progress
            retry_count: Number of retries on failure
            
        Returns:
            True if successful, False otherwise
        """
        part_file = f"{self.temp_filepath}.part{part_num}"
        
        for attempt in range(retry_count):
            try:
                # Create a new session for this chunk to avoid SSL issues
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=1,
                    pool_maxsize=1,
                    max_retries=0  # We handle retries manually
                )
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                
                headers = {'Range': f'bytes={start}-{end}'}
                response = session.get(self.url, headers=headers, stream=True, timeout=30)
                
                if response.status_code not in [200, 206]:
                    session.close()
                    if attempt < retry_count - 1:
                        time.sleep(1)
                        continue
                    return False
                
                with open(part_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        # Check for cancellation
                        with self.lock:
                            if self.is_cancelled:
                                session.close()
                                return False
                        
                        # Wait while paused
                        while self.is_paused:
                            time.sleep(0.1)
                            with self.lock:
                                if self.is_cancelled:
                                    session.close()
                                    return False
                        
                        if chunk:
                            f.write(chunk)
                            
                            with self.lock:
                                self.downloaded_bytes += len(chunk)
                
                session.close()
                return True
                
            except RuntimeError:
                # Object deleted
                return False
            except Exception as e:
                print(f"Error downloading chunk {part_num} (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)  # Wait before retry
                else:
                    return False
        
        return False
    
    def _parallel_download(self):
        """
        Download file using multiple parallel connections for maximum speed.
        Uses better error handling and connection management.
        """
        try:
            # Check if resuming
            start_byte = 0
            if os.path.exists(self.temp_filepath):
                start_byte = os.path.getsize(self.temp_filepath)
                self.downloaded_bytes = start_byte
            
            if start_byte >= self.total_bytes:
                self._finalize_download()
                return
            
            # Limit connections for HTTPS to avoid SSL issues
            max_connections = min(self.num_connections, 4) if self.url.startswith('https://') else self.num_connections
            
            # Calculate chunk size per connection
            remaining = self.total_bytes - start_byte
            chunk_size = remaining // max_connections
            
            # Create download ranges
            ranges = []
            for i in range(max_connections):
                start = start_byte + (i * chunk_size)
                end = start + chunk_size - 1 if i < max_connections - 1 else self.total_bytes - 1
                ranges.append((start, end, i))
            
            try:
                self.status_changed.emit(self.download_id, 'downloading')
            except RuntimeError:
                return
            
            # Download chunks in parallel with reduced worker count
            with ThreadPoolExecutor(max_workers=max_connections) as executor:
                futures = {executor.submit(self._download_chunk, start, end, i, None): i 
                          for start, end, i in ranges}
                
                for future in as_completed(futures):
                    # Check for cancellation
                    with self.lock:
                        if self.is_cancelled:
                            executor.shutdown(wait=False, cancel_futures=True)
                            return
                    
                    if not future.result():
                        # Don't raise exception if cancelled
                        with self.lock:
                            if not self.is_cancelled:
                                # Try falling back to single connection download
                                print("Parallel download failed, falling back to single connection...")
                                executor.shutdown(wait=False, cancel_futures=True)
                                self._single_connection_download()
                                return
                        return
            
            # Merge all parts into single file
            with open(self.temp_filepath, 'wb') as outfile:
                for i in range(max_connections):
                    part_file = f"{self.temp_filepath}.part{i}"
                    if os.path.exists(part_file):
                        with open(part_file, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(part_file)
            
            # Check for cancellation before finalizing
            with self.lock:
                if self.is_cancelled:
                    return
            
            self._finalize_download()
            
        except RuntimeError:
            # Object deleted, just return
            return
        except Exception as e:
            with self.lock:
                if not self.is_cancelled:
                    print(f"Parallel download error: {e}")
                    # Try falling back to single connection
                    try:
                        self._single_connection_download()
                    except:
                        try:
                            self.download_failed.emit(self.download_id, str(e))
                            self.status_changed.emit(self.download_id, 'failed')
                        except RuntimeError:
                            pass
    
    def _single_connection_download(self):
        """
        Fallback: Download using single connection (for servers that don't support ranges).
        """
        try:
            # Check if resuming
            resume_header = {}
            if os.path.exists(self.temp_filepath):
                self.downloaded_bytes = os.path.getsize(self.temp_filepath)
                resume_header = {'Range': f'bytes={self.downloaded_bytes}-'}
            
            # Send request with optimized settings
            response = requests.get(
                self.url, 
                headers=resume_header, 
                stream=True, 
                timeout=30,
                # Optimize for speed
                allow_redirects=True
            )
            
            # Get total file size
            if 'Content-Length' in response.headers:
                content_length = int(response.headers['Content-Length'])
                self.total_bytes = self.downloaded_bytes + content_length
            elif 'Content-Range' in response.headers:
                content_range = response.headers['Content-Range']
                self.total_bytes = int(content_range.split('/')[-1])
            
            if response.status_code == 416:
                self.downloaded_bytes = self.total_bytes
                self._finalize_download()
                return
            
            # Open file for writing
            mode = 'ab' if self.downloaded_bytes > 0 else 'wb'
            
            # Use larger buffer for better performance
            buffer_size = max(self.chunk_size, 65536)  # At least 64KB
            
            with open(self.temp_filepath, mode, buffering=buffer_size) as f:
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
                        with self.lock:
                            if self.is_cancelled:
                                return
                        
                        f.write(chunk)
                        self.downloaded_bytes += len(chunk)
                        
                        # Update progress
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
            
            with self.lock:
                if self.is_cancelled:
                    return
            
            self._finalize_download()
            
        except requests.exceptions.RequestException as e:
            with self.lock:
                if not self.is_cancelled:
                    self.download_failed.emit(self.download_id, str(e))
                    self.status_changed.emit(self.download_id, 'failed')
        except Exception as e:
            with self.lock:
                if not self.is_cancelled:
                    self.download_failed.emit(self.download_id, str(e))
                    self.status_changed.emit(self.download_id, 'failed')
    
    def _download(self):
        """
        Internal method to perform the actual download.
        Uses adaptive strategy based on file size and protocol.
        """
        self.session = requests.Session()
        
        # Configure session for optimal performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.num_connections,
            pool_maxsize=self.num_connections * 2,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Start progress monitoring thread
        self.progress_thread = Thread(target=self._monitor_progress, daemon=True)
        self.progress_thread.start()
        
        try:
            # Check if server supports parallel downloads
            supports_parallel = self._check_resume_support()
            
            # Use single connection for HTTPS files > 500MB to avoid SSL issues
            # Or if server doesn't support ranges
            use_single_connection = (
                not supports_parallel or 
                (self.url.startswith('https://') and self.total_bytes > 500 * 1024 * 1024)
            )
            
            if use_single_connection or self.total_bytes < 1024 * 1024:
                # Single connection for small files or when parallel isn't supported
                self._single_connection_download()
            else:
                # Use parallel download for better speed
                self._parallel_download()
                
        finally:
            # Stop progress monitoring
            with self.lock:
                self.is_cancelled = True  # Signal to stop progress thread
            
            if self.progress_thread:
                self.progress_thread.join(timeout=1.0)
            
            if self.session:
                try:
                    self.session.close()
                except:
                    pass
    
    def _monitor_progress(self):
        """
        Monitor and emit progress updates continuously.
        """
        last_update = time.time()
        last_downloaded = self.downloaded_bytes
        
        while True:
            time.sleep(0.3)  # Update every 300ms
            
            with self.lock:
                if self.is_cancelled:
                    break
                
                current_downloaded = self.downloaded_bytes
                is_paused = self.is_paused
            
            if is_paused:
                continue
            
            current_time = time.time()
            time_diff = current_time - last_update
            bytes_diff = current_downloaded - last_downloaded
            
            if time_diff > 0:
                speed = bytes_diff / time_diff
                
                try:
                    self.progress_updated.emit(
                        self.download_id,
                        current_downloaded,
                        speed
                    )
                except RuntimeError:
                    # Object deleted, stop monitoring
                    break
                
                last_update = current_time
                last_downloaded = current_downloaded
    
    def _finalize_download(self):
        """
        Finalize download by renaming temp file to final filename.
        """
        try:
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
    
    def add_download(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192,
                    num_connections: int = 8) -> DownloadTask:
        """
        Add a new download.
        
        Args:
            download_id: Unique download identifier
            url: URL to download from
            filepath: Full path where file will be saved
            chunk_size: Size of chunks to download (bytes)
            num_connections: Number of parallel connections for speed
            
        Returns:
            DownloadTask object
        """
        task = DownloadTask(download_id, url, filepath, chunk_size, num_connections)
        
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
                for download_id, task in list(self.active_downloads.items()):
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
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        if task:
            task.pause()
            self._start_next_download()
    
    def resume_download(self, download_id: int):
        """
        Resume a download.
        
        Args:
            download_id: Download ID
        """
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        if task:
            task.resume()
    
    def cancel_download(self, download_id: int):
        """
        Cancel a download.
        
        Args:
            download_id: Download ID
        """
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        # Cancel outside the lock to avoid deadlock
        if task:
            task.cancel()
            
            # Remove from active downloads after cancellation
            with self.lock:
                if download_id in self.active_downloads:
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