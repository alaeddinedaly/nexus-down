# utils.py




"""
Utility Functions Module
========================
Contains helper functions for formatting, file operations, etc.
"""

import os
from urllib.parse import urlparse, unquote


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if bytes_value < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_speed(bytes_per_second: float) -> str:
    """
    Format download speed to human-readable string.
    
    Args:
        bytes_per_second: Speed in bytes per second
        
    Returns:
        Formatted string (e.g., "1.5 MB/s")
    """
    return format_bytes(int(bytes_per_second)) + "/s"


def get_filename_from_url(url: str) -> str:
    """
    Extract filename from URL.
    
    Args:
        url: Download URL
        
    Returns:
        Filename extracted from URL
    """
    # Parse URL
    parsed = urlparse(url)
    
    # Get path component
    path = unquote(parsed.path)
    
    # Extract filename
    filename = os.path.basename(path)
    
    # If no filename found, generate one
    if not filename or '.' not in filename:
        filename = f"download_{hash(url) % 1000000}"
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (e.g., ".pdf")
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def ensure_unique_filename(filepath: str) -> str:
    """
    Ensure filename is unique by adding number suffix if needed.
    
    Args:
        filepath: Full path to file
        
    Returns:
        Unique filepath
    """
    if not os.path.exists(filepath):
        return filepath
    
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_filename = f"{name} ({counter}){ext}"
        new_filepath = os.path.join(directory, new_filename)
        
        if not os.path.exists(new_filepath):
            return new_filepath
        
        counter += 1


def calculate_eta(downloaded: int, total: int, speed: float) -> str:
    """
    Calculate estimated time to completion.
    
    Args:
        downloaded: Bytes downloaded
        total: Total bytes
        speed: Current speed in bytes/second
        
    Returns:
        Formatted ETA string (e.g., "5m 30s")
    """
    if speed <= 0 or total <= 0:
        return "Unknown"
    
    remaining = total - downloaded
    seconds = int(remaining / speed)
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"