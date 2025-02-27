import sys
import platform
import os
import json
import dataclasses

from datetime import datetime
from time import time
from typing import Optional
import re

from PyQt5.QtWidgets import (
  QApplication, 
  QWidget, 
  QVBoxLayout, 
  QPushButton, 
  QLabel, 
  QGridLayout,
  QFrame,
  QTextEdit,
  QDialog, 
  QHBoxLayout, 
  QSpacerItem, 
  QSizePolicy,
  QCheckBox,
  QStyle,
  QComboBox,
  QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg

from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory
from widgets.ToastWidget import ToastWidget, NotificationType
from utils.const import *
from utils.docker import _DockerUtilsMixin
from utils.docker_commands import DockerCommandHandler
from utils.updater import _UpdaterMixin

from utils.icon import ICON_BASE64

from app_forms.frm_utils import (
  get_icon_from_base64, DateAxisItem,
  generate_container_name, get_volume_name
)

from ver import __VER__ as __version__
from widgets.dialogs.AuthorizedAddressedDialog import AuthorizedAddressesDialog
from models.AllowedAddress import AllowedAddress, AllowedAddressList
from models.StartupConfig import StartupConfig
from models.ConfigApp import ConfigApp
from widgets.HostSelector import HostSelector
from widgets.ModeSwitch import ModeSwitch


def get_platform_and_os_info():
  platform_info = platform.platform()
  os_name = platform.system()
  os_version = platform.version()
  return platform_info, os_name, os_version

def log_with_color(message, color="gray"):
  """
    Log message with color in the terminal.
    :param message: Message to log
    :param color: Color of the message
  """
  color_codes = {
    "yellow": "\033[93m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "light": "\033[97m",
    "green": "\033[92m",
    "blue" : "\033[94m",
    "cyan" : "\033[96m",
  }
  start_color = color_codes.get(color, "\033[90m")
  end_color = "\033[0m"
  print(f"{start_color}{message}{end_color}", flush=True)
  return

class EdgeNodeLauncher(QWidget, _DockerUtilsMixin, _UpdaterMixin):
  def __init__(self):
    self.logView = None
    self.log_buffer = []
    self.__force_debug = False
    super().__init__()

    # Set current environment (you'll need to get this from your configuration)
    self.current_environment = DEFAULT_ENVIRONMENT

    self.__current_node_uptime = -1
    self.__current_node_epoch = -1
    self.__current_node_epoch_avail = -1
    self.__current_node_ver = -1
    self.__display_uptime = None


    self._current_stylesheet = DARK_STYLESHEET
    self.__last_plot_data = None
    self.__last_auto_update_check = 0
    
    self.__version__ = __version__
    self.__last_timesteps = []
    self._icon = get_icon_from_base64(ICON_BASE64)
    
    self.runs_in_production = self.is_running_in_production()
    
    self.initUI()

    self.__cwd = os.getcwd()
    
    self.showMaximized()
    self.add_log(f'Edge Node Launcher v{self.__version__} started. Running in production: {self.runs_in_production}, running with debugger: {self.runs_with_debugger()}, running in ipython: {self.runs_from_ipython()},  running from exe: {not self.not_running_from_exe()}')
    self.add_log(f'Running from: {self.__cwd}')


    platform_info, os_name, os_version = get_platform_and_os_info()
    self.add_log(f'Platform: {platform_info}')
    self.add_log(f'OS: {os_name} {os_version}')

    if not self.check_docker():
      sys.exit(1)    

    self.docker_initialize()
    self.docker_handler = DockerCommandHandler(DOCKER_CONTAINER_NAME)

    # Initialize container list
    self.refresh_container_list()

    if self.is_container_running():
      self.post_launch_setup()
      self.refresh_local_address()
      self.plot_data()  # Initial plot

    self.update_toggle_button_text()

    self.timer = QTimer(self)
    self.timer.timeout.connect(self.refresh_all)
    self.timer.start(REFRESH_TIME)  # Refresh every 10 seconds
    self.toast = ToastWidget(self)

    return

  @staticmethod
  def not_running_from_exe():
    """
    Checks if the script is running from a PyInstaller-generated executable.

    Returns
    -------
    bool
      True if running from a PyInstaller executable, False otherwise.
    """
    return not (hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'))
  
  @staticmethod
  def runs_from_ipython():
    try:
      __IPYTHON__
      return True
    except NameError:
      return False
    
  @staticmethod
  def runs_with_debugger():
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
      return False
    else:
      return not gettrace() is None    
    
  def is_running_in_production(self):
    return not (self.runs_from_ipython() or self.runs_with_debugger() or self.not_running_from_exe())
  
  
  def add_log(self, line, debug=False, color="gray"):
    show = (debug and not self.runs_in_production) or not debug
    show = show or self.__force_debug
    if show:      
      timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
      line = f'{timestamp} {line}'
      if self.logView is not None:
        self.logView.append(line)
      else:
        self.log_buffer.append(line)
      QApplication.processEvents()  # Flush the event queue
      if debug or self.__force_debug:
        log_with_color(line, color=color)
    return  
  
  def center(self):
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - self.width()) // 2
    y = (screen_geometry.height() - self.height()) // 2
    self.move(x, y)
    return

  def set_windows_taskbar_icon(self):
    if os.name == 'nt':
      import ctypes
      myappid = 'naeural.edge_node_launcher'  # arbitrary string
      ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # TODO: Add support for other OS (Linux, MacOS)
    return
  
  def initUI(self):
    HEIGHT = 1100
    self.setWindowTitle(WINDOW_TITLE)
    self.setGeometry(0, 0, 1800, HEIGHT)
    self.center()

    # Create the main layout
    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Content area with overlay for mode switch
    content_widget = QWidget()
    content_widget.setLayout(QHBoxLayout())
    content_widget.layout().setContentsMargins(0, 0, 0, 0)
    content_widget.layout().setSpacing(0)

    # Left menu layout with fixed width
    menu_widget = QWidget()
    menu_widget.setFixedWidth(300)  # Set the fixed width here
    menu_layout = QVBoxLayout(menu_widget)
    menu_layout.setAlignment(Qt.AlignTop)
    menu_layout.setContentsMargins(0, 0, 0, 0)
    
    # Add host selector
    self.host_selector = HostSelector()
    self.host_selector.host_selected.connect(self._on_host_selected)
    self.host_selector.mode_changed.connect(self._on_host_mode_changed)
    self.host_selector.apply_stylesheet(self._current_stylesheet == DARK_STYLESHEET)
    self.host_selector.hide()  # Initially hidden in simple mode
    menu_layout.addWidget(self.host_selector)
    
    top_button_area = QVBoxLayout()

    # Container selector area
    container_selector_layout = QHBoxLayout()
    
    # Container dropdown
    self.container_combo = QComboBox()
    self.container_combo.setFont(QFont("Courier New", 10))
    self.container_combo.currentTextChanged.connect(self._on_container_selected)
    container_selector_layout.addWidget(self.container_combo, stretch=1)
    
    # Add Node button
    self.add_node_button = QPushButton("Add Node")
    self.add_node_button.setFont(QFont("Courier New", 10))
    self.add_node_button.clicked.connect(self.show_add_node_dialog)
    container_selector_layout.addWidget(self.add_node_button)
    
    top_button_area.addLayout(container_selector_layout)

    # Launch Edge Node button
    self.toggleButton = QPushButton(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.clicked.connect(self.toggle_container)
    top_button_area.addWidget(self.toggleButton)

    # Docker download button right under Launch Edge Node
    self.docker_download_button = QPushButton('Download Docker')
    self.docker_download_button.setToolTip('Ratio1 Edge Node requires Docker Desktop running in parallel')
    self.docker_download_button.clicked.connect(self.open_docker_download)
    top_button_area.addWidget(self.docker_download_button)

    # dApp button
    self.dapp_button = QPushButton(DAPP_BUTTON_TEXT)
    self.dapp_button.clicked.connect(self.dapp_button_clicked)
    top_button_area.addWidget(self.dapp_button)

    # Explorer button
    self.explorer_button = QPushButton(EXPLORER_BUTTON_TEXT)
    self.explorer_button.clicked.connect(self.explorer_button_clicked)
    top_button_area.addWidget(self.explorer_button)

    menu_layout.addLayout(top_button_area)

    # Spacer to push bottom_button_area to the bottom
    menu_layout.addSpacerItem(QSpacerItem(20, int(HEIGHT * 0.75), QSizePolicy.Minimum, QSizePolicy.Expanding))


    # Bottom button area
    bottom_button_area = QVBoxLayout()
    
    ## info box
    info_box = QFrame()
    info_box.setFrameShape(QFrame.Box)
    info_box.setFrameShadow(QFrame.Sunken)
    info_box.setLineWidth(4)
    info_box.setMidLineWidth(1)
    info_box_layout = QVBoxLayout()

    # Address display with copy button
    addr_layout = QHBoxLayout()
    self.addressDisplay = QLabel('')
    self.addressDisplay.setFont(QFont("Courier New"))
    addr_layout.addWidget(self.addressDisplay)
    
    self.copyAddrButton = QPushButton()
    self.copyAddrButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
    self.copyAddrButton.setToolTip('Copy address')
    self.copyAddrButton.clicked.connect(self.copy_address)
    self.copyAddrButton.setFixedSize(24, 24)
    self.copyAddrButton.hide()  # Initially hidden
    addr_layout.addWidget(self.copyAddrButton)
    addr_layout.addStretch()
    info_box_layout.addLayout(addr_layout)

    # ETH address display with copy button
    eth_addr_layout = QHBoxLayout()
    self.ethAddressDisplay = QLabel('')
    self.ethAddressDisplay.setFont(QFont("Courier New"))
    eth_addr_layout.addWidget(self.ethAddressDisplay)
    
    self.copyEthButton = QPushButton()
    self.copyEthButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
    self.copyEthButton.setToolTip('Copy Ethereum address')
    self.copyEthButton.clicked.connect(self.copy_eth_address)
    self.copyEthButton.setFixedSize(24, 24)
    self.copyEthButton.hide()  # Initially hidden
    eth_addr_layout.addWidget(self.copyEthButton)
    eth_addr_layout.addStretch()
    info_box_layout.addLayout(eth_addr_layout)

    self.nameDisplay = QLabel('')
    self.nameDisplay.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.nameDisplay)

    self.node_uptime = QLabel(UPTIME_LABEL)
    self.node_uptime.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_uptime)

    self.node_epoch = QLabel(EPOCH_LABEL)
    self.node_epoch.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch)

    self.node_epoch_avail = QLabel(EPOCH_AVAIL_LABEL)
    self.node_epoch_avail.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_epoch_avail)

    self.node_version = QLabel()
    self.node_version.setFont(QFont("Courier New"))
    info_box_layout.addWidget(self.node_version)
    
    info_box.setLayout(info_box_layout)
    bottom_button_area.addWidget(info_box)
    
    ## buttons
    # Add Rename Node button
    self.renameNodeButton = QPushButton(RENAME_NODE_BUTTON_TEXT)
    self.renameNodeButton.clicked.connect(self.show_rename_dialog)
    bottom_button_area.addWidget(self.renameNodeButton)

    self.btn_edit_addrs = QPushButton(EDIT_AUTHORIZED_ADDRS)
    self.btn_edit_addrs.clicked.connect(self.edit_addrs)
    bottom_button_area.addWidget(self.btn_edit_addrs)

    
    # view_config_files
    self.btn_view_configs = QPushButton(VIEW_CONFIGS_BUTTON_TEXT)
    self.btn_view_configs.clicked.connect(self.view_config_files)
    bottom_button_area.addWidget(self.btn_view_configs)

    
    self.deleteButton = QPushButton(DELETE_AND_RESTART_BUTTON_TEXT)
    self.deleteButton.clicked.connect(self.delete_and_restart)
    bottom_button_area.addWidget(self.deleteButton)

    # Toggle theme button
    self.themeToggleButton = QPushButton(LIGHT_DASHBOARD_BUTTON_TEXT)
    # self.themeToggleButton.setCheckable(True)
    self.themeToggleButton.clicked.connect(self.toggle_theme)
    bottom_button_area.addWidget(self.themeToggleButton)    
    
    # add a checkbox item to force debug
    self.force_debug_checkbox = QCheckBox('Force Debug Mode')
    self.force_debug_checkbox.setChecked(False)
    self.force_debug_checkbox.setFont(QFont("Courier New", 9, QFont.Bold))
    self.force_debug_checkbox.setStyleSheet("color: white;")
    self.force_debug_checkbox.stateChanged.connect(self.toggle_force_debug)
    bottom_button_area.addWidget(self.force_debug_checkbox)

    bottom_button_area.addStretch()
    menu_layout.addLayout(bottom_button_area)
    
    content_widget.layout().addWidget(menu_widget)

    # Right panel with mode switch overlay
    right_container = QWidget()
    right_container_layout = QVBoxLayout(right_container)
    right_container_layout.setContentsMargins(0, 0, 0, 0)
    right_container_layout.setSpacing(0)

    # Mode switch at the top
    mode_switch_layout = QHBoxLayout()
    mode_switch_layout.setContentsMargins(10, 5, 10, 5)
    mode_switch_layout.setSpacing(0)
    mode_switch_layout.addStretch(1)
    self.mode_switch = ModeSwitch()
    self.mode_switch.mode_changed.connect(self._on_simple_pro_mode_changed)
    self.mode_switch.apply_stylesheet(self._current_stylesheet == DARK_STYLESHEET)
    mode_switch_layout.addWidget(self.mode_switch, 0, Qt.AlignRight | Qt.AlignVCenter)
    right_container_layout.addLayout(mode_switch_layout)

    # Add a small spacer between mode switch and graphs
    right_container_layout.addSpacing(5)
    
    # Right side layout (for graphs)
    right_panel = QWidget()
    right_panel_layout = QVBoxLayout(right_panel)
    
    # the graph area
    self.graphView = QWidget()
    graph_layout = QGridLayout()
    
    self.cpu_plot = pg.PlotWidget()
    self.memory_plot = pg.PlotWidget()
    self.gpu_plot = pg.PlotWidget()
    self.gpu_memory_plot = pg.PlotWidget()
    
    graph_layout.addWidget(self.cpu_plot, 0, 0)
    graph_layout.addWidget(self.memory_plot, 0, 1)
    graph_layout.addWidget(self.gpu_plot, 1, 0)
    graph_layout.addWidget(self.gpu_memory_plot, 1, 1)
    
    self.graphView.setLayout(graph_layout)
    right_panel_layout.addWidget(self.graphView)
    
    # the log scroll text area
    self.logView = QTextEdit()
    self.logView.setReadOnly(True)
    self.logView.setStyleSheet(self._current_stylesheet)
    self.logView.setFixedHeight(150)
    self.logView.setFont(QFont("Courier New"))
    right_panel_layout.addWidget(self.logView)
    if self.log_buffer:
        for line in self.log_buffer:
            self.logView.append(line)
        self.log_buffer = []

    right_container_layout.addWidget(right_panel)
    
    # Add the main content widgets
    content_widget.layout().addWidget(menu_widget)
    content_widget.layout().addWidget(right_container)
    
    main_layout.addWidget(content_widget)

    self.setLayout(main_layout)
    self.apply_stylesheet()
    
    self.setWindowIcon(self._icon)
    self.set_windows_taskbar_icon()

    return
  
  def toggle_theme(self):
    if self._current_stylesheet == DARK_STYLESHEET:
      self._current_stylesheet = LIGHT_STYLESHEET
      self.themeToggleButton.setText('Switch to Dark Theme')
      self.host_selector.apply_stylesheet(False)  # Light theme
    else:
      self._current_stylesheet = DARK_STYLESHEET
      self.themeToggleButton.setText('Switch to Light Theme')
      self.host_selector.apply_stylesheet(True)  # Dark theme
    self.apply_stylesheet()
    self.plot_graphs()
    self.change_text_color()
    return  

  # TODO: Find a better approach. It's a hotfix for the text color issue.
  def change_text_color(self):
    if self._current_stylesheet == DARK_STYLESHEET:
      self.force_debug_checkbox.setStyleSheet("color: white;")
    else:
      self.force_debug_checkbox.setStyleSheet("color: black;")

  def apply_stylesheet(self):
    is_dark = self._current_stylesheet == DARK_STYLESHEET
    self.setStyleSheet(self._current_stylesheet)
    self.logView.setStyleSheet(self._current_stylesheet)
    self.cpu_plot.setBackground(None)  # Reset the background to let the stylesheet take effect
    self.memory_plot.setBackground(None)
    self.gpu_plot.setBackground(None)
    self.gpu_memory_plot.setBackground(None)
    
    # Style container selector
    text_color = "white" if is_dark else "black"
    bg_color = "#2b2b2b" if is_dark else "white"
    border_color = "#555555" if is_dark else "#cccccc"
    hover_color = "#3b3b3b" if is_dark else "#f5f5f5"
    
    combobox_style = f"""
        QComboBox {{
            color: {text_color};
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 4px;
            min-width: 100px;
        }}
        QComboBox:hover {{
            background-color: {hover_color};
            border: 1px solid #4CAF50;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {text_color};
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            color: {text_color};
            background-color: {bg_color};
            selection-background-color: {hover_color};
            selection-color: {text_color};
        }}
    """
    
    button_style = f"""
        QPushButton {{
            color: {text_color};
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 4px 12px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid #4CAF50;
        }}
    """
    
    self.container_combo.setStyleSheet(combobox_style)
    self.add_node_button.setStyleSheet(button_style)
    
    if hasattr(self, 'mode_switch'):
      self.mode_switch.apply_stylesheet(is_dark)
    return

  def toggle_container(self):
    # Get currently selected container
    container_name = self.container_combo.currentText()
    if not container_name:
        self.toast.show_notification(NotificationType.ERROR, "No container selected")
        return
        
    try:
        # Update docker handler with selected container
        self.docker_handler.set_container_name(container_name)
        
        if self.is_container_running():
            self.add_log(f'Stopping container {container_name}...')
            # Use docker_handler to stop the container instead of the mixin method
            self.docker_handler.stop_container()
            self._clear_info_display()
        else:
            self.add_log(f'Starting container {container_name}...')
            # Get volume name based on container name
            volume_name = get_volume_name(container_name)
            self.launch_container(volume_name=volume_name)
            
        self.update_toggle_button_text()
        
    except Exception as e:
        self.add_log(f"Error toggling container {container_name}: {str(e)}", debug=True, color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error toggling container: {str(e)}")
    return

  def update_toggle_button_text(self):
    container_name = self.container_combo.currentText()
    if not container_name:
        self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
        self.toggleButton.setStyleSheet("background-color: gray; color: white;")
        self.toggleButton.setEnabled(False)
        return
        
    self.toggleButton.setEnabled(True)
    if self.is_container_running():
        self.toggleButton.setText(STOP_CONTAINER_BUTTON_TEXT)
        self.toggleButton.setStyleSheet("background-color: red; color: white;")
    else:
        self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
        self.toggleButton.setStyleSheet("background-color: green; color: white;")
    return
  
  def edit_file(self, file_path, func, title='Edit File'):
    env_content = ''
    try:
      with open(file_path, 'r') as file:
        env_content = file.read()
    except FileNotFoundError:
      pass    
    
    # Create the text edit widget with Courier New font and light font color
    text_edit = QTextEdit()
    text_edit.setText(env_content)
    # text_edit.setFont(QFont("Courier New", 14))
    # text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

    # Create the dialog
    dialog = QDialog(self)
    dialog.setWindowTitle(title)
    dialog.setGeometry(0, 0, 1000, 900)  # Enlarge the edit window

    # Center the dialog on the screen
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(text_edit)

    # Save button
    save_button = QPushButton('Save')
    save_button.clicked.connect(lambda: func(text_edit.toPlainText(), dialog))
    dialog_layout.addWidget(save_button)

    dialog.setLayout(dialog_layout)
    dialog.exec_()
    return    

  def edit_env_file(self):
    self.edit_file(
      file_path=self.env_file, 
      func=self.save_env_file, 
      title='Edit .env file'
    )
    return
  
  def save_env_file(self, content, dialog):
    with open(self.env_file, 'w') as file:
      file.write(content)
    dialog.accept()
    return
  
  
  # def edit_addrs(self):
  #   self.edit_file(
  #     file_path=self.addrs_file,
  #     func=self.save_addrs_file,
  #     title='Edit authorized addrs file'
  #   )
  #   return


  def edit_addrs(self):
    if not self.is_container_running():
        self.toast.show_notification(NotificationType.ERROR, "Container not running. Could not edit Authorized Addressees.")
        return

    dialog = AuthorizedAddressesDialog(self, on_save_callback=None)

    def on_success(data: dict) -> None:
        allowed_list = AllowedAddressList.from_dict(data)
        dialog.load_data(allowed_list.to_batch_format())
        
        while True:  # Keep showing dialog until properly saved or cancelled
            if dialog.exec_() != QDialog.Accepted:
                break  # User clicked Cancel on the main dialog
                
            # Check for long aliases and duplicates before saving
            data_to_save = dialog.get_data()
            
            # Check for duplicate aliases
            aliases = [item['alias'] for item in data_to_save]
            duplicate_aliases = [alias for alias in set(aliases) if aliases.count(alias) > 1]
            
            if duplicate_aliases:
                # Show duplicate aliases warning
                warning_msg = "The following aliases are duplicated:\n\n"
                for alias in duplicate_aliases:
                    warning_msg += f"• {alias}\n"
                warning_msg += "\nPlease make all aliases unique before saving."
                
                # Show warning dialog
                dup_dialog = QDialog(dialog)
                dup_dialog.setWindowTitle("Warning: Duplicate Aliases")
                layout = QVBoxLayout()
                
                # Add message
                label = QLabel(warning_msg)
                layout.addWidget(label)
                
                # Add OK button
                ok_btn = QPushButton("OK")
                ok_btn.clicked.connect(dup_dialog.accept)
                layout.addWidget(ok_btn)
                
                dup_dialog.setLayout(layout)
                dup_dialog.exec_()
                continue  # Go back to editing
            
            # Check for long aliases
            long_aliases = [(item['alias'], len(item['alias'])) for item in data_to_save if len(item['alias']) > MAX_ALIAS_LENGTH]
            
            if not long_aliases:  # No long aliases, proceed with save
                def save_success(data: dict) -> None:
                    self.add_log('Successfully updated authorized addresses', debug=True)
                    self.toast.show_notification(
                        NotificationType.SUCCESS, 
                        'Authorized addresses updated successfully'
                    )

                def save_error(error: str) -> None:
                    self.add_log(f'Error updating authorized addresses: {error}', debug=True)
                    self.toast.show_notification(
                        NotificationType.ERROR, 
                        'Failed to update authorized addresses'
                    )

                self.docker_handler.update_allowed_batch(data_to_save, save_success, save_error)
                break  # Exit the loop after successful save
            
            # Show warning for long aliases
            warning_msg = f"The following aliases are too long (max {MAX_ALIAS_LENGTH} characters) and will be truncated:\n\n"
            for alias, length in long_aliases:
                warning_msg += f"• {alias} ({length} characters)\n"
            warning_msg += "\nDo you want to proceed with truncation?"
            
            # Show confirmation dialog
            confirm_dialog = QDialog(dialog)
            confirm_dialog.setWindowTitle("Warning: Long Aliases")
            layout = QVBoxLayout()
            
            # Add message
            label = QLabel(warning_msg)
            layout.addWidget(label)
            
            # Add buttons
            button_layout = QHBoxLayout()
            proceed_btn = QPushButton("Proceed")
            cancel_btn = QPushButton("Cancel")
            
            button_layout.addWidget(proceed_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            confirm_dialog.setLayout(layout)
            
            # Connect buttons
            proceed_btn.clicked.connect(confirm_dialog.accept)
            cancel_btn.clicked.connect(confirm_dialog.reject)
            
            if confirm_dialog.exec_() == QDialog.Accepted:
                # Truncate long aliases
                for item in data_to_save:
                    if len(item['alias']) > MAX_ALIAS_LENGTH:
                        item['alias'] = item['alias'][:MAX_ALIAS_LENGTH]
                
                def save_success(data: dict) -> None:
                    self.add_log('Successfully updated authorized addresses', debug=True)
                    self.toast.show_notification(
                        NotificationType.SUCCESS, 
                        'Authorized addresses updated successfully'
                    )

                def save_error(error: str) -> None:
                    self.add_log(f'Error updating authorized addresses: {error}', debug=True)
                    self.toast.show_notification(
                        NotificationType.ERROR, 
                        'Failed to update authorized addresses'
                    )

                self.docker_handler.update_allowed_batch(data_to_save, save_success, save_error)
                break  # Exit the loop after successful save
            # If user clicked Cancel on confirmation, loop continues and shows main dialog again

    def on_error(error: str) -> None:
        self.add_log(f'Error getting allowed addresses: {error}', debug=True)
        dialog.load_data([])
        dialog.exec_()

    if self.is_container_running():
        self.docker_handler.get_allowed_addresses(on_success, on_error)
    else:
        on_error("Container not running")


  def view_config_files(self):
    startup_config = None
    config_app = None
    error_occurred = False

    def check_and_show_configs():
        if error_occurred:
            return
        if startup_config is not None and config_app is not None:
            # Both configs are loaded, show them
            config_startup_content = json.dumps(dataclasses.asdict(startup_config), indent=2)
            config_app_content = json.dumps(dataclasses.asdict(config_app), indent=2)

            # Create the text edit widgets
            startup_text_edit = QTextEdit()
            startup_text_edit.setText(config_startup_content)
            startup_text_edit.setFont(QFont("Courier New", 11))
            startup_text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

            app_text_edit = QTextEdit()
            app_text_edit.setText(config_app_content)
            app_text_edit.setFont(QFont("Courier New", 11))
            app_text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

            # Create and show dialog
            self.show_config_dialog(startup_text_edit, app_text_edit)

    def on_startup_success(config: StartupConfig) -> None:
        nonlocal startup_config
        startup_config = config
        check_and_show_configs()

    def on_startup_error(error: str) -> None:
        nonlocal error_occurred
        error_occurred = True
        self.add_log(f'Error getting startup config: {error}', debug=True)
        self.toast.show_notification(NotificationType.ERROR, 'Failed to load startup config')

    def on_config_app_success(config: ConfigApp) -> None:
        nonlocal config_app
        config_app = config
        check_and_show_configs()

    def on_config_app_error(error: str) -> None:
        nonlocal error_occurred
        error_occurred = True
        self.add_log(f'Error getting config app: {error}', debug=True)
        self.toast.show_notification(NotificationType.ERROR, 'Failed to load config app')

    if self.is_container_running():
        # Start both requests in parallel
        self.docker_handler.get_startup_config(on_startup_success, on_startup_error)
        self.docker_handler.get_config_app(on_config_app_success, on_config_app_error)
    else:
        self.toast.show_notification(NotificationType.ERROR, 'Container not running')

  def show_config_dialog(self, startup_text_edit, app_text_edit):
    # Create the dialog
    dialog = QDialog(self)
    dialog.setWindowTitle('View config files')
    dialog.setGeometry(0, 0, 1000, 900)  # Enlarge the edit window

    # Center the dialog on the screen
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(startup_text_edit)
    dialog_layout.addWidget(app_text_edit)

    # Save button
    save_button = QPushButton('Ok')
    save_button.clicked.connect(
      lambda: self.close_config_files(
        startup_text_edit.toPlainText(), app_text_edit.toPlainText(), dialog)
      )
    dialog_layout.addWidget(save_button)

    dialog.setLayout(dialog_layout)
    dialog.exec_()
    return  
  
  def close_config_files(self, txt_startup, txt_app, dialog):
    # TODO: edit files
    dialog.accept()
    return

  
  def check_data(self, data):
    result = False
    if 'timestamps' in data:
      self.__current_node_epoch = data.pop('epoch', -1)
      self.__current_node_epoch_avail = data.pop('epoch_avail', -1)
      self.__current_node_uptime = data.pop('uptime', -1)
      self.__current_node_ver = data.pop('version', '')
              
      start_time = data['timestamps'][0] 
      end_time = data['timestamps'][-1]
      current_timestamps = data['timestamps'].copy()
      if current_timestamps != self.__last_timesteps:
        self.__last_timesteps = current_timestamps
        data_size = len(data['timestamps'])
        if data_size > 0 and data_size > MAX_HISTORY_QUEUE:
          for key in data:
            if isinstance(data[key], list):
              data[key] = data[key][-MAX_HISTORY_QUEUE:]
        start_time = data['timestamps'][0] 
        end_time = data['timestamps'][-1]
        self.add_log('Data loaded & cleaned: {} timestamps from {} to {}'.format(
          len(data['timestamps']), start_time, end_time), debug=True
        )
        result = True
      else:
        self.add_log('Data already up-to-date. No new data.', debug=True)
    else:
      self.add_log('No timestamps data found in the file.', debug=True)
    return result

  def plot_data(self):
    """Fetch and plot node history data.
    
    This method fetches node history data from the container and plots it.
    It handles errors and timeouts gracefully.
    """
    # Define success and error callbacks
    def on_success(history: NodeHistory) -> None:
      self.__current_node_epoch = history.current_epoch
      self.__current_node_epoch_avail = history.current_epoch_avail
      self.__current_node_uptime = history.uptime
      self.__current_node_ver = history.version

      if history.timestamps != self.__last_timesteps:
        self.__last_timesteps = history.timestamps.copy()
        if len(history.timestamps) > MAX_HISTORY_QUEUE:
          history.timestamps = history.timestamps[-MAX_HISTORY_QUEUE:]
          history.cpu_load = history.cpu_load[-MAX_HISTORY_QUEUE:]
          history.occupied_memory = history.occupied_memory[-MAX_HISTORY_QUEUE:]
          if history.gpu_load:
            history.gpu_load = history.gpu_load[-MAX_HISTORY_QUEUE:]
          if history.gpu_occupied_memory:
            history.gpu_occupied_memory = history.gpu_occupied_memory[-MAX_HISTORY_QUEUE:]

        self.add_log(f'Data loaded & cleaned: {len(history.timestamps)} timestamps', debug=True)
        self.plot_graphs(history)
      else:
        self.add_log('Data already up-to-date. No new data.', debug=True)

    def on_error(error: str) -> None:
      self.add_log(f'Error getting history: {error}', debug=True)
      # Still try to plot with existing data if available
      self.plot_graphs(None)
      
      # If this is a timeout error, log it more prominently
      if "timed out" in error.lower():
        self.add_log("Node history request timed out. This may indicate network issues or high load on the remote host.", color="red")

    # Start the request
    try:
      self.docker_handler.get_node_history(on_success, on_error)
    except Exception as e:
      self.add_log(f"Failed to start node history request: {str(e)}", debug=True, color="red")
      # Try to plot with existing data
      self.plot_graphs(None)

  def plot_graphs(self, history: Optional[NodeHistory] = None, limit: int = 100) -> None:
    if history is None:
      data = self.__last_plot_data
    else:
      self.__last_plot_data = history

    timestamps = [
      datetime.fromisoformat(ts).timestamp()
      for ts in history.timestamps[-limit:]
    ] if history else [datetime.now().timestamp()]

    start_time = datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
    end_time = datetime.fromtimestamp(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')

    def update_plot(plot, timestamps, values, label, color):
      plot.clear()
      plot.addLegend()
      values = [x for x in values if x is not None]
      if values:
        values = values[-limit:]
        plot.plot(timestamps, values, pen=pg.mkPen(color=color, width=2), name=label)
      else:
        plot.plot([0], [0], pen=None, symbol='o', symbolBrush=color, name='NO DATA')
      plot.setLabel('left', text=label, color=color)
      plot.setLabel('bottom', text='Time', color=color)
      if timestamps:
        plot.setLabel('bottom', f"Time ({start_time} to {end_time})", color=color)
      plot.getAxis('bottom').autoVisible = False
      plot.getAxis('bottom').enableAutoSIPrefix(False)

    color = 'white' if self._current_stylesheet == DARK_STYLESHEET else 'black'
    self.add_log(f'Plotting data: {len(timestamps)} timestamps with color: {color}')

    # CPU Load
    cpu_data = history.cpu_load if history else []
    cpu_date_axis = DateAxisItem(orientation='bottom')
    cpu_date_axis.setTimestamps(timestamps, parent="cpu")
    self.cpu_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.cpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.cpu_plot.setAxisItems({'bottom': cpu_date_axis})
    self.cpu_plot.setTitle('CPU Load')
    update_plot(self.cpu_plot, timestamps, cpu_data, 'CPU Load', color)

    # Memory Load
    mem_data = history.occupied_memory if history else []
    mem_date_axis = DateAxisItem(orientation='bottom')
    mem_date_axis.setTimestamps(timestamps, parent="mem")
    self.memory_plot.getAxis('bottom').setTickSpacing(60, 10)
    self.memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
    self.memory_plot.setAxisItems({'bottom': mem_date_axis})
    self.memory_plot.setTitle('Memory Load')
    update_plot(self.memory_plot, timestamps, mem_data, 'Occupied Memory', color)

    # GPU Load if available
    if history and history.gpu_load:
      gpu_date_axis = DateAxisItem(orientation='bottom')
      gpu_date_axis.setTimestamps(timestamps, parent="gpu")
      self.gpu_plot.getAxis('bottom').setTickSpacing(60, 10)
      self.gpu_plot.getAxis('bottom').setStyle(tickTextOffset=10)
      self.gpu_plot.setAxisItems({'bottom': gpu_date_axis})
      self.gpu_plot.setTitle('GPU Load')
      update_plot(self.gpu_plot, timestamps, history.gpu_load, 'GPU Load', color)

    # GPU Memory if available
    if history and history.gpu_occupied_memory:
      gpumem_date_axis = DateAxisItem(orientation='bottom')
      gpumem_date_axis.setTimestamps(timestamps, parent="gpu_mem")
      self.gpu_memory_plot.getAxis('bottom').setTickSpacing(60, 10)
      self.gpu_memory_plot.getAxis('bottom').setStyle(tickTextOffset=10)
      self.gpu_memory_plot.setAxisItems({'bottom': gpumem_date_axis})
      self.gpu_memory_plot.setTitle('GPU Memory Load')
      update_plot(self.gpu_memory_plot, timestamps, history.gpu_occupied_memory, 'Occupied GPU Memory', color)

  def refresh_local_address(self):
    """Fetch and display node address information.
    
    This method fetches node address information from the container and updates the UI.
    It handles errors and timeouts gracefully.
    """
    if not self.is_container_running():
        self.addressDisplay.setText('Address: Node not running')
        self.ethAddressDisplay.setText('ETH Address: Not available')
        self.nameDisplay.setText('')
        self.copyAddrButton.hide()
        self.copyEthButton.hide()
        return

    def on_success(node_info: NodeInfo) -> None:
        self.node_name = node_info.alias
        self.nameDisplay.setText('Name: ' + node_info.alias)

        if node_info.address != self.node_addr:
            self.node_addr = node_info.address
            self.node_eth_address = node_info.eth_address

            # Format addresses with clear labels and truncated values
            str_display = f"Address: {node_info.address[:16]}...{node_info.address[-8:]}"
            self.addressDisplay.setText(str_display)
            self.copyAddrButton.setVisible(bool(node_info.address))
            
            str_eth_display = f"ETH Address: {node_info.eth_address[:16]}...{node_info.eth_address[-8:]}"
            self.ethAddressDisplay.setText(str_eth_display)
            self.copyEthButton.setVisible(bool(node_info.eth_address))
            
            self.add_log(f'Node info updated: {self.node_addr} : {self.node_name}, ETH: {self.node_eth_address}')

    def on_error(error):
        self.add_log(f'Error getting node info: {error}', debug=True)
        self.addressDisplay.setText('Address: Error getting node info')
        self.ethAddressDisplay.setText('ETH Address: Not available')
        self.nameDisplay.setText('')
        self.copyAddrButton.hide()
        self.copyEthButton.hide()
        
        # If this is a timeout error, log it more prominently
        if "timed out" in error.lower():
            self.add_log("Node info request timed out. This may indicate network issues or high load on the remote host.", color="red")

    try:
        self.docker_handler.get_node_info(on_success, on_error)
    except Exception as e:
        self.add_log(f"Failed to start node info request: {str(e)}", debug=True, color="red")
        on_error(str(e))

  def maybe_refresh_uptime(self):
    # update uptime, epoch and epoch avail
    uptime = self.__current_node_uptime
    node_epoch = self.__current_node_epoch
    node_epoch_avail = self.__current_node_epoch_avail
    ver = self.__current_node_ver
    color = 'black'
    if not self.container_last_run_status:
      uptime = "STOPPED"
      node_epoch = "N/A"
      node_epoch_avail = 0
      ver = "N/A"
      color = 'red'
    #end if overwrite if stopped      
    if uptime != self.__display_uptime:
      if self.__display_uptime is not None and node_epoch_avail is not None and node_epoch_avail > 0:
        color = 'green'
        
      self.node_uptime.setText(f'Up Time: {uptime}')
      self.node_uptime.setStyleSheet(f'color: {color}')
      
      self.node_epoch.setText(f'Epoch: {node_epoch}')
      self.node_epoch.setStyleSheet(f'color: {color}')
      
      prc = round(node_epoch_avail * 100 if node_epoch_avail > 0 else node_epoch_avail, 2) if node_epoch_avail is not None else 0
      self.node_epoch_avail.setText(f'Epoch avail: {prc}%')
      self.node_epoch_avail.setStyleSheet(f'color: {color}')
      
      self.node_version.setText(f'Running ver: {ver}')
      self.node_version.setStyleSheet(f'color: {color}')
      
      self.__display_uptime = uptime
    return

  def copy_address(self):
    if not self.node_addr:
      self.toast.show_notification(NotificationType.ERROR, NOTIFICATION_ADDRESS_COPY_FAILED)
      return

    clipboard = QApplication.clipboard()
    clipboard.setText(self.node_addr)
    self.toast.show_notification(NotificationType.SUCCESS, NOTIFICATION_ADDRESS_COPIED.format(address=self.node_addr))
    return

  def copy_eth_address(self):
    if not self.node_eth_address:
      self.toast.show_notification(NotificationType.ERROR, NOTIFICATION_ADDRESS_COPY_FAILED)
      return

    clipboard = QApplication.clipboard()
    clipboard.setText(self.node_eth_address)
    self.toast.show_notification(NotificationType.SUCCESS, NOTIFICATION_ADDRESS_COPIED.format(address=self.node_eth_address))
    return

  def refresh_all(self):
    """Refresh all data and UI elements."""
    # Check if we're in simple mode
    is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
    
    # Check if we're in remote mode and not in simple mode
    if not is_simple_mode and hasattr(self, 'host_selector') and self.host_selector.is_multi_host_mode():
      # Get current host
      current_host = self.host_selector.get_current_host()
      if not current_host:
        return
        
      # Check host status in a non-blocking way
      # Connect to the host_status_updated signal for a one-time update
      self.host_selector.host_status_updated.connect(self._on_refresh_host_status_updated)
      
      # Start the status check
      self.host_selector.check_host_status(current_host)
    else:
      # For local mode or simple mode, just refresh container list and info
      self._refresh_local_containers()
    
    # Check for updates periodically
    if (time() - self.__last_auto_update_check) > AUTO_UPDATE_CHECK_INTERVAL:
      verbose = self.__last_auto_update_check == 0
      self.__last_auto_update_check = time()
      self.check_for_updates(verbose=verbose or FULL_DEBUG)

  def _on_refresh_host_status_updated(self, host_name, is_online):
    """Handle host status update during refresh."""
    # Disconnect from the signal to avoid multiple connections
    self.host_selector.host_status_updated.disconnect(self._on_refresh_host_status_updated)
    
    # Check if we're in simple mode
    is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
    
    if is_simple_mode:
        # In simple mode, skip SSH connection and proceed with local Docker
        self.add_log("Simple mode: skipping SSH connection, using local Docker")
        self._refresh_local_containers()
        return
    
    # Log the status update
    self.add_log(f"Host {host_name} status update: {'online' if is_online else 'offline'}")
    
    # If status has changed, handle it
    if is_online:
      # If host is online but we don't have a connection, try to reconnect
      if not hasattr(self, 'ssh_service') or not self.ssh_service or not self.ssh_service.check_connection():
        self.add_log(f"Host {host_name} is online, checking connection...")
        # Get SSH command for the host
        ssh_command = self.host_selector.get_ssh_command(host_name)
        if ssh_command:
          # Set up remote connection
          self.set_remote_connection(ssh_command)
          self.docker_handler.set_remote_connection(ssh_command)
          self.add_log(f"Connected to host: {host_name}")
          
          # In pro mode, specifically check for edge_node_container
          if hasattr(self, 'mode_switch') and self.mode_switch.is_pro_mode():
            # Check if edge_node_container exists and is running
            stdout, stderr, return_code = self.ssh_service.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
            if return_code == 0:
              containers = [name.strip() for name in stdout.split('\n') if name.strip() and (name.strip() == 'edge_node_container' or name.strip().startswith('edge_node_container'))]
              if containers:
                self.add_log(f"Found container on remote host: {containers[0]}")
                # Set the container in the docker handler
                self.docker_handler.set_container_name(containers[0])
                
                # Update the container combo box
                self.refresh_container_list()
                index = self.container_combo.findText(containers[0])
                if index >= 0:
                  self.container_combo.setCurrentIndex(index)
                  
                # Refresh container info
                self._refresh_remote_containers()
              else:
                self.add_log(f"No edge_node_container found on host {host_name}")
                self.toggleButton.setText("No Container Found")
                self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                self.toggleButton.setEnabled(False)
            else:
              self.add_log(f"Error checking for containers on host {host_name}")
          else:
            # For non-pro mode, just refresh container list and info
            self._refresh_remote_containers()
      else:
        # Connection is already established, just refresh container info
        self.add_log(f"Connection to {host_name} is active, refreshing containers")
        
        # In pro mode, specifically check for edge_node_container
        if hasattr(self, 'mode_switch') and self.mode_switch.is_pro_mode():
          # Check if edge_node_container exists and is running
          stdout, stderr, return_code = self.ssh_service.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
          if return_code == 0:
            containers = [name.strip() for name in stdout.split('\n') if name.strip() and (name.strip() == 'edge_node_container' or name.strip().startswith('edge_node_container'))]
            if containers:
              self.add_log(f"Found container on remote host: {containers[0]}")
              # Set the container in the docker handler
              self.docker_handler.set_container_name(containers[0])
              
              # Update the container combo box
              self.refresh_container_list()
              index = self.container_combo.findText(containers[0])
              if index >= 0:
                self.container_combo.setCurrentIndex(index)
        
        self._refresh_remote_containers()
    else:
      # Host is offline
      self.add_log(f"Host {host_name} is offline")
      self.toggleButton.setText("Host Offline")
      self.toggleButton.setStyleSheet("background-color: gray; color: white;")
      self.toggleButton.setEnabled(False)

  def _refresh_local_containers(self):
    """Refresh local container list and info."""
    try:
        # Refresh container list
        self.refresh_container_list()
        
        # Update container info if running
        if self.is_container_running():
            try:
                # Refresh address first (usually faster)
                self.refresh_local_address()
                
                # Then plot data (can be slower)
                try:
                    self.plot_data()
                except Exception as e:
                    self.add_log(f"Error plotting data for local container: {str(e)}", debug=True, color="red")
            except Exception as e:
                self.add_log(f"Error refreshing local container info: {str(e)}", color="red")
        
        # Always update the toggle button text
        self.update_toggle_button_text()
    except Exception as e:
        self.add_log(f"Error in local container refresh: {str(e)}", color="red")
        # Ensure toggle button text is updated even if there's an error
        self.update_toggle_button_text()

  def _refresh_remote_containers(self):
    """Refresh remote container list and info."""
    try:
        # Refresh container list
        self.refresh_container_list()
        
        # Update container info if running
        if self.is_container_running():
            # Set a timeout for these operations
            self.add_log("Refreshing remote container information...", debug=True)
            
            # Use a timer to prevent UI freezing if operations take too long
            refresh_timer = QTimer(self)
            refresh_timer.setSingleShot(True)
            refresh_timer.timeout.connect(lambda: self.add_log("Remote container refresh timed out, operations may be incomplete", color="red"))
            refresh_timer.start(30000)  # 30 second timeout
            
            try:
                # Refresh address first (usually faster)
                self.refresh_local_address()
                
                # Then plot data (can be slower)
                try:
                    self.plot_data()
                except Exception as e:
                    self.add_log(f"Error plotting data for remote container: {str(e)}", debug=True, color="red")
                
                # Stop the timer if we completed successfully
                refresh_timer.stop()
            except Exception as e:
                self.add_log(f"Error refreshing remote container info: {str(e)}", color="red")
                refresh_timer.stop()
        
        # Always update the toggle button text
        self.update_toggle_button_text()
    except Exception as e:
        self.add_log(f"Error in remote container refresh: {str(e)}", color="red")
        # Ensure toggle button text is updated even if there's an error
        self.update_toggle_button_text()

  def dapp_button_clicked(self):
    import webbrowser
    dapp_url = DAPP_URLS.get(self.current_environment)
    if dapp_url:
      webbrowser.open(dapp_url)
      self.add_log(f'Opening dApp URL: {dapp_url}', debug=True)
    else:
      self.add_log(f'Unknown environment: {self.current_environment}', debug=True)
      self.toast.show_notification(
        NotificationType.ERROR,
        f'Unknown environment: {self.current_environment}'
      )
    return
  
  
  def explorer_button_clicked(self):
    self.toast.show_notification(
      NotificationType.INFO,
      'Ratio1 Explorer is not yet implemented'
    )
    return
  
  
  def toggle_force_debug(self):
    self.__force_debug = self.force_debug_checkbox.isChecked()
    if self.__force_debug:
      self.add_log('Force Debug enabled.')
    else:
      self.add_log('Force Debug disabled.')
    return

  def show_rename_dialog(self):
    if not self.is_container_running():
        self.toast.show_notification(NotificationType.ERROR, "Container not running. Could not rename node.")
        return

    dialog = QDialog(self)
    dialog.setWindowTitle('Rename Node')
    dialog_layout = QVBoxLayout()

    # Add note about max length
    note_label = QLabel(f"Note: Maximum node name length is {MAX_ALIAS_LENGTH} characters")
    note_label.setStyleSheet("color: gray; font-style: italic;")
    dialog_layout.addWidget(note_label)

    # Text input field
    text_edit = QTextEdit()
    text_edit.setText(self.node_name)
    text_edit.setFixedHeight(50)
    dialog_layout.addWidget(text_edit)

    # Button layout
    button_layout = QHBoxLayout()
    
    save_button = QPushButton('Save')
    save_button.clicked.connect(lambda: self.validate_and_save_node_name(text_edit.toPlainText(), dialog))
    button_layout.addWidget(save_button)

    cancel_button = QPushButton('Cancel')
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_button)

    dialog_layout.addLayout(button_layout)
    dialog.setLayout(dialog_layout)
    dialog.exec_()

  def validate_and_save_node_name(self, new_name: str, dialog: QDialog):
    new_name = new_name.strip()
    if len(new_name) > MAX_ALIAS_LENGTH:
        # Show warning dialog
        warning_dialog = QDialog(dialog)
        warning_dialog.setWindowTitle("Warning: Name Too Long")
        layout = QVBoxLayout()
        
        # Add message
        warning_msg = f"The node name is too long ({len(new_name)} characters).\n\n"
        warning_msg += f"'{new_name}' will be truncated to '{new_name[:MAX_ALIAS_LENGTH]}'\n\n"
        warning_msg += "Do you want to proceed?"
        
        label = QLabel(warning_msg)
        layout.addWidget(label)
        
        # Add buttons
        button_layout = QHBoxLayout()
        proceed_btn = QPushButton("Proceed")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addWidget(proceed_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        warning_dialog.setLayout(layout)
        
        # Connect buttons
        proceed_btn.clicked.connect(warning_dialog.accept)
        cancel_btn.clicked.connect(warning_dialog.reject)
        
        if warning_dialog.exec_() == QDialog.Accepted:
            new_name = new_name[:MAX_ALIAS_LENGTH]
        else:
            return  # Return to editing if user cancels
    
    def on_success(data: dict) -> None:
        self.add_log('Successfully renamed node, restarting container...', debug=True)
        self.toast.show_notification(
            NotificationType.SUCCESS,
            'Node renamed successfully. Restarting...'
        )
        dialog.accept()
        
        # Stop and restart the container
        self.stop_container()
        self.launch_container()
        self.post_launch_setup()
        self.refresh_local_address()

    def on_error(error: str) -> None:
        self.add_log(f'Error renaming node: {error}', debug=True)
        self.toast.show_notification(
            NotificationType.ERROR,
            'Failed to rename node'
        )

    self.docker_handler.update_node_name(new_name, on_success, on_error)

  def _clear_info_display(self):
    """Clear all information displays."""
    # Set text color based on theme
    text_color = "white" if self._current_stylesheet == DARK_STYLESHEET else "black"
    
    # Set text and color for each label
    self.addressDisplay.setText('Address: Not available')
    self.addressDisplay.setStyleSheet(f"color: {text_color};")
    self.copyAddrButton.hide()
    
    self.ethAddressDisplay.setText('ETH Address: Not available')
    self.ethAddressDisplay.setStyleSheet(f"color: {text_color};")
    self.copyEthButton.hide()
    
    self.nameDisplay.setText('')
    self.nameDisplay.setStyleSheet(f"color: {text_color};")
    
    self.node_uptime.setText(UPTIME_LABEL)
    self.node_uptime.setStyleSheet(f"color: {text_color};")
    
    self.node_epoch.setText(EPOCH_LABEL)
    self.node_epoch.setStyleSheet(f"color: {text_color};")
    
    self.node_epoch_avail.setText(EPOCH_AVAIL_LABEL)
    self.node_epoch_avail.setStyleSheet(f"color: {text_color};")
    
    self.node_version.setText('')
    self.node_version.setStyleSheet(f"color: {text_color};")
    
    # Reset state variables
    self.__display_uptime = None
    self.node_addr = None
    self.node_eth_address = None
    self.__current_node_uptime = -1
    self.__current_node_epoch = -1
    self.__current_node_epoch_avail = -1
    self.__current_node_ver = -1
    self.__last_plot_data = None
    self.__last_timesteps = []
    
    # Clear all graphs
    self.cpu_plot.clear()
    self.memory_plot.clear()
    self.gpu_plot.clear()
    self.gpu_memory_plot.clear()
    
    # Reset graph titles and labels with current theme color
    for plot in [self.cpu_plot, self.memory_plot, self.gpu_plot, self.gpu_memory_plot]:
        plot.setTitle('')
        plot.setLabel('left', '')
        plot.setLabel('bottom', '')
    
    # Update toggle button state and color
    self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.setStyleSheet("background-color: green; color: white;")

  def _on_host_selected(self, host_name: str):
    """Handle host selection."""
    # Clear current display and state
    self._clear_info_display()
    
    if not host_name:
        return
    
    # Check if we're in simple mode
    is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
    
    if is_simple_mode:
        # In simple mode, skip SSH connection and proceed with local Docker
        self.add_log("Simple mode: skipping SSH connection, using local Docker")
        self.toggleButton.setEnabled(True)
        self.update_toggle_button_text()
        self.refresh_container_list()
        return
        
    # Disable button and show checking status
    self.toggleButton.setText("Checking Host...")
    self.toggleButton.setStyleSheet("background-color: gray; color: white;")
    self.toggleButton.setEnabled(False)
    
    self.add_log(f"Host selected: {host_name}, checking status...")
        
    ssh_command = self.host_selector.get_ssh_command(host_name)
    if not ssh_command:
        self.add_log(f"Failed to get SSH command for host: {host_name}")
        self.toast.show_notification(NotificationType.ERROR, f"Failed to get SSH command for host: {host_name}")
        self.toggleButton.setText("SSH Error")
        self.toggleButton.setStyleSheet("background-color: gray; color: white;")
        self.toggleButton.setEnabled(False)
        return

    # Connect to the host_status_updated signal
    self.host_selector.host_status_updated.connect(self._on_host_status_updated)
    
    # Force a fresh status check
    self.host_selector.check_host_status(host_name)

  def _on_host_status_updated(self, host_name: str, is_online: bool):
    """Handle host status update."""
    # Disconnect from the signal to avoid multiple connections
    self.host_selector.host_status_updated.disconnect(self._on_host_status_updated)
    
    # Check if we're in simple mode
    is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
    
    if is_simple_mode:
        # In simple mode, skip SSH connection and proceed with local Docker
        self.add_log("Simple mode: skipping SSH connection, using local Docker")
        self.toggleButton.setEnabled(True)
        self.update_toggle_button_text()
        self.refresh_container_list()
        return
    
    if not is_online:
        self.add_log(f"Host {host_name} is offline")
        self.toggleButton.setText("Host Offline")
        self.toggleButton.setStyleSheet("background-color: gray; color: white;")
        self.toggleButton.setEnabled(False)
        self.toast.show_notification(NotificationType.ERROR, f"Host {host_name} is offline")
        return
    
    # Only proceed with connection if host is online
    ssh_command = self.host_selector.get_ssh_command(host_name)
    if ssh_command:
        self._check_host_connection(host_name, ssh_command)

  def _check_host_connection(self, host_name: str, ssh_command: str):
    """Check connection and Docker status for a host."""
    try:
        # Check if we're in simple mode - if so, skip SSH connection
        is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
        
        if not is_simple_mode:
            # Set up remote connection only in pro mode
            self.set_remote_connection(ssh_command)
            
            # Test SSH connection first
            if not self.ssh_service.check_connection():
                raise Exception("Failed to establish SSH connection")
                
            self.docker_handler.set_remote_connection(ssh_command)
            self.add_log(f"Connected to remote host: {host_name}")
            
            # Check if Docker is available on the remote host
            stdout, stderr, return_code = self.ssh_service.execute_command(['docker', '--version'])
            if return_code != 0:
                self.add_log(f"Docker not found on host {host_name}")
                self.toggleButton.setText("Docker Not Found")
                self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                self.toggleButton.setEnabled(False)
                self.toast.show_notification(NotificationType.ERROR, f"Docker not found on host {host_name}")
                return
            
            # Check if Docker daemon is running
            stdout, stderr, return_code = self.ssh_service.execute_command(['docker', 'info'])
            if return_code != 0:
                self.add_log(f"Docker daemon not running on host {host_name}")
                self.toggleButton.setText("Docker Not Running")
                self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                self.toggleButton.setEnabled(False)
                self.toast.show_notification(NotificationType.ERROR, f"Docker daemon not running on host {host_name}")
                return
            
            self.add_log(f"Docker is available on host {host_name}")
        else:
            # In simple mode, just check if Docker is available locally
            self.add_log("Simple mode: skipping SSH connection, using local Docker")
            
            # Clear any remote connection settings to ensure we're using local Docker
            self.clear_remote_connection()
            self.docker_handler.clear_remote_connection()
            
            # Check if Docker is available locally
            try:
                import subprocess
                result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
                if result.returncode != 0:
                    self.add_log("Docker not found locally")
                    self.toggleButton.setText("Docker Not Found")
                    self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                    self.toggleButton.setEnabled(False)
                    self.toast.show_notification(NotificationType.ERROR, "Docker not found locally")
                    return
                
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
                if result.returncode != 0:
                    self.add_log("Docker daemon not running locally")
                    self.toggleButton.setText("Docker Not Running")
                    self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                    self.toggleButton.setEnabled(False)
                    self.toast.show_notification(NotificationType.ERROR, "Docker daemon not running locally")
                    return
                
                self.add_log("Docker is available locally")
            except Exception as e:
                self.add_log(f"Error checking Docker: {str(e)}")
                self.toggleButton.setText("Docker Check Failed")
                self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                self.toggleButton.setEnabled(False)
                self.toast.show_notification(NotificationType.ERROR, f"Failed to check Docker: {str(e)}")
                return
        
        # In pro mode, specifically check for edge_node_container
        if hasattr(self, 'mode_switch') and self.mode_switch.is_pro_mode():
            # Check if edge_node_container exists
            stdout, stderr, return_code = self.ssh_service.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
            if return_code == 0:
                containers = [name.strip() for name in stdout.split('\n') if name.strip() and (name.strip() == 'edge_node_container' or name.strip().startswith('edge_node_container'))]
                if containers:
                    self.add_log(f"Found container on remote host: {containers[0]}")
                    # Set the container in the docker handler
                    self.docker_handler.set_container_name(containers[0])
                    
                    # Update the container combo box
                    self.refresh_container_list()
                    index = self.container_combo.findText(containers[0])
                    if index >= 0:
                        self.container_combo.setCurrentIndex(index)
                else:
                    self.add_log(f"No edge_node_container found on host {host_name}")
                    self.toggleButton.setText("No Container Found")
                    self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                    self.toggleButton.setEnabled(False)
                    self.toast.show_notification(NotificationType.WARNING, f"No edge_node_container found on host {host_name}")
                    return
            else:
                self.add_log(f"Error checking for containers on host {host_name}")
                self.toggleButton.setText("Container Check Failed")
                self.toggleButton.setStyleSheet("background-color: gray; color: white;")
                self.toggleButton.setEnabled(False)
                self.toast.show_notification(NotificationType.ERROR, f"Failed to check for containers on host {host_name}")
                return
        else:
            # For non-pro mode, just refresh the container list
            self.refresh_container_list()
        
        self.toggleButton.setEnabled(True)
        
        # Refresh container status
        if self.is_container_running():
            self.post_launch_setup()
            self.refresh_local_address()
            self.plot_data()
        self.update_toggle_button_text()
        
    except Exception as e:
        # Clear any partial connection state
        self.clear_remote_connection()
        self.docker_handler.clear_remote_connection()
        
        self.add_log(f"Connection failed to host {host_name}: {str(e)}")
        self.toggleButton.setText("Connection Failed")
        self.toggleButton.setStyleSheet("background-color: gray; color: white;")
        self.toggleButton.setEnabled(False)
        self.toast.show_notification(NotificationType.ERROR, f"Failed to connect to host {host_name}")
        return

  def _on_host_mode_changed(self, is_multi_host: bool):
    """Handle mode change for host selector (multi-host mode)"""
    # Clear current display and state
    self._clear_info_display()
    
    if not is_multi_host:
        self.clear_remote_connection()
        self.docker_handler.clear_remote_connection()  # Clear remote connection for docker_handler
        self.add_log("Switched to local mode")
        self.toggleButton.setEnabled(True)
        # Refresh container status
        if self.is_container_running():
            self.post_launch_setup()
            self.refresh_local_address()
            self.plot_data()
        self.update_toggle_button_text()
    else:
        self.add_log("Switched to multi-host mode")
        self.toggleButton.setEnabled(False)  # Disable toggle button until a host is selected
        
        # Check the initial host if one is selected
        current_host = self.host_selector.get_current_host()
        if current_host:
            self._on_host_selected(current_host)  # This will check the host's status

  def _on_simple_pro_mode_changed(self, is_pro_mode):
    """Handle mode change between simple and pro"""
    self.add_log(f'Switched to {"pro" if is_pro_mode else "simple"} mode')
    
    # Update host selector pro mode state
    self.host_selector.set_pro_mode(is_pro_mode)
    
    # Handle UI visibility and functionality based on mode
    if is_pro_mode:
      # Show host selector for remote connections
      self.host_selector.show()
      
      # Hide container dropdown and add node button in pro mode
      self.container_combo.hide()
      self.add_node_button.hide()
      
      # Clear any existing container info
      self._clear_info_display()
      
      # Disable toggle button until a host is selected and verified
      self.toggleButton.setText("Select Host...")
      self.toggleButton.setStyleSheet("background-color: gray; color: white;")
      self.toggleButton.setEnabled(False)
      
      # Check the initial host if one is selected
      current_host = self.host_selector.get_current_host()
      if current_host:
        # Use QTimer to delay the host selection to avoid blocking the UI
        QTimer.singleShot(100, lambda: self._on_host_selected(current_host))
    else:
      # Hide host selector in simple mode
      self.host_selector.hide()
      
      # Show container dropdown and add node button in simple mode
      self.container_combo.show()
      self.add_node_button.show()
      
      # Clear any remote connections
      self.clear_remote_connection()
      self.docker_handler.clear_remote_connection()
      
      # Reset toggle button
      self.update_toggle_button_text()

  def open_docker_download(self):
    """Open Docker download page in default browser."""
    import webbrowser
    webbrowser.open('https://docs.docker.com/get-docker/')

  def _on_container_selected(self, container_name: str):
    """Handle container selection and update dashboard display"""
    if not container_name:
        self._clear_info_display()
        return
        
    try:
        # Update docker handler with new container
        self.docker_handler.set_container_name(container_name)
        
        # Update UI elements
        self.update_toggle_button_text()
        
        # If container is running, update all information displays
        if self.is_container_running():
            self.post_launch_setup()
            self.refresh_local_address()  # Updates address, ETH address, and name displays
            self.plot_data()  # Updates graphs and metrics
            self.maybe_refresh_uptime()  # Updates uptime, epoch, and version info
            self.add_log(f"Selected container: {container_name}", debug=True)
        else:
            self._clear_info_display()
            self.add_log(f"Selected container {container_name} is not running", debug=True)
            
    except Exception as e:
        self._clear_info_display()
        self.add_log(f"Error selecting container {container_name}: {str(e)}", debug=True, color="red")
        self.toast.show_notification(NotificationType.ERROR, f"Error selecting container: {str(e)}")

  def show_add_node_dialog(self):
    """Show confirmation dialog for adding a new node."""
    from PyQt5.QtWidgets import QMessageBox
    
    # Generate the container name that would be used
    container_name = generate_container_name()
    volume_name = get_volume_name(container_name)
    
    # Create confirmation dialog
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle("Add New Node")
    msg.setText("Would you like to create a new edge node?")
    msg.setInformativeText(f"This will create:\nContainer: {container_name}\nVolume: {volume_name}")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    
    # Show dialog and handle response
    if msg.exec_() == QMessageBox.Yes:
        self.add_new_node(container_name, volume_name)

  def add_new_node(self, container_name: str, volume_name: str):
    """Add a new edge node container.
    
    Args:
        container_name: Name for the new container
        volume_name: Name for the container's volume
    """
    try:
        # Set the container name in the Docker handler
        self.docker_handler.set_container_name(container_name)
        
        # Launch the container
        self.launch_container(volume_name=volume_name)
        
        # Refresh the container list
        self.refresh_container_list()
        
        # Select the new container
        index = self.container_combo.findText(container_name)
        if index >= 0:
            self.container_combo.setCurrentIndex(index)
        
        # Show success message
        self.add_log(f"Successfully created new node: {container_name}", color="green")
        
    except Exception as e:
        self.add_log(f"Failed to create new node: {str(e)}", color="red")

  def get_edge_node_containers(self) -> list:
    """Get list of all edge node containers"""
    containers = []
    try:
      # In pro mode with remote host, we only look for the specific edge_node_container
      if hasattr(self, 'mode_switch') and self.mode_switch.is_pro_mode() and self.host_selector.is_multi_host_mode():
        self.add_log("Pro mode with remote host: Looking for edge_node_container", debug=True)
        stdout, stderr, return_code = self.docker_handler.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
        if return_code == 0:
          # In pro mode, we only care about the exact container name
          containers = [name.strip() for name in stdout.split('\n') if name.strip() == 'edge_node_container']
          if not containers and 'edge_node_container' not in stdout:
            # If we didn't find the exact container, check if it exists with a suffix
            stdout, stderr, return_code = self.docker_handler.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
            if return_code == 0:
              containers = [name.strip() for name in stdout.split('\n') if name.strip().startswith('edge_node_container')]
              if containers:
                self.add_log(f"Found container with prefix: {containers[0]}", debug=True)
      else:
        # Get all containers that match our pattern for local mode
        stdout, stderr, return_code = self.docker_handler.execute_command(['docker', 'ps', '-a', '--format', '{{.Names}}'])
        if return_code == 0:
          containers = [name.strip() for name in stdout.split('\n') if name.strip().startswith('edge_node_container_')]
    except Exception as e:
      self.add_log(f"Error getting containers: {str(e)}", debug=True)
    
    self.add_log(f"Found containers: {containers}", debug=True)
    return containers

  def launch_container(self, volume_name: str):
    """Launch the currently selected container"""
    self.add_log(f'Launching container {self.docker_handler.container_name} with volume {volume_name}...')
    self.docker_handler.launch_container(volume_name=volume_name)
    
    # Update UI after launch
    self.post_launch_setup()
    self.refresh_local_address()
    self.plot_data()
    self.update_toggle_button_text()

  def refresh_container_list(self):
    """Refresh the dropdown list of containers"""
    try:
      # Store current selection
      current_container = self.container_combo.currentText()
      
      # Clear and repopulate the list
      self.container_combo.clear()
      containers = self.get_edge_node_containers()
      for container in containers:
        self.container_combo.addItem(container)
        
      # Restore previous selection if it exists, otherwise select first item
      if current_container and current_container in containers:
        self.container_combo.setCurrentText(current_container)
      elif containers:
        self.container_combo.setCurrentIndex(0)
        
    except Exception as e:
      self.add_log(f"Error refreshing container list: {str(e)}", debug=True, color="red")

  def is_container_running(self):
    """Check if the currently selected container is running.
    
    This method uses the docker_handler to check if the container is running.
    It properly handles both local and remote containers.
    
    Returns:
        bool: True if the container is running, False otherwise
    """
    try:
        # Check if we're in simple mode
        is_simple_mode = hasattr(self, 'mode_switch') and not self.mode_switch.is_pro_mode()
        
        # Make sure we have a container name selected
        container_name = self.container_combo.currentText()
        if not container_name:
            # In pro mode with remote host, we might need to check for edge_node_container directly
            if not is_simple_mode and hasattr(self, 'mode_switch') and self.mode_switch.is_pro_mode() and self.host_selector.is_multi_host_mode():
                # Check if we have a remote connection
                if hasattr(self, 'ssh_service') and self.ssh_service and self.ssh_service.check_connection():
                    self.add_log("Pro mode with remote host: Checking edge_node_container status directly", debug=True)
                    # Check if edge_node_container is running
                    stdout, stderr, return_code = self.ssh_service.execute_command(['docker', 'ps', '--format', '{{.Names}}', '--filter', 'name=edge_node_container'])
                    if return_code == 0:
                        containers = [name.strip() for name in stdout.split('\n') if name.strip() and (name.strip() == 'edge_node_container' or name.strip().startswith('edge_node_container'))]
                        if containers:
                            self.add_log(f"Found running container on remote host: {containers[0]}", debug=True)
                            # Set the container in the docker handler
                            self.docker_handler.set_container_name(containers[0])
                            # Update the container combo box
                            self.refresh_container_list()
                            return True
            return False
            
        # Make sure the docker handler has the correct container name
        self.docker_handler.set_container_name(container_name)
        
        # Use the docker handler to check if the container is running
        is_running = self.docker_handler.is_container_running()
        
        # Log status changes for debugging
        if hasattr(self, 'container_last_run_status') and self.container_last_run_status != is_running:
            self.add_log(f'Container {container_name} status changed: {self.container_last_run_status} -> {is_running}', debug=True)
            self.container_last_run_status = is_running
            
        return is_running
    except Exception as e:
        self.add_log(f"Error checking if container is running: {str(e)}", debug=True, color="red")
        return False