from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate, QApplication, QWidget, QStylePainter, QStyle, QStyleOptionComboBox
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, QRect, QSize
from PyQt5.QtGui import QFontMetrics, QPainter, QPalette, QIcon
from utils.const import DARK_STYLESHEET

class NoDecorationsDelegate(QStyledItemDelegate):
    """A delegate that removes all decorations and indicators from combo box items"""
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Remove all decorations and icons
        option.icon = QIcon()  # Use empty QIcon instead of None
        option.decorationSize = QSize(0, 0)  # Use QSize instead of Qt.Size
        # option.features = None  # Reset all features to remove decorations

class ClickToOpenFilter(QObject):
    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo

    def eventFilter(self, obj, event):
        try:
            if obj == self.combo.lineEdit() and event.type() == QEvent.MouseButtonPress:
                self.combo.showPopup()
                return True
            return super().eventFilter(obj, event)
        except RuntimeError:
            # Handle case where the C/C++ object has been deleted
            return False

class CenteredComboBox(QComboBox):
    """A QComboBox that centers both the dropdown items and the selected item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up a delegate to center the items in the view and remove decorations
        delegate = NoDecorationsDelegate(self)
        self.setItemDelegate(delegate)

        # Make editable to get the line edit for centering
        self.setEditable(True)

        # Disable editing by setting read-only
        self.lineEdit().setReadOnly(True)

        # Center the text in the line edit
        self.lineEdit().setAlignment(Qt.AlignCenter)

        # Make the line edit look like a non-editable combo box
        self.lineEdit().setFrame(False)
        
        # Completely remove the dropdown button to ensure text centering
        self.setStyleSheet("""
            QComboBox {
            	  font-weight: normal !important;
                combobox-popup: 1;
                background: transparent;
                border-radius: 15px;
                padding-left: 0px;
                padding-right: 0px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 0px;
                border: none;
                background: transparent;
                image: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                background: transparent;
            }
        """)
        
        # Apply a balanced margin to the line edit for perfect centering
        self.lineEdit().setStyleSheet("""
            background: transparent;
            border: none;
            padding-left: 0px;
            padding-right: 0px;
            margin: 0px;
        """)
        
        self.lineEdit().installEventFilter(ClickToOpenFilter(self))
        # Disable all text interactions:
        self.lineEdit().setFocusPolicy(Qt.NoFocus)

        # (Optional) Change the cursor so it doesn't look like an I-beam:
        self.lineEdit().setCursor(Qt.ArrowCursor)

        # Make sure the popup is also properly styled
        self.view().parentWidget().setStyleSheet("background: transparent;")
        
        # Ensure combo box popup items are centered as well
        for i in range(self.count()):
            self.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
            
        # Apply the default theme
        self.apply_default_theme()
        
        # Set this to prevent the dropdown arrow from appearing
        self.setMaxVisibleItems(10)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        
    def paintEvent(self, event):
        """Override the paint event to have complete control over rendering"""
        # Use QStylePainter for more reliable styled drawing
        painter = QStylePainter(self)
        
        # Create style option
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        
        # Disable the arrow by removing its subcontrol
        opt.subControls &= ~QStyle.SC_ComboBoxArrow
        
        # Draw the combobox without the arrow
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)
        
        # Draw the text centered in the box
        if self.currentText():
            text_rect = self.rect()
            text_rect.adjust(10, 0, -10, 0)  # Add some padding
            
            # Set the text color based on the theme
            if self.is_dark_theme():
                painter.setPen(Qt.white)
            else:
                painter.setPen(Qt.black)
                
            # painter.drawText(text_rect, Qt.AlignCenter, self.currentText())

    def apply_default_theme(self):
        """Apply appropriate styling for the current theme when the widget is first created"""
        is_dark = self.is_dark_theme()
        
        if is_dark:
            # Dark theme button appearance
            line_edit_style = """
                QLineEdit {
                    background: transparent;
                    color: white;
                    border: none;
                    padding-left: 0px;
                    padding-right: 0px;
                    margin: 0px;
                }
            """
        else:
            # Light theme button appearance
            line_edit_style = """
                QLineEdit {
                    background: transparent;
                    color: #333333;
                    border: none;
                    padding-left: 0px;
                    padding-right: 0px;
                    margin: 0px;
                }
            """
            
        self.lineEdit().setStyleSheet(line_edit_style)

    def addItem(self, text, userData=None):
        """Override addItem to ensure new items are center-aligned"""
        super().addItem(text, userData)
        self.setItemData(self.count() - 1, Qt.AlignCenter, Qt.TextAlignmentRole)
        # Remove any decoration or icon
        self.setItemData(self.count() - 1, None, Qt.DecorationRole)

    def insertItem(self, index, text, userData=None):
        """Override insertItem to ensure new items are center-aligned"""
        super().insertItem(index, text, userData)
        self.setItemData(index, Qt.AlignCenter, Qt.TextAlignmentRole)
        # Remove any decoration or icon
        self.setItemData(index, None, Qt.DecorationRole)

    def is_dark_theme(self):
        """Detect if dark theme is currently active based on main window's stylesheet"""
        # Get the main window
        parent = self.parent()
        while parent is not None:
            # Check if this parent has the _current_stylesheet attribute 
            if hasattr(parent, '_current_stylesheet'):
                return parent._current_stylesheet == DARK_STYLESHEET
            parent = parent.parent()
        
        # Fallback to the application palette check if we can't find the main window
        app = QApplication.instance()
        if app:
            bg_color = app.palette().color(app.palette().Window)
            return bg_color.lightness() < 128
            
        return True  # Default to dark theme if can't determine

    def showPopup(self):
        """Override showPopup to ensure all items are center-aligned and have rounded corners with theme awareness"""
        for i in range(self.count()):
            self.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)
            # Remove any decoration or icon
            self.setItemData(i, None, Qt.DecorationRole)

        # Determine if we're in dark or light theme
        is_dark = self.is_dark_theme()
        
        if is_dark:
            # Original dark theme styling (restored)
            self.view().setStyleSheet("""
                QListView {
                    border: 1px solid #555;
                    border-radius: 6px;
                    background-color: #1E293B;
                    outline: 10px;
                    padding: 14px;
                }
                
                QListView::item {
                    border-radius: 6px;
                    padding: 4px;
                    margin: 2px;
                    text-align: center;
                }
                
                QListView::item:selected {
                    background-color: #2a82da;
                    color: white;
                }
                QComboBox QAbstractItemView::item {
                    text-align: center;
                }
            """)
        else:
            # Light theme styling (enhanced for better appearance)
            self.view().setStyleSheet("""
                QListView {
                    border: 1px solid #D0D0D0;
                    border-radius: 8px;
                    background-color: #FFFFFF;
                    outline: none;
                    padding: 14px;
                    box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.15);
                }
                
                QListView::item {
                    border-radius: 6px;
                    padding: 6px;
                    margin: 3px;
                    color: #333333;
                    text-align: center;
                }
                
                QListView::item:hover {
                    background-color: #F0F7FF;
                }
                
                QListView::item:selected {
                    background-color: #4CAF50;
                    color: white;
                }
                                
                QComboBox QAbstractItemView::item {
                    text-align: center;
                }
            """)

        # Set window flags to remove frame and shadow
        self.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        # Make the background translucent
        self.view().window().setAttribute(Qt.WA_TranslucentBackground)

        super().showPopup()