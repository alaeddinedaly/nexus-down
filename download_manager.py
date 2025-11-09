"""
Complete Download Manager with Auto-Retry and Resume
====================================================
Fully integrated with database and UI for seamless retry/resume functionality.
"""

import os
import time
import requests
from threading import Thread, Lock
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed

class DownloadTask(QObject):
    """Download task with automatic retry and resume capability."""
    
    # Signals for UI updates
    progress_updated = pyqtSignal(int, int, float)  # download_id, downloaded_bytes, speed
    status_changed = pyqtSignal(int, str)  # download_id, status
    download_completed = pyqtSignal(int)  # download_id
    download_failed = pyqtSignal(int, str)  # download_id, error_message
    retry_attempt = pyqtSignal(int, int, int)  # download_id, attempt, max_attempts
    
    def __init__(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192, 
                 num_connections: int = 8, max_retries: int = 5):
        super().__init__()
        self.download_id = download_id
        self.url = url
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.num_connections = num_connections
        self.max_retries = max_retries
        
        self.is_paused = False
        self.is_cancelled = False
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.thread = None
        self.progress_thread = None
        self.lock = Lock()
        
        # Retry tracking
        self.retry_count = 0
        self.last_error = None
        
        # For resume capability
        self.temp_filepath = filepath + ".idmtemp"
        
        # Session for connection reuse
        self.session = None
        
        # Track if server supports range requests
        self.supports_resume = False
    
    def start(self):
        """Start the download in a separate thread."""
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = Thread(target=self._download, daemon=True)
        self.thread.start()
    
    def pause(self):
        """Pause the download."""
        with self.lock:
            if not self.is_paused and not self.is_cancelled:
                self.is_paused = True
                try:
                    self.status_changed.emit(self.download_id, 'paused')
                except RuntimeError:
                    pass
    
    def resume(self):
        """Resume the download."""
        with self.lock:
            if self.is_paused and not self.is_cancelled:
                self.is_paused = False
                # Reset retry count on manual resume
                self.retry_count = 0
        
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
        """Cancel the download and clean up temp files."""
        with self.lock:
            self.is_cancelled = True
            self.is_paused = False
        
        if self.progress_thread and self.progress_thread.is_alive():
            self.progress_thread.join(timeout=1.0)
        
        if self.session:
            try:
                self.session.close()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # Clean up temp files
        try:
            if os.path.exists(self.temp_filepath):
                os.remove(self.temp_filepath)
            for i in range(self.num_connections):
                part_file = f"{self.temp_filepath}.part{i}"
                if os.path.exists(part_file):
                    os.remove(part_file)
        except Exception as e:
            print(f"Error removing temp file: {e}")
        
        try:
            self.status_changed.emit(self.download_id, 'cancelled')
        except RuntimeError:
            pass
    
    def _should_retry(self) -> bool:
        """Determine if download should be retried."""
        with self.lock:
            if self.is_cancelled or self.is_paused:
                return False
            return self.retry_count < self.max_retries
    
    def _wait_before_retry(self):
        """Wait before retrying with exponential backoff."""
        wait_time = min(2 ** self.retry_count, 60)  # Cap at 60 seconds
        
        for _ in range(int(wait_time * 10)):  # Check every 0.1s for cancellation
            with self.lock:
                if self.is_cancelled:
                    return
            time.sleep(0.1)
    
    def _check_resume_support(self) -> bool:
        """Check if server supports range requests with retry."""
        for attempt in range(3):
            try:
                response = requests.head(self.url, timeout=10, allow_redirects=True)
                
                if 'Accept-Ranges' in response.headers and response.headers['Accept-Ranges'] != 'none':
                    self.supports_resume = True
                
                if 'Content-Length' in response.headers:
                    self.total_bytes = int(response.headers['Content-Length'])
                
                return self.supports_resume
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                else:
                    print(f"Failed to check resume support: {e}")
                    # Try to get content length anyway
                    try:
                        response = requests.get(self.url, stream=True, timeout=10)
                        if 'Content-Length' in response.headers:
                            self.total_bytes = int(response.headers['Content-Length'])
                        response.close()
                    except:
                        pass
                    return False
        return False
    
    def _download_chunk(self, start: int, end: int, part_num: int, retry_count: int = 3) -> bool:
        """Download a specific chunk with retry logic."""
        part_file = f"{self.temp_filepath}.part{part_num}"
        
        # Check if part file already exists and is complete
        if os.path.exists(part_file):
            expected_size = end - start + 1
            actual_size = os.path.getsize(part_file)
            if actual_size >= expected_size:
                # Part already downloaded
                with self.lock:
                    self.downloaded_bytes += actual_size
                return True
        
        for attempt in range(retry_count):
            try:
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=1,
                    pool_maxsize=1,
                    max_retries=0
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
                        with self.lock:
                            if self.is_cancelled:
                                session.close()
                                return False
                        
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
                
            except Exception as e:
                print(f"Error downloading chunk {part_num} (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                else:
                    return False
        
        return False
    
    def _parallel_download(self) -> bool:
        """Download using parallel connections with proper resume support."""
        try:
            # Check for existing merged temp file
            start_byte = 0
            if os.path.exists(self.temp_filepath):
                start_byte = os.path.getsize(self.temp_filepath)
                self.downloaded_bytes = start_byte
            
            if start_byte >= self.total_bytes and self.total_bytes > 0:
                self._finalize_download()
                return True
            
            # Limit connections for HTTPS
            max_connections = min(self.num_connections, 4) if self.url.startswith('https://') else self.num_connections
            
            remaining = self.total_bytes - start_byte
            chunk_size_per_conn = remaining // max_connections
            
            ranges = []
            for i in range(max_connections):
                start = start_byte + (i * chunk_size_per_conn)
                end = start + chunk_size_per_conn - 1 if i < max_connections - 1 else self.total_bytes - 1
                ranges.append((start, end, i))
            
            try:
                self.status_changed.emit(self.download_id, 'downloading')
            except RuntimeError:
                return False
            
            with ThreadPoolExecutor(max_workers=max_connections) as executor:
                futures = {executor.submit(self._download_chunk, start, end, i): i 
                          for start, end, i in ranges}
                
                for future in as_completed(futures):
                    with self.lock:
                        if self.is_cancelled:
                            executor.shutdown(wait=False, cancel_futures=True)
                            return False
                    
                    if not future.result():
                        with self.lock:
                            if not self.is_cancelled:
                                executor.shutdown(wait=False, cancel_futures=True)
                                print("Parallel download chunk failed, falling back to single connection...")
                                return self._single_connection_download()
                        return False
            
            # Merge all parts if not already merged
            if not os.path.exists(self.temp_filepath) or os.path.getsize(self.temp_filepath) < self.total_bytes:
                with open(self.temp_filepath, 'wb') as outfile:
                    for i in range(max_connections):
                        part_file = f"{self.temp_filepath}.part{i}"
                        if os.path.exists(part_file):
                            with open(part_file, 'rb') as infile:
                                outfile.write(infile.read())
                            os.remove(part_file)
            
            with self.lock:
                if self.is_cancelled:
                    return False
            
            self._finalize_download()
            return True
            
        except Exception as e:
            with self.lock:
                if self.is_cancelled:
                    return False
                self.last_error = str(e)
            print(f"Parallel download error: {e}")
            return False
    
    def _single_connection_download(self) -> bool:
        """Download using single connection with automatic resume."""
        try:
            # Check if resuming
            resume_header = {}
            if os.path.exists(self.temp_filepath):
                self.downloaded_bytes = os.path.getsize(self.temp_filepath)
                if self.downloaded_bytes > 0:
                    resume_header = {'Range': f'bytes={self.downloaded_bytes}-'}
            
            response = requests.get(
                self.url, 
                headers=resume_header, 
                stream=True, 
                timeout=30,
                allow_redirects=True
            )
            
            # Handle content length
            if 'Content-Length' in response.headers:
                content_length = int(response.headers['Content-Length'])
                if resume_header:
                    self.total_bytes = self.downloaded_bytes + content_length
                else:
                    self.total_bytes = content_length
            elif 'Content-Range' in response.headers:
                content_range = response.headers['Content-Range']
                self.total_bytes = int(content_range.split('/')[-1])
            
            if response.status_code == 416:  # Range not satisfiable
                if self.downloaded_bytes >= self.total_bytes:
                    self._finalize_download()
                    return True
                else:
                    # Start from beginning
                    self.downloaded_bytes = 0
                    return self._single_connection_download()
            
            mode = 'ab' if self.downloaded_bytes > 0 and resume_header else 'wb'
            buffer_size = max(self.chunk_size, 65536)
            
            with open(self.temp_filepath, mode, buffering=buffer_size) as f:
                try:
                    self.status_changed.emit(self.download_id, 'downloading')
                except RuntimeError:
                    return False
                
                start_time = time.time()
                last_update_time = start_time
                last_downloaded = self.downloaded_bytes
                
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    with self.lock:
                        if self.is_cancelled:
                            return False
                    
                    while self.is_paused:
                        time.sleep(0.1)
                        with self.lock:
                            if self.is_cancelled:
                                return False
                    
                    if chunk:
                        with self.lock:
                            if self.is_cancelled:
                                return False
                        
                        f.write(chunk)
                        self.downloaded_bytes += len(chunk)
                        
                        # Update progress
                        current_time = time.time()
                        if current_time - last_update_time >= 0.5:
                            time_diff = current_time - last_update_time
                            bytes_diff = self.downloaded_bytes - last_downloaded
                            speed = bytes_diff / time_diff if time_diff > 0 else 0
                            
                            try:
                                self.progress_updated.emit(
                                    self.download_id,
                                    self.downloaded_bytes,
                                    speed
                                )
                            except RuntimeError:
                                return False
                            
                            last_update_time = current_time
                            last_downloaded = self.downloaded_bytes
            
            with self.lock:
                if self.is_cancelled:
                    return False
            
            self._finalize_download()
            return True
            
        except requests.exceptions.RequestException as e:
            with self.lock:
                if self.is_cancelled:
                    return False
                self.last_error = str(e)
            print(f"Download error: {e}")
            return False
        except Exception as e:
            with self.lock:
                if self.is_cancelled:
                    return False
                self.last_error = str(e)
            print(f"Unexpected error: {e}")
            return False
    
    def _download(self):
        """Main download method with automatic retry logic."""
        self.session = requests.Session()
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.num_connections,
            pool_maxsize=self.num_connections * 2,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Start progress monitoring
        self.progress_thread = Thread(target=self._monitor_progress, daemon=True)
        self.progress_thread.start()
        
        try:
            while True:
                # Check if cancelled
                with self.lock:
                    if self.is_cancelled:
                        return
                
                # Check resume support
                supports_parallel = self._check_resume_support()
                
                # Determine download strategy
                use_single_connection = (
                    not supports_parallel or 
                    (self.url.startswith('https://') and self.total_bytes > 500 * 1024 * 1024) or
                    self.total_bytes < 1024 * 1024
                )
                
                # Attempt download
                success = False
                if use_single_connection:
                    success = self._single_connection_download()
                else:
                    success = self._parallel_download()
                
                # If successful, break the retry loop
                if success:
                    break
                
                # Check if should retry
                if not self._should_retry():
                    # Max retries reached
                    error_msg = self.last_error or "Download failed after maximum retries"
                    try:
                        self.download_failed.emit(self.download_id, error_msg)
                        self.status_changed.emit(self.download_id, 'failed')
                    except RuntimeError:
                        pass
                    break
                
                # Increment retry count and emit signal
                with self.lock:
                    self.retry_count += 1
                
                try:
                    self.retry_attempt.emit(self.download_id, self.retry_count, self.max_retries)
                    self.status_changed.emit(self.download_id, f'retrying ({self.retry_count}/{self.max_retries})')
                except RuntimeError:
                    break
                
                print(f"Download {self.download_id} failed, retrying {self.retry_count}/{self.max_retries}...")
                
                # Wait before retry
                self._wait_before_retry()
                
        finally:
            # Stop progress monitoring
            with self.lock:
                self.is_cancelled = True
            
            if self.progress_thread:
                self.progress_thread.join(timeout=1.0)
            
            if self.session:
                try:
                    self.session.close()
                except:
                    pass
    
    def _monitor_progress(self):
        """Monitor and emit progress updates continuously."""
        last_update = time.time()
        last_downloaded = self.downloaded_bytes
        
        while True:
            time.sleep(0.3)
            
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
                    break
                
                last_update = current_time
                last_downloaded = current_downloaded
    
    def _finalize_download(self):
        """Finalize download by renaming temp file."""
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
    """Manages multiple concurrent downloads."""
    
    download_added = pyqtSignal(int)
    
    def __init__(self, max_concurrent: int = 3):
        super().__init__()
        self.max_concurrent = max_concurrent
        self.active_downloads = {}
        self.download_queue = []
        self.lock = Lock()
    
    def add_download(self, download_id: int, url: str, filepath: str, chunk_size: int = 8192,
                    num_connections: int = 8, max_retries: int = 5) -> DownloadTask:
        """Add a new download with retry capability."""
        task = DownloadTask(download_id, url, filepath, chunk_size, num_connections, max_retries)
        
        with self.lock:
            self.active_downloads[download_id] = task
        
        task.download_completed.connect(self._on_download_completed)
        task.download_failed.connect(self._on_download_completed)
        
        self._start_next_download()
        self.download_added.emit(download_id)
        
        return task
    
    def _start_next_download(self):
        """Start next download from queue if slot available."""
        with self.lock:
            downloading_count = sum(
                1 for task in self.active_downloads.values()
                if not task.is_paused and not task.is_cancelled and
                (task.thread and task.thread.is_alive())
            )
            
            if downloading_count < self.max_concurrent:
                for download_id, task in list(self.active_downloads.items()):
                    if not task.thread or not task.thread.is_alive():
                        if not task.is_paused and not task.is_cancelled:
                            task.start()
                            downloading_count += 1
                            if downloading_count >= self.max_concurrent:
                                break
    
    def _on_download_completed(self, download_id: int):
        """Callback when download completes or fails."""
        self._start_next_download()
    
    def pause_download(self, download_id: int):
        """Pause a download."""
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        if task:
            task.pause()
            self._start_next_download()
    
    def resume_download(self, download_id: int):
        """Resume a download."""
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        if task:
            task.resume()
    
    def cancel_download(self, download_id: int):
        """Cancel a download."""
        task = None
        with self.lock:
            if download_id in self.active_downloads:
                task = self.active_downloads[download_id]
        
        if task:
            task.cancel()
            
            with self.lock:
                if download_id in self.active_downloads:
                    del self.active_downloads[download_id]
            
            self._start_next_download()
    
    def get_download(self, download_id: int) -> Optional[DownloadTask]:
        """Get download task by ID."""
        with self.lock:
            return self.active_downloads.get(download_id)
    
    def set_max_concurrent(self, max_concurrent: int):
        """Set maximum concurrent downloads."""
        with self.lock:
            self.max_concurrent = max_concurrent
        self._start_next_download()