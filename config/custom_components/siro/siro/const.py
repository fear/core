# MIT License
#
# Copyright (c) 2020 Felix Arnold
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = "Felix Arnold (@fear)"
__copyright__ = "Copyright (c) 2020 Felix Arnold"
__credits__ = ["Richard Moore (@ricmoo)", "everybody helping others on stackoverflow or somewhere else"]
__license__ = "MIT"
__version__ = "0.3"
__maintainer__ = "Felix Arnold (@fear)"
__email__ = "hello@felix-arnold.dev"
__status__ = "Beta"
__topic__ = "Home Automation"

""" Constant Declaration"""

# Config File
CONFIGFILE_DEVICE_NAMES = 'names.json'

# Logging
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10

LOG_FILE = 'siro.log'
LOGLEVEL = WARNING


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
    'State': {
        'OPEN': 1,
        'OPENING': 2,
        'CLOSED': 3,
        'CLOSING': 4,
        'STOP': 5,
    },
    'StateRev': {
        1: 'OPEN',
        2: 'OPENING',
        3: 'CLOSED',
        4: 'CLOSING',
        5: 'STOP',
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
