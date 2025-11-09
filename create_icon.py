"""
Create icon.ico for NexusDown application
Run this once to generate the icon file
"""

from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
from PIL import Image
import io

def create_icon():
    """Create application icon and save as .ico file"""
    
    # Create multiple sizes for better quality
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        # Create pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QColor(74, 144, 226))  # Blue
        painter.setPen(Qt.NoPen)
        margin = size // 16
        painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
        
        # Draw inner circle
        painter.setBrush(QColor(255, 255, 255))  # White
        inner_margin = size // 4
        painter.drawEllipse(inner_margin, inner_margin, 
                          size - 2*inner_margin, size - 2*inner_margin)
        
        # Draw download arrow
        painter.setBrush(QColor(74, 144, 226))
        arrow_width = size // 8
        arrow_height = size // 3
        arrow_x = (size - arrow_width) // 2
        arrow_y = (size - arrow_height) // 2
        
        # Arrow shaft
        painter.drawRect(arrow_x, arrow_y, arrow_width, arrow_height * 2 // 3)
        
        # Arrow head (triangle)
        from PyQt5.QtGui import QPolygon
        from PyQt5.QtCore import QPoint
        points = QPolygon([
            QPoint(arrow_x - arrow_width, arrow_y + arrow_height * 2 // 3),
            QPoint(arrow_x + arrow_width * 2, arrow_y + arrow_height * 2 // 3),
            QPoint(arrow_x + arrow_width // 2, arrow_y + arrow_height)
        ])
        painter.drawPolygon(points)
        
        painter.end()
        
        # Convert QPixmap to PIL Image
        # Save to temporary file instead of buffer (compatibility fix)
        temp_png = f'temp_icon_{size}.png'
        pixmap.save(temp_png, "PNG")
        pil_image = Image.open(temp_png)
        images.append(pil_image.copy())
        pil_image.close()
        
        # Clean up temp file
        import os
        os.remove(temp_png)
    
    # Save as .ico with multiple sizes
    images[0].save('icon.ico', format='ICO', sizes=[(img.width, img.height) for img in images])
    print("✓ Icon created successfully: icon.ico")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    create_icon()
    print("\nYou can now run: pyinstaller NexusDown.spec")