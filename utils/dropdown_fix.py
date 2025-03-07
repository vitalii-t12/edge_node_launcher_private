"""
Dropdown styling utilities to fix white background issues in dropdown menus.
This module provides functions to apply styling to QComboBox dropdowns for both dark and light themes.
"""

from PyQt5.QtWidgets import QComboBox, QProxyStyle
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QColor, QPalette

class ComboBoxStyle(QProxyStyle):
    """
    Custom style for QComboBox to fix dropdown background issues.
    """
    def __init__(self, is_dark=True):
        super().__init__()
        self.is_dark = is_dark
        
    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QProxyStyle.SH_ComboBox_Popup:
            return 0
        return super().styleHint(hint, option, widget, returnData)
    
    def subControlRect(self, control, option, subControl, widget=None):
        rect = super().subControlRect(control, option, subControl, widget)
        if control == QProxyStyle.CC_ComboBox and widget and widget.property("class") == "centered-text-combo":
            if subControl == QProxyStyle.SC_ComboBoxEditField:
                # Make the edit field take up more space for text centering
                rect.setLeft(rect.left() + 5)
                rect.setRight(rect.right() - 30)  # Allow space for dropdown arrow
            elif subControl == QProxyStyle.SC_ComboBoxArrow:
                # Position the arrow on the right
                rect.setLeft(rect.right() - 25)
        return rect
        
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QProxyStyle.PE_PanelItemViewItem:
            if option.state & QProxyStyle.State_Selected:
                # Custom selection color
                painter.fillRect(option.rect, QColor("#4A6591" if self.is_dark else "#87CEFA"))
            elif option.state & QProxyStyle.State_MouseOver:
                # Custom hover color
                painter.fillRect(option.rect, QColor("#2A3450" if self.is_dark else "#E6F2FF"))
            else:
                # Base item color (match theme background)
                painter.fillRect(option.rect, QColor("#1A2433" if self.is_dark else "#F0F8FF"))
            return
        super().drawPrimitive(element, option, painter, widget)
    
    def drawControl(self, element, option, painter, widget=None):
        if element == QProxyStyle.CE_ComboBoxLabel and widget and widget.property("class") == "centered-text-combo":
            if not widget.lineEdit():
                # Custom drawing for the combo box text to center it
                painter.save()
                painter.setPen(QColor("white" if self.is_dark else "black"))
                
                # Calculate text rectangle with proper horizontal centering
                text_rect = option.rect
                text_rect.setLeft(text_rect.left() + 20)  # Add left margin
                text_rect.setRight(text_rect.right() - 30)  # Add right margin for arrow
                
                # Draw the text centered
                text = widget.currentText()
                painter.drawText(text_rect, Qt.AlignCenter, text)
                painter.restore()
                return
        super().drawControl(element, option, painter, widget)
        
    def set_dark_mode(self, is_dark):
        self.is_dark = is_dark

class ComboEventFilter(QObject):
    """
    Event filter for QComboBox to ensure dropdown styling is applied on popup.
    """
    def __init__(self, parent, combo_style, is_dark_callback):
        super().__init__(parent)
        self.combo_style = combo_style
        self.is_dark_callback = is_dark_callback
        self.combo_box = parent
        
        # Connect to model changes to center new items
        self.combo_box.model().rowsInserted.connect(self._center_items)
        self.combo_box.currentIndexChanged.connect(self._update_text_centering)
        
    def _center_items(self):
        """Center all items in the combobox."""
        for i in range(self.combo_box.count()):
            self.combo_box.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
    
    def _update_text_centering(self, index):
        """Update text centering after selection changes."""
        # Force style refresh to update the centered text
        self.combo_box.update()
        
    def eventFilter(self, obj, event):
        # Handle dropdown showing
        if event.type() == QEvent.MouseButtonPress:
            # Center items first
            self._center_items()
            
            # When the user clicks on the combobox, ensure style is applied
            is_dark = self.is_dark_callback()
            view = obj.view()
            
            # Apply style to the view window to make sure there's no square background
            if view and view.window():
                view.window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                view.window().setAttribute(Qt.WA_TranslucentBackground)
                
                # Make sure the popup has proper styling
                dark_bg = "#1A2433"
                light_bg = "#F0F8FF"
                bg_color = dark_bg if is_dark else light_bg
                
                view.window().setStyleSheet(f"""
                    QWidget {{ 
                        background-color: {bg_color}; 
                        border-radius: 15px; 
                    }}
                """)
            
            # Force the colors to match the theme
            if is_dark:
                view.setStyleSheet("""
                    QListView {
                        background-color: #1A2433; 
                        color: white; 
                        border: 1px solid gray; 
                        border-radius: 15px; 
                        padding: 3px;
                    }
                    QListView::item {
                        min-height: 28px;
                        padding: 5px;
                        text-align: center;
                    }
                    QListView::item:selected {
                        background-color: #2A3450;
                        border: 1px solid #4CAF50;
                    }
                    QListView::item:hover {
                        background-color: #2A3450;
                    }
                """)
                palette = view.palette()
                palette.setColor(QPalette.Base, QColor("#1A2433"))
                palette.setColor(QPalette.Text, QColor("white"))
                palette.setColor(QPalette.Highlight, QColor("#4A6591"))
                palette.setColor(QPalette.HighlightedText, QColor("white"))
                palette.setColor(QPalette.Window, QColor("#1A2433"))
            else:
                view.setStyleSheet("""
                    QListView {
                        background-color: #F0F8FF; 
                        color: black; 
                        border: 1px solid gray; 
                        border-radius: 15px; 
                        padding: 3px;
                    }
                    QListView::item {
                        min-height: 28px;
                        padding: 5px;
                        text-align: center;
                    }
                    QListView::item:selected {
                        background-color: #E6F2FF;
                        border: 1px solid #4CAF50;
                    }
                    QListView::item:hover {
                        background-color: #E6F2FF;
                    }
                """)
                palette = view.palette()
                palette.setColor(QPalette.Base, QColor("#F0F8FF"))
                palette.setColor(QPalette.Text, QColor("black"))
                palette.setColor(QPalette.Highlight, QColor("#87CEFA"))
                palette.setColor(QPalette.HighlightedText, QColor("black"))
                palette.setColor(QPalette.Window, QColor("#F0F8FF"))
            view.setPalette(palette)
            
        # Handle selection to ensure the display text is centered
        elif event.type() == QEvent.MouseButtonRelease:
            # Force style refresh to update centering
            obj.update()
        
        # For QEvent.Show, make sure the popup has the right style
        elif event.type() == QEvent.Show and hasattr(obj, 'view') and obj.view():
            view = obj.view()
            if view.window():
                view.window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                view.window().setAttribute(Qt.WA_TranslucentBackground)
        
        return False

def apply_dark_style_to_combobox(combo_box):
    """
    Apply dark theme styling to a QComboBox.
    
    Args:
        combo_box: The QComboBox to style
    """
    # Set the font and size
    combo_box.setMinimumHeight(36)
    
    # First, make sure it's not editable to restore default behavior
    was_editable = combo_box.isEditable()
    if was_editable:
        combo_box.setEditable(False)
    
    # Apply direct stylesheet to the combobox
    combo_box.setStyleSheet("""
        QComboBox {
            color: white;
            background-color: #1A2433;
            border: 1px solid gray;
            border-radius: 15px;
            padding-left: 15px;
            padding-right: 30px; /* More padding on right for the arrow */
            text-align: center;
            font-weight: bold;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            border: none;
            width: 30px;
            background-color: transparent;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin-right: 15px;
            background-color: transparent;
        }
        QComboBox QAbstractItemView {
            background-color: #1A2433;
            color: white;
            border: 1px solid #3A4561;
            border-radius: 15px;
            selection-background-color: #2A3450;
        }
        /* Set combobox-popup property to 0 to remove square background */
        QComboBox {
            combobox-popup: 0;
        }
    """)
    
    # Add custom property for text alignment
    combo_box.setLayoutDirection(Qt.LeftToRight)  # Reset direction first
    
    # Center align all items in the dropdown
    for i in range(combo_box.count()):
        combo_box.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
    
    # Set the view style
    view = combo_box.view()
    view.setStyleSheet("""
        QListView {
            background-color: #1A2433;
            color: white;
            border: 1px solid #3A4561;
            border-radius: 15px;
            outline: none;
            padding: 0px;
        }
        QListView::item {
            min-height: 28px;
            padding: 5px;
            text-align: center;
        }
        QListView::item:selected {
            background-color: #2A3450;
            border: 1px solid #4CAF50;
        }
        QListView::item:hover {
            background-color: #2A3450;
        }
    """)
    view.setTextElideMode(Qt.ElideMiddle)
    
    # Set palette
    palette = view.palette()
    palette.setColor(QPalette.Base, QColor("#1A2433"))
    palette.setColor(QPalette.Text, QColor("white"))
    palette.setColor(QPalette.Highlight, QColor("#4A6591"))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    palette.setColor(QPalette.Button, QColor("#1A2433"))  # Add this to fix the button background
    view.setPalette(palette)
    
    # Set window flags to remove the square box background
    if view.window():
        view.window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        view.window().setAttribute(Qt.WA_TranslucentBackground)
    
    return view

def apply_light_style_to_combobox(combo_box):
    """
    Apply light theme styling to a QComboBox.
    
    Args:
        combo_box: The QComboBox to style
    """
    # Set the font and size
    combo_box.setMinimumHeight(36)
    
    # First, make sure it's not editable to restore default behavior
    was_editable = combo_box.isEditable()
    if was_editable:
        combo_box.setEditable(False)
    
    # Apply direct stylesheet to the combobox
    combo_box.setStyleSheet("""
        QComboBox {
            color: black;
            background-color: #F0F8FF;
            border: 1px solid gray;
            border-radius: 15px;
            padding-left: 15px;
            padding-right: 30px; /* More padding on right for the arrow */
            text-align: center;
            font-weight: bold;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            border: none;
            width: 30px;
            background-color: transparent;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid black;
            margin-right: 15px;
            background-color: transparent;
        }
        QComboBox QAbstractItemView {
            background-color: #F0F8FF;
            color: black;
            border: 1px solid #B0C4DE;
            border-radius: 15px;
            selection-background-color: #E6F2FF;
        }
        /* Set combobox-popup property to 0 to remove square background */
        QComboBox {
            combobox-popup: 0;
        }
    """)
    
    # Add custom property for text alignment
    combo_box.setLayoutDirection(Qt.LeftToRight)  # Reset direction first
    
    # Center align all items in the dropdown
    for i in range(combo_box.count()):
        combo_box.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
    
    # Set the view style
    view = combo_box.view()
    view.setStyleSheet("""
        QListView {
            background-color: #F0F8FF;
            color: black;
            border: 1px solid #B0C4DE;
            border-radius: 15px;
            outline: none;
            padding: 0px;
        }
        QListView::item {
            min-height: 28px;
            padding: 5px;
            text-align: center;
        }
        QListView::item:selected {
            background-color: #E6F2FF;
            border: 1px solid #4CAF50;
        }
        QListView::item:hover {
            background-color: #E6F2FF;
        }
    """)
    view.setTextElideMode(Qt.ElideMiddle)
    
    # Set palette
    palette = view.palette()
    palette.setColor(QPalette.Base, QColor("#F0F8FF"))
    palette.setColor(QPalette.Text, QColor("black"))
    palette.setColor(QPalette.Highlight, QColor("#87CEFA"))
    palette.setColor(QPalette.HighlightedText, QColor("black"))
    palette.setColor(QPalette.Button, QColor("#F0F8FF"))  # Add this to fix the button background
    view.setPalette(palette)
    
    # Set window flags to remove the square box background
    if view.window():
        view.window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        view.window().setAttribute(Qt.WA_TranslucentBackground)
    
    return view

def style_combobox_for_theme(combo_box, is_dark=True):
    """
    Apply the appropriate theme styling to a QComboBox.
    
    Args:
        combo_box: The QComboBox to style
        is_dark: Whether to use dark theme styling (True) or light theme styling (False)
    """
    # Set a custom class name for the combobox to help with centering
    combo_box.setProperty("class", "centered-text-combo")
    
    # Apply the style based on the theme
    if is_dark:
        view = apply_dark_style_to_combobox(combo_box)
    else:
        view = apply_light_style_to_combobox(combo_box)
    
    # Create and apply the custom style
    combo_style = ComboBoxStyle(is_dark=is_dark)
    combo_box.setStyle(combo_style)
    
    # Install the event filter to handle popup events
    event_filter = ComboEventFilter(
        combo_box, 
        combo_style, 
        lambda: is_dark
    )
    combo_box.removeEventFilter(event_filter)  # Remove any existing filters first
    combo_box.installEventFilter(event_filter)
    
    # Force style update
    combo_box.style().unpolish(combo_box)
    combo_box.style().polish(combo_box)
    
    return combo_style 