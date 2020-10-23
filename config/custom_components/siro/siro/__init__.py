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
__version__ = "0.4"
__maintainer__ = "Felix Arnold (@fear)"
__email__ = "hello@felix-arnold.dev"
__status__ = "Beta"
__topic__ = "Home Automation"

from siro.siro import (
    Bridge,
    Driver,
    RadioMotor,
)
from siro.const import (
    CALLBACK_PORT,
    CONFIGFILE_DEVICE_NAMES,
    CURRENT_STATE,
    DOWN,
    LOG_FILE,
    LOGLEVEL,
    MSG_TYPES,
    MULTICAST_GRP,
    POSITION,
    RADIO_MOTOR,
    SEND_PORT,
    STATE_DOWN,
    STATE_UP,
    STATUS,
    STOP,
    UDP_TIMEOUT,
    UP,
    WIFI_BRIDGE,
)
