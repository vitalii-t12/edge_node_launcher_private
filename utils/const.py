from ver import __VER__

FULL_DEBUG = True

# ============================================================================
# DIRECTORY AND FILE CONSTANTS
# ============================================================================
HOME_SUBFOLDER = ".naeural_launcher"
CONFIG_DIR = ".ratio1/edge_node_launcher"
E2_PEM_FILE = 'e2.pem'

# ============================================================================
# DOCKER CONSTANTS
# ============================================================================
DOCKER_VOLUME = 'naeural_vol'
DOCKER_IMAGE = 'naeural/edge_node'
DOCKER_TAG = 'testnet'
DOCKER_CONTAINER_NAME = 'r1node'
DOCKER_VOLUME_PATH = '/edge_node/_local_cache'

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
SHOW_MODE_SWITCH = False  # Whether to show the Simple/Pro mode switch in the UI
REFRESH_TIME = 20_000
MAX_HISTORY_QUEUE = 5 * 60 // 10  # 5 minutes @ 10 seconds each hb
AUTO_UPDATE_CHECK_INTERVAL = 60
MAX_ALIAS_LENGTH = 15  # Maximum length for aliases (node name and authorized addresses)

# ============================================================================
# UI TEXT CONSTANTS
# ============================================================================
# Window and titles
WINDOW_TITLE = f'Edge Node Manager v{__VER__}'

# Button texts
LAUNCH_CONTAINER_BUTTON_TEXT = 'Launch Edge Node'
STOP_CONTAINER_BUTTON_TEXT = 'Stop Edge Node'
DAPP_BUTTON_TEXT = 'Launch dApp'
EXPLORER_BUTTON_TEXT = 'Ratio1 Explorer'
DELETE_AND_RESTART_BUTTON_TEXT = 'Reset Node Address'
REFRESH_LOCAL_ADDRESS_BUTTON_TEXT = 'Refresh Local Address'
COPY_ADDRESS_BUTTON_TEXT = 'Copy Address'
COPY_ETHEREUM_ADDRESS_BUTTON_TEXT = 'Copy Ethereum Address'
RENAME_NODE_BUTTON_TEXT = 'Change Node Alias'
LIGHT_DASHBOARD_BUTTON_TEXT = 'Switch to Light Theme'
DARK_DASHBOARD_BUTTON_TEXT = 'Switch to Dark Theme'
DOWNLOAD_DOCKER_BUTTON_TEXT = 'Download Docker'

# Label texts
LOCAL_NODE_ADDRESS_LABEL_TEXT = 'Local Node Address'
UPTIME_LABEL = 'Up Time:'
EPOCH_LABEL = 'Epoch:'
EPOCH_AVAIL_LABEL = 'Epochs avail:'
NODE_VERSION_LABEL = 'Running ver:'

# Status texts
NO_CONTAINER_SELECTED_TEXT = 'Address: No container selected'
ETH_ADDRESS_NOT_AVAILABLE_TEXT = 'ETH Address: Not available'
NODE_NOT_RUNNING_TEXT = 'Address: Node not running'
ERROR_GETTING_NODE_INFO_TEXT = 'Address: Error getting node info'
NAME_PREFIX_TEXT = 'Name: '
ADDRESS_PREFIX_TEXT = 'Address: '
LOCAL_ADDRESS_PREFIX_TEXT = 'Local Address: '
ETH_ADDRESS_PREFIX_TEXT = 'ETH Address: '
UPTIME_PREFIX_TEXT = 'Uptime: '
EMPTY_DASH_TEXT = '-'

# Button states
NO_CONTAINER_FOUND_TEXT = 'No Container Found'
HOST_OFFLINE_TEXT = 'Host Offline'
CHECKING_HOST_TEXT = 'Checking Host...'
SSH_ERROR_TEXT = 'SSH Error'
DOCKER_NOT_FOUND_TEXT = 'Docker Not Found'
DOCKER_NOT_RUNNING_TEXT = 'Docker Not Running'
DOCKER_CHECK_FAILED_TEXT = 'Docker Check Failed'
CONTAINER_CHECK_FAILED_TEXT = 'Container Check Failed'
CONNECTION_FAILED_TEXT = 'Connection Failed'
SELECT_HOST_TEXT = 'Select Host...'

# Plot titles
CPU_LOAD_TITLE = 'CPU Load'
MEMORY_USAGE_TITLE = 'Memory Usage'
GPU_LOAD_TITLE = 'GPU Load'
GPU_MEMORY_LOAD_TITLE = 'GPU Memory Load'

