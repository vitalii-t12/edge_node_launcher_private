from ver import __VER__
# Constants Section
ENV_FILE = '.env'
DOCKER_VOLUME = 'naeural_vol'
DOCKER_IMAGE = 'naeural/edge_node'
DOCKER_TAG = 'develop'
DOCKER_CONTAINER_NAME = 'edge_node_container'
WINDOWS_VOLUME_PATH = f'\\\\wsl.localhost\\docker-desktop-data\\data\\docker\\volumes\\{DOCKER_VOLUME}\\_data'
LINUX_VOLUME_PATH = '/var/lib/docker/volumes/naeural_vol/_data'
LOCAL_HISTORY_FILE = '_data/local_history.json'
E2_PEM_FILE = '_data/e2.pem'
LOCAL_ADDRESS_FILE = '_data/local_address.txt'
WINDOW_TITLE = f'Edge Node Manager v{__VER__}'
EDIT_ENV_BUTTON_TEXT = 'Edit .env File'
LAUNCH_CONTAINER_BUTTON_TEXT = 'Launch Container'
STOP_CONTAINER_BUTTON_TEXT = 'Stop Container'
DELETE_AND_RESTART_BUTTON_TEXT = 'Reset local node'
LOCAL_NODE_ADDRESS_LABEL_TEXT = 'Local Node Address'
REFRESH_LOCAL_ADDRESS_BUTTON_TEXT = 'Refresh Local Address'
COPY_ADDRESS_BUTTON_TEXT = 'Copy Address'

REFRESH_TIME = 10_000
MAX_HISTORY_QUEUE = 5 * 60 // 10 # 5 minutes @ 10 seconds each hb

DEFAULT_MQTT_HOST = 'r9092118.ala.eu-central-1.emqxsl.com'
DEFAULT_MQTT_USER = 'corenaeural'
DEFAULT_MQTT_PASSWORD = ''


ENV_TEMPLATE = '''
# LOCAL FILE TEMPLATE

# admin
EE_ID={}
EE_SUPERVISOR=true
EE_DEVICE=cuda:0


# MinIO / S3
EE_MINIO_ENDPOINT=endpoint
EE_MINIO_ACCESS_KEY=access_key
EE_MINIO_SECRET_KEY=secret_key
EE_MINIO_SECURE=false
EE_MINIO_UPLOAD_BUCKET=bucket


# MQTT
EE_MQTT_HOST={}
EE_MQTT_PORT=8883
EE_MQTT_USER={}
EE_MQTT={}
EE_MQTT_SUBTOPIC=address
EE_MQTT_CERT=

EE_NGROK_AUTH_TOKEN=ngrok-auth-token
EE_NGROK_EDGE_LABEL=ngrok-edge-label

# Misc
EE_GITVER=token_for_accessing_private_repositories
EE_OPENAI=token_for_accessing_openai_api
EE_HF_TOKEN=token_for_accessing_huggingface_api
'''

STYLESHEET = """
  QPushButton {
    background-color: #1E90FF; 
    color: white; 
    border: 2px solid #87CEEB; 
    padding: 10px 20px; 
    font-size: 16px; 
    margin: 4px 2px;
    border-radius: 15px;
  }
  QPushButton:hover {
    background-color: #104E8B;
  }
  QLabel {
    font-size: 14px;
    color: white;
  }
  QProgressBar {
    border: 2px solid #1E90FF;
    border-radius: 5px;
    text-align: center;
    height: 30px;
    color: white;
  }
  QProgressBar::chunk {
    background-color: #1E90FF;
  }
  QDialog, QWidget {
    background-color: #0D1F2D;
  }
  QTextEdit {
    background-color: #0D1F2D;
    color: white;
    font-size: 12px;
    border: 1px solid #1E90FF;
    border-radius: 5px;
  }
"""