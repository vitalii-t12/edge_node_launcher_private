"""
Application icons embedded as strings to avoid path resolution issues
when running as a packaged application.
"""
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtSvg import QSvgRenderer


# Copy icon SVG content
COPY_ICON_SVG = '''
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e8eaed">
    <path d="M360-240q-33 0-56.5-23.5T280-320v-480q0-33 23.5-56.5T360-880h360q33 0 56.5 23.5T800-800v480q0 33-23.5 56.5T720-240H360Zm0-80h360v-480H360v480ZM200-80q-33 0-56.5-23.5T120-160v-560h80v560h440v80H200Zm160-240v-480 480Z"/>
</svg>
'''


def get_copy_icon(is_light_theme=False):
    """
    Returns a QIcon for the copy button with appropriate color based on theme.
    
    Args:
        is_light_theme (bool): Whether to use light theme colors (dark icon)
    
    Returns:
        QIcon: Icon configured for the current theme
    """
    # Modify SVG fill color based on theme
    if is_light_theme:
        # Use black fill for light theme
        modified_svg = COPY_ICON_SVG.replace('fill="#e8eaed"', 'fill="#000000"')
    else:
        # Use light gray fill for dark theme
        modified_svg = COPY_ICON_SVG
    
    # Create renderer with the SVG content
    renderer = QSvgRenderer()
    renderer.load(bytes(modified_svg, 'utf-8'))
    
    # Render to pixmap
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    # Return icon
    return QIcon(pixmap)


def apply_copy_icons_to_buttons(buttons, is_light_theme=False, icon_size=(20, 20)):
    """
    Apply copy icons to multiple buttons.
    
    Args:
        buttons (list): List of QPushButton objects to apply the icon to
        is_light_theme (bool): Whether to use light theme colors
        icon_size (tuple): Width and height of the icon
    """
    icon = get_copy_icon(is_light_theme)
    qsize = QSize(*icon_size)
    
    for button in buttons:
        button.setIcon(icon)
        button.setIconSize(qsize) 