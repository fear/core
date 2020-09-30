""" Constant Declaration"""

""" Constants  """
# Config File
CONFIGFILE_DEVICE_NAMES = 'persisted_names.json'
LOG_FILE = 'siro.log'

# Device Types
RADIO_MOTOR = '10000000'
WIFI_BRIDGE = '02000001'
WIFI_CURTAIN = '22000000'
WIFI_MOTOR_WIFI = '22000002'
WIFI_RECEIVER = '22000005'

# Network Config
CALLBACK_PORT = 32101
SEND_PORT = 32100
MULTICAST_GRP = '238.0.0.18'
UDP_TIMEOUT = 2

# Positions
STATE_DOWN = 100
STATE_UP = 0

# Operations
DOWN = 0
UP = 1
STOP = 2
POSITION = 3
ANGLE = 4
STATUS = 5

# Dictionaries
DEVICE_TYPES = {
    '02000001': 'Wi-Fi Bridge',
    '10000000': '433Mhz radio motor',
    '22000000': 'Wi-Fi Curtain',
    '22000002': 'Wi-Fi tubular motor',
    '22000005': 'Wi-Fi receiver',
}
CURRENT_STATE = {
    'Bridge': {
        1: 'Working',
        2: 'Pairing',
        3: 'Updating',
    },
    'Motor': {
        0: 'No limits',
        1: 'Top-limit detected',
        2: 'Bottom-limit detected',
        3: 'Limits detected',
        4: '3rd -limit detected',
    },
}
OPERATIONS = {
    0: 'Close/Down',
    1: 'Open/Up',
    2: 'Stop',
    3: 'Position',
    4: 'Angle',
    5: 'Status query',
}
VOLTAGE_MODE = {
    0: 'AC Motor',
    1: 'DC Motor',
}
WIRELESS_MODE = {
    0: 'Uni-direction',
    1: 'Bi-direction',
    2: 'Bi-direction (mechanical limits)',
    3: 'Others',
}
MOTOR_TYPE = {
    1: 'Roller Blinds',
    2: 'Venetian Blinds',
    3: 'Roman Blinds',
    4: 'Honeycomb Blinds',
    5: 'Shangri-La Blinds',
    6: 'Roller Shutter',
    7: 'Roller Gate',
    8: 'Awning',
    9: 'TDBU',
    10: 'Day&night Blinds',
    11: 'Dimming Blinds',
    12: 'Curtain',
    13: 'Curtain(Open Left)',
    14: 'Curtain(Open Right',
}
MSG_TYPES = {
    'READ': 'ReadDevice',
    'READ_ACK': 'ReadDeviceAck',
    'WRITE': 'WriteDevice',
    'WRITE_ACK': 'WriteDeviceAck',
    'LIST': 'GetDeviceList',
    'LIST_ACK': 'GetDeviceListAck',
    'ALIVE': 'Heartbeat',
    'REPORT': 'Report',
}