# ============================================================================
# TOOLTIP TEXTS
# ============================================================================
DOCKER_DOWNLOAD_TOOLTIP = 'Ratio1 Edge Node requires Docker Desktop running in parallel'
COPY_ADDRESS_TOOLTIP = 'Copy address'
COPY_ETH_ADDRESS_TOOLTIP = 'Copy Ethereum address'

# ============================================================================
# DIALOG TEXTS
# ============================================================================
# Dialog titles
ADD_NEW_NODE_DIALOG_TITLE = 'Add New Node'
RENAME_NODE_DIALOG_TITLE = 'Rename Node'
EDIT_AUTHORIZED_ADDRESSES_DIALOG_TITLE = 'Edit Authorized Addresses'
VIEW_CONFIG_FILES_DIALOG_TITLE = 'View Configuration Files'
EDIT_ENV_FILE_DIALOG_TITLE = 'Edit .env File'

# Dialog messages
RESET_NODE_CONFIRMATION_TEXT = 'Are you sure you want to reset this node?'
ENTER_NODE_NAME_TEXT = 'Enter a friendly name for this node:'
RESETTING_NODE_ADDRESS_TEXT = 'Resetting node address...'

# Input placeholders
ENTER_NODE_NAME_PLACEHOLDER = 'Enter node name'
ENTER_FRIENDLY_NODE_NAME_PLACEHOLDER = 'Enter a friendly name for your node'
ENTER_ADDRESS_PLACEHOLDER = 'Enter address'
ENTER_ALIAS_PLACEHOLDER = 'Enter alias'

# ============================================================================
# LOG MESSAGES
# ============================================================================
SUCCESS_NODE_CREATION_LOG = 'Successfully created new node: {}'
FAILED_NODE_CREATION_LOG = 'Failed to create new node: {}'

# ============================================================================
# ENVIRONMENT SETTINGS
# ============================================================================
ENVIRONMENTS = {
    'mainnet': 'Mainnet',
    'testnet': 'Testnet',
    'devnet': 'Devnet'
}

DAPP_URLS = {
    'mainnet': 'https://app.ratio1.ai/',
    'testnet': 'https://testnet-app.ratio1.ai/',
    'devnet': 'https://devnet-app.ratio1.ai/'
}

DEFAULT_ENVIRONMENT = 'testnet'

# ============================================================================
# TEMPLATES
# ============================================================================
ENV_TEMPLATE = '''
# LOCAL FILE TEMPLATE

# admin
EE_ID={}
EE_SUPERVISOR=false
EE_DEVICE=cuda:0


# MinIO / S3
EE_MINIO_ENDPOINT=endpoint
EE_MINIO_ACCESS_KEY=access_key
EE_MINIO_SECRET_KEY=secret_key
EE_MINIO_SECURE=false
EE_MINIO_UPLOAD_BUCKET=bucket


# MQTT
EE_MQTT_PORT=8883
EE_MQTT_SUBTOPIC=address
EE_MQTT_CERT=

EE_NGROK_AUTH_TOKEN=ngrok-auth-token
EE_NGROK_EDGE_LABEL=ngrok-edge-label

# Misc
EE_GITVER=token_for_accessing_private_repositories
EE_OPENAI=token_for_accessing_openai_api
EE_HF_TOKEN=token_for_accessing_huggingface_api
'''

# ============================================================================
# STYLESHEETS
# ============================================================================

# Common style properties that don't depend on theme
COMMON_STYLES = {
    "font_size": "14px",
    "border_radius": "5px",
    "progress_height": "30px",
    "button_padding": "10px 20px",
    "button_font_size": "16px",
    "button_margin": "4px 2px",
    "button_border_radius": "15px",
    "combo_border_radius": "4px",
    "combo_padding": "4px",
    "combo_min_width": "100px",
    "combo_dropdown_width": "20px",
    "text_align_center": "center"
}

# Color definitions for dark theme
DARK_COLORS = {
    "text_color": "white",
    "bg_color": "#2b2b2b",
    "border_color": "#555555",
    "hover_color": "#3b3b3b",
    "button_bg": "#1E90FF",
    "button_border": "#87CEEB",
    "button_hover": "#104E8B",
    "progress_border": "#1E90FF",
    "progress_chunk": "#1E90FF",
    "widget_bg": "#0D1F2D",
    "text_edit_bg": "#0D1F2D",
    "text_edit_border": "#1E90FF",
    "plot_bg": "#243447",
    "plot_border": "#87CEEB",
    "combo_bg": "#2b2b2b",
    "combo_border": "#555555",
    "combo_hover_bg": "#3b3b3b",
    "combo_hover_border": "#4CAF50",
    "combo_arrow_color": "white",
    "combo_dropdown_bg": "#2b2b2b",
    "combo_dropdown_select_bg": "#3b3b3b",
    "combo_dropdown_select_color": "white",
    "green_highlight": "#4CAF50",
    "button_copy_address_bg": "transparent"
}

# Color definitions for light theme
LIGHT_COLORS = {
    "text_color": "black",
    "bg_color": "white",
    "border_color": "#cccccc",
    "hover_color": "#f5f5f5",
    "button_bg": "#D3D3D3",
    "button_border": "#A9A9A9",
    "button_hover": "#A9A9A9",
    "progress_border": "#D3D3D3",
    "progress_chunk": "#D3D3D3",
    "widget_bg": "#F0F0F0",
    "text_edit_bg": "#FFFFFF",
    "text_edit_border": "#D3D3D3",
    "plot_bg": "#FFFFFF",
    "plot_border": "#A9A9A9",
    "combo_bg": "white",
    "combo_border": "#cccccc",
    "combo_hover_bg": "#f5f5f5",
    "combo_hover_border": "#4CAF50",
    "combo_arrow_color": "black",
    "combo_dropdown_bg": "white",
    "combo_dropdown_select_bg": "#f5f5f5",
    "combo_dropdown_select_color": "black",
    "green_highlight": "#4CAF50",
    "button_copy_address_bg": "transparent"
}

# Merge common styles with theme-specific colors
DARK_THEME = {**COMMON_STYLES, **DARK_COLORS}
LIGHT_THEME = {**COMMON_STYLES, **LIGHT_COLORS}

# Checkbox style template
CHECKBOX_STYLE_TEMPLATE = """
    QCheckBox {{
        color: {text_color};
    }}
"""

# Common stylesheet template with placeholders for theme-specific values
COMMON_STYLESHEET_TEMPLATE = """
  QLabel {{
    font-size: {font_size};
    color: {text_color};
  }}
  QProgressBar {{
    border: 2px solid {progress_border};
    border-radius: {border_radius};
    text-align: {text_align_center};
    height: {progress_height};
    color: {text_color};
  }}
  QProgressBar::chunk {{
    background-color: {progress_chunk};
  }}
  QDialog, QWidget {{
    background-color: {widget_bg};
  }}
  QTextEdit {{
    background-color: {text_edit_bg};
    color: {text_color};
    font-size: {font_size};
    border: 1px solid {text_edit_border};
    border-radius: {border_radius};
  }}
  
  PlotWidget {{
    background-color: {plot_bg};
    border: 1px solid {plot_border};
    color: {text_color};  
  }}

  PlotWidget LabelItem {{
    color: {text_color};
  }}
  
  QComboBox {{
    color: {text_color};
    background-color: {combo_bg};
    border: 1px solid {combo_border};
    border-radius: {combo_border_radius};
    padding: {combo_padding};
    min-width: {combo_min_width};
  }}
  QComboBox:hover {{
    background-color: {combo_hover_bg};
    border: 1px solid {green_highlight};
  }}
  QComboBox::drop-down {{
    border: none;
    width: {combo_dropdown_width};
  }}
  QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {combo_arrow_color};
    margin-right: 8px;
  }}
  QComboBox QAbstractItemView {{
    color: {text_color};
    background-color: {combo_dropdown_bg};
    selection-background-color: {combo_dropdown_select_bg};
    selection-color: {combo_dropdown_select_color};
  }}
  
  QCheckBox {{
    color: {text_color};
  }}
  
  QPushButton {{
    background-color: {button_bg}; 
    color: {text_color}; 
    border: 2px solid {button_border}; 
    padding: {button_padding}; 
    font-size: {button_font_size}; 
    margin: {button_margin};
    border-radius: {button_border_radius};
  }}
  QPushButton:hover {{
    background-color: {button_hover};
  }}
  
  #copyAddrButton, #copyEthButton {{
    background-color: {button_copy_address_bg};
    border: none;
    padding: 0px;
    margin: 0px;
  }}
"""

# Apply the common template with dark theme values
DARK_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**DARK_THEME)

# Apply the common template with light theme values, with additional light-specific styles
LIGHT_STYLESHEET = COMMON_STYLESHEET_TEMPLATE.format(**LIGHT_THEME) + """
  PlotWidget .axis {
    color: black;
  }

  PlotWidget .plotLabel {
    color: black;
  }
"""

# Notification messages
NOTIFICATION_TITLE_STRINGS_ENUM = {
    'success': 'Success',
    'error': 'Error',
    'warning': 'Warning',
    'info': 'Information'
}
NOTIFICATION_ADDRESS_COPIED = "Address {address} copied to clipboard"
NOTIFICATION_ADDRESS_COPY_FAILED = "No address available to copy. Try again after launching the Edge Node."

