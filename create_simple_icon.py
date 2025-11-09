"""
Create a simple icon.ico without Pillow dependency
Uses only PyQt5 to create a basic ICO file
"""

from PyQt5.QtGui import QPixmap, QPainter, QColor, QPolygon, QImage
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication
import sys
import struct

def create_simple_icon():
    """Create a simple icon.ico file using only PyQt5"""
    
    # Create application (required for QPixmap)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a 256x256 icon
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background circle (blue)
    painter.setBrush(QColor(74, 144, 226))
    painter.setPen(Qt.NoPen)
    margin = size // 16
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
    
    # Draw inner circle (white)
    painter.setBrush(QColor(255, 255, 255))
    inner_margin = size // 4
    painter.drawEllipse(inner_margin, inner_margin, 
                       size - 2*inner_margin, size - 2*inner_margin)
    
    # Draw download arrow (blue)
    painter.setBrush(QColor(74, 144, 226))
    arrow_width = size // 8
    arrow_height = size // 3
    arrow_x = (size - arrow_width) // 2
    arrow_y = (size - arrow_height) // 2
    
    # Arrow shaft
    painter.drawRect(arrow_x, arrow_y, arrow_width, arrow_height * 2 // 3)
    
    # Arrow head (triangle)
    points = QPolygon([
        QPoint(arrow_x - arrow_width, arrow_y + arrow_height * 2 // 3),
        QPoint(arrow_x + arrow_width * 2, arrow_y + arrow_height * 2 // 3),
        QPoint(arrow_x + arrow_width // 2, arrow_y + arrow_height)
    ])
    painter.drawPolygon(points)
    
    painter.end()
    
    # Convert to QImage
    image = pixmap.toImage()
    
    # Save directly as PNG first (for testing)
    pixmap.save('icon_temp.png', 'PNG')
    
    # Create ICO file manually with multiple sizes
    sizes_to_create = [256, 128, 64, 48, 32, 16]
    
    with open('icon.ico', 'wb') as ico_file:
        # ICO header
        ico_file.write(struct.pack('<HHH', 0, 1, len(sizes_to_create)))  # Reserved, Type, Count
        
        offset = 6 + (16 * len(sizes_to_create))  # Header + directory entries
        
        # Directory entries
        for icon_size in sizes_to_create:
            # Create scaled pixmap
            scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled_image = scaled_pixmap.toImage()
            
            # Convert to 32-bit RGBA
            scaled_image = scaled_image.convertToFormat(QImage.Format_RGBA8888)
            
            # Calculate size
            width = scaled_image.width()
            height = scaled_image.height()
            
            # Create BMP data
            bmp_data = bytearray()
            
            # BMP Info Header (40 bytes)
            bmp_data.extend(struct.pack('<I', 40))  # Header size
            bmp_data.extend(struct.pack('<i', width))  # Width
            bmp_data.extend(struct.pack('<i', height * 2))  # Height (doubled for ICO)
            bmp_data.extend(struct.pack('<H', 1))  # Planes
            bmp_data.extend(struct.pack('<H', 32))  # Bits per pixel
            bmp_data.extend(struct.pack('<I', 0))  # Compression
            bmp_data.extend(struct.pack('<I', width * height * 4))  # Image size
            bmp_data.extend(struct.pack('<i', 0))  # X pixels per meter
            bmp_data.extend(struct.pack('<i', 0))  # Y pixels per meter
            bmp_data.extend(struct.pack('<I', 0))  # Colors used
            bmp_data.extend(struct.pack('<I', 0))  # Important colors
            
            # Pixel data (bottom-up, BGRA format)
            for y in range(height - 1, -1, -1):
                for x in range(width):
                    pixel = scaled_image.pixel(x, y)
                    b = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    r = pixel & 0xFF
                    a = (pixel >> 24) & 0xFF
                    bmp_data.extend([b, g, r, a])
            
            # AND mask (all zeros for 32-bit images with alpha)
            and_mask = bytes(((width + 31) // 32 * 4) * height)
            bmp_data.extend(and_mask)
            
            size_bytes = len(bmp_data)
            
            # Write directory entry
            w = width if width < 256 else 0
            h = height if height < 256 else 0
            ico_file.write(struct.pack('<BBBBHHII', 
                w, h,  # Width, Height
                0,  # Color palette
                0,  # Reserved
                1,  # Color planes
                32,  # Bits per pixel
                size_bytes,  # Size of image data
                offset  # Offset to image data
            ))
            
            offset += size_bytes
        
        # Write image data for each size
        for icon_size in sizes_to_create:
            scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled_image = scaled_pixmap.toImage()
            scaled_image = scaled_image.convertToFormat(QImage.Format_RGBA8888)
            
            width = scaled_image.width()
            height = scaled_image.height()
            
            # BMP Info Header
            ico_file.write(struct.pack('<I', 40))
            ico_file.write(struct.pack('<i', width))
            ico_file.write(struct.pack('<i', height * 2))
            ico_file.write(struct.pack('<H', 1))
            ico_file.write(struct.pack('<H', 32))
            ico_file.write(struct.pack('<I', 0))
            ico_file.write(struct.pack('<I', width * height * 4))
            ico_file.write(struct.pack('<i', 0))
            ico_file.write(struct.pack('<i', 0))
            ico_file.write(struct.pack('<I', 0))
            ico_file.write(struct.pack('<I', 0))
            
            # Pixel data
            for y in range(height - 1, -1, -1):
                for x in range(width):
                    pixel = scaled_image.pixel(x, y)
                    b = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    r = pixel & 0xFF
                    a = (pixel >> 24) & 0xFF
                    ico_file.write(bytes([b, g, r, a]))
            
            # AND mask
            and_mask = bytes(((width + 31) // 32 * 4) * height)
            ico_file.write(and_mask)
    
    print("✓ Icon created successfully: icon.ico")
    print("✓ Preview saved: icon_temp.png")
    
    # Clean up
    import os
    try:
        os.remove('icon_temp.png')
    except:
        pass

if __name__ == "__main__":
    try:
        create_simple_icon()
        print("\nYou can now run: pyinstaller NexusDown.spec")
    except Exception as e:
        print(f"Error creating icon: {e}")
        print("\nYou can continue without an icon by removing the 'icon=' line from NexusDown.spec")