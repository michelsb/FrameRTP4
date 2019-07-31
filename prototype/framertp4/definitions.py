import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ROOT_DIR, 'db')
DRIVER_DIR = os.path.join(ROOT_DIR, 'drivers')
BUILD_DIR = os.path.join(ROOT_DIR, 'build')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
RTP4APP_DIR = os.path.join(ROOT_DIR, 'rtp4app')
DMM_DIR = os.path.join(ROOT_DIR, 'smart_detector')
MLMODEL_DIR = os.path.join(DMM_DIR, 'ml_model')
CONFIG_FILE = os.path.join(RTP4APP_DIR, 'config.ini')

DB_NAME = "database.sqlite3"
JSON_NAME = "rtp4app.json"
MLMODEL_NAME = "Random Forest"

WILDCARDS_GENERATION_TIMEOUT = 10
WILDCARDS_GENERATION_THRESHOLD = 5

SFCMON_COUNT_REGISTER = 'ctr_flows'
SFCMON_IDX_REGISTERS = ['hash1','hash2','hash3']
SFCMON_FLOW_REGISTERS = ['proto',
                         'srcAddr','dstAddr',
                         'srcPort','dstPort',
                         'spi', 'si']
SFCMON_METRIC_REGISTERS = ['ctr_pkts','ctr_bytes','first_seen']

SFCMON_READ_TIMEOUT = 5
SFCMON_RESET_TIMEOUT = 60


