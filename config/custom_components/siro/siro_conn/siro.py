import json

from abc import (
    ABC
)
from const import (
    CALLBACK_PORT,
    CONFIGFILE_DEVICE_NAMES,
    CURRENT_STATE,
    DEVICE_TYPES,
    DOWN,
    LOG_FILE,
    LOG_LEVEL,
    MSG_TYPES,
    MULTICAST_GRP,
    POSITION,
    RADIO_MOTOR,
    SEND_PORT,
    STATE_DOWN,
    STATE_UP,
    STOP,
    UDP_TIMEOUT,
    UP,
    WIFI_BRIDGE,
)
from socket import (
    AF_INET,
    IPPROTO_IP,
    IPPROTO_UDP,
    IP_ADD_MEMBERSHIP,
    IP_MULTICAST_TTL,
    SOCK_DGRAM,
    inet_aton,
    socket,
)
from logging import (
    Logger,
    getLogger,
    FileHandler,
    Formatter,
)


class Device(ABC):
    def __init__(self, mac: str, devicetype: str, logger: Logger = None) -> None:
        self._log = self._init_log(logger)
        self._mac = mac
        self._devicetype = devicetype
        self._name = self._get_persisted_name_from_file()
        self._rssi = None
        self._msg_status = None
        self._online = True
        self._last_update = None

    @staticmethod
    def _init_log(logger_: Logger) -> Logger:
        if logger_:
            return logger_
        else:
            logger = getLogger(__name__)
            logger.setLevel(LOG_LEVEL)
            file_handler = FileHandler(LOG_FILE)
            formatter = Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            return logger

    def _set_last_update(self) -> None:
        from datetime import datetime
        self._last_update = datetime.now()

    def _set_last_msg_status(self, msg: dict) -> None:
        self._msg_status = msg
        self._set_last_update()

    def _get_persisted_name_from_file(self, config_file: str = CONFIGFILE_DEVICE_NAMES) -> str:
        try:
            known_devices = json.load(open(config_file))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            self._log.debug(f'{self._mac}: There is no File {config_file}. Setting name to Unknown.')
            return '-unknown-'
        else:
            for known_device in known_devices:
                if known_device['mac'] == self._mac:
                    self._log.debug(f'{self._mac}: Name found. Setting name to {known_device["name"]}.')
                    return known_device['name']
            self._log.debug(f'{self._mac}: No Name found. Setting name to Unknown.')
            return '-unknown-'

    def set_name(self, device_name: str, config_file: str = CONFIGFILE_DEVICE_NAMES) -> None:
        self._name = device_name

        device_exists = False
        try:
            known_devices = json.load(open(config_file))
        except json.decoder.JSONDecodeError:
            known_devices = []

        for known_device in known_devices:
            if known_device['mac'] == self._mac:
                known_device['name'] = device_name
                device_exists = True
        if not device_exists:
            known_devices.append(
                {
                    "mac": self._mac,
                    "name": self._name,
                }
            )
        name_file = open(config_file, 'w')
        name_file.write(json.dumps(known_devices, indent=4))
        name_file.close()
        self._log.debug(f'{self._mac}: Name was set to "{device_name}".')

    def get_name(self) -> str:
        return self._name

    def get_mac(self) -> str:
        return self._mac

    def get_devicetype(self):
        return self._devicetype

    def get_rssi(self) -> int:
        return self._rssi

    def get_logger(self) -> Logger:
        return self._log

    def is_online(self):
        return self._online

    @staticmethod
    def get_timestamp() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d%H%M%S%f")[0:17]


class Bridge(Device):
    # noinspection PyTypeChecker,PyMissingConstructor
    def __init__(self, connector, logger: Logger = None, bridge_address: str = '') -> None:
        super().__init__('', WIFI_BRIDGE, logger)
        self._connector: Connector = connector
        self._key: str = ''
        self._access_token: str = ''
        self._bridge_address: str = bridge_address
        self._callback_address: str = ''
        self._protocol_version: str = ''
        self._firmware: str = ''
        self._token: str = ''
        self._rssi: int = 0
        self._current_state: int = 0
        self._devices: list = []
        self._number_of_devices: int = None
        self._key_accepted: bool = None
        self._sock: socket = None

        self._msg_device_list: dict = {}
        self._msg_callback: dict = {}

    def init(self, key: str, callback_address: str = '') -> None:
        self._key = key
        self._callback_address = self._ident_callback_address(callback_address)
        self._init_socket()
        self._msg_device_list, self._bridge_address = self._load_device_list_from_bridge()
        self._mac = self._msg_device_list["mac"]
        self._token = self._msg_device_list["token"]
        self._protocol_version = self._msg_device_list['ProtocolVersion']
        self._firmware = self._msg_device_list['fwVersion']
        self._access_token = self._get_access_token()
        self._number_of_devices = len(self._msg_device_list['data'])-1
        self._devices = self.get_devices()

        self._set_last_msg_status(self.get_status(force_update=True))
        self._key_accepted = self.validate_key()

    def _ident_callback_address(self, callback_address: str = "") -> str:
        if callback_address == '':
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(("208.67.222.222", 80))
            address_ = s.getsockname()[0]
            s.close()
        else:
            address_ = callback_address

        self._log.info(f"Set callback address to: {address_}")
        return address_

    def get_callback_address(self) -> str:
        return self._callback_address

    def get_connector(self) -> any:
        return self._connector

    def _load_device_list_from_bridge(self) -> (dict, str):
        payload = json.dumps({
            'msgType': MSG_TYPES['LIST'],
            'msgID': self.get_timestamp()}
        )
        return self.send_payload(payload)

    def _set_last_msg_callback(self, msg: dict) -> None:
        self._msg_callback = msg

    def _get_access_token(self) -> str:
        from Cryptodome.Cipher import AES

        if self._access_token == '':
            key = self._key
            token = self._token

            if len(key) != 16:
                raise Exception('The Key seems broken.')

            cypher_key = bytearray()
            cypher_key.extend(map(ord, key))

            cipher = AES.new(cypher_key, AES.MODE_ECB)
            cipher_bytes = cipher.encrypt(token.encode("utf8"))
            access_token = ''.join('%02x' % byte for byte in bytearray(cipher_bytes))
            self._access_token = access_token.upper()
        return self._access_token

    def _update_status(self) -> None:
        payload = json.dumps(
            {
                "msgType": MSG_TYPES['WRITE'],
                "mac": self._mac,
                "deviceType": self._devicetype,
                "AccessToken": self._access_token,
                "msgID": self.get_timestamp(),
                "data": {'operation': 5}
            }
        )

        status = self.send_payload(payload)
        status = status[0]

        self._current_state = status['data']['currentState']
        self._number_of_devices = status['data']['numberOfDevices']
        self._rssi = status['data']['RSSI']

        if self._number_of_devices == 0:
            raise UserWarning('No devices were found.')

        self._set_last_update()
        self._msg_status = status

    def get_status(self, force_update: bool = False) -> dict:
        if force_update:
            self._update_status()

        return self._msg_status

    def validate_key(self) -> bool:
        try:
            status = self.get_status()
            if status['actionResult'] == 'AccessToken error':
                raise ValueError('The key was rejected!')
        except KeyError:
            return True

    def print_device_info(self) -> None:
        print(f"Mac: {self._mac}")
        print(f"Device Type: {self._devicetype}")
        print(f"Key: {self._key}")
        print(f"Access Token: {self._access_token}")
        print(f"current State: {self._current_state}")
        print(f"RSSI: {self._rssi}")
        print(f"Bridge Address: {self._bridge_address}")
        print(f"Callback Address: {self._callback_address}")
        print(f"Protocol Version: {self._protocol_version}")
        print(f"Firmware Version: {self._firmware}")
        print(f"Token: {self._token}")
        print(f"Message Heartbeat: {self._msg_status}")
        print(f"Message Device list: {self._msg_device_list}")

    def _init_socket(self) -> None:
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', CALLBACK_PORT))
            mreq = inet_aton(MULTICAST_GRP) + inet_aton(self._callback_address)
            s.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
            self._sock = s
        except Exception:
            raise

    def _set_socket_timeout(self, timeout: int) -> None:
        self._sock.settimeout(timeout)

    def _get_socket(self) -> socket:
        return self._sock

    def send_payload(self, payload: str) -> (dict, str):
        if self._bridge_address == '':
            remote_ip = MULTICAST_GRP
        else:
            remote_ip = self._bridge_address
        try:
            self._set_socket_timeout(UDP_TIMEOUT)
            self._get_socket().sendto(payload.encode(), (remote_ip, SEND_PORT))
            self.get_logger().debug(f'{self._mac}: Send to {remote_ip}:{SEND_PORT}: {payload}.')

            data, address = self._get_socket().recvfrom(1024)
            message = json.loads(data.decode('utf-8'))

            self.get_logger().debug(f'{self._mac}: Receive from {address[0]}:{address[1]}: {message}.')
            return message, address[0]
        except Exception:
            raise

    def get_callback_from_bridge(self, timeout: int = 60) -> dict:
        # noinspection PyBroadException
        try:
            self._set_socket_timeout(timeout)
            msg = self._get_socket().recv(1024)
        except Exception as e:
            self._log.warning(e)
            return {'msgType': 'timeout'}
        data = json.loads(msg.decode('utf-8'))
        self._set_last_msg_callback(data)

        if data['msgType'] == MSG_TYPES['REPORT']:
            self._set_last_msg_callback(data)
            return data
        else:
            self.get_callback_from_bridge(timeout=timeout)

    def send_payload_old(self, payload: str) -> (dict, str):
        if self._bridge_address == '':
            remote_ip = MULTICAST_GRP
        else:
            remote_ip = self._bridge_address
        try:
            s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            s.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 32)
            s.bind((self._callback_address, CALLBACK_PORT))
            s.settimeout(UDP_TIMEOUT)

            s.sendto(payload.encode(), (remote_ip, SEND_PORT))
            self.get_logger().debug(f'{self._mac}: Send to {remote_ip}:{SEND_PORT}: {payload}.')

            data, address = s.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            port = address[1]
            address = address[0]
            s.close()
            self.get_logger().debug(f'{self._mac}: Receive from {address}:{port}: {message}.')
            return message, address
        except Exception:
            raise

    def get_callback_from_bridge_old(self, sock=None, timeout: int = 60) -> dict:
        if sock is None:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', CALLBACK_PORT))
            s.settimeout(timeout)
            mreq = inet_aton(MULTICAST_GRP) + inet_aton(self._callback_address)
            s.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        else:
            s = sock
        # noinspection PyBroadException
        try:
            msg = s.recv(1024)
        except Exception as e:
            self._log.warning(e)
            return {'msgType': 'timeout'}
        data = json.loads(msg.decode('utf-8'))
        self._set_last_msg_callback(data)

        if data['msgType'] == MSG_TYPES['REPORT']:
            # s.close()
            self._set_last_msg_callback(data)
            return data
        else:
            self.get_callback_from_bridge(timeout=timeout)

    # noinspection PyTypeChecker
    def load_devices(self) -> None:
        if self._number_of_devices > 0:
            for known_device in self._msg_device_list["data"]:
                if known_device['deviceType'] == RADIO_MOTOR:
                    new_device = Connector.device_factory(
                        known_device['mac'],
                        known_device['deviceType'],
                        self,
                        self._log
                    )
                    if not self.check_if_device_exist(known_device['mac']):
                        self._devices.append(new_device)
                        self.get_logger().info(f'{self._mac}: Created Device with mac {known_device["mac"]}.')
                    else:
                        self.get_logger().info(f'{self._mac}: Device with mac {known_device["mac"]} already exists.')
                elif known_device['deviceType'] == WIFI_BRIDGE:
                    pass
                else:
                    self.get_logger().warning(
                        f'{known_device["mac"]}: Found not supported device of Type {known_device["deviceType"]}. '
                    )

    def check_if_device_exist(self, mac: str) -> bool:
        try:
            self.get_device_by_mac(mac)
        except UserWarning as warn:
            self.get_logger().debug(warn)
            return False
        else:
            return True

    def get_devices(self, force_update: bool = str) -> list:
        if self._devices or not force_update:
            return self._devices
        else:
            self.load_devices()
            return self._devices

    def get_device_by_mac(self, mac: str) -> Device:
        for known_device in self._devices:
            if known_device.get_mac() == mac:
                return known_device
        else:
            raise UserWarning(f'Device with mac "{mac}" is not known.')

    def get_access_token(self) -> str:
        return self._access_token

    def get_bridge_address(self) -> str:
        return self._bridge_address

    def get_firmware(self) -> str:
        return self._firmware


class RadioMotor(Device):
    def __init__(self, mac: str, siro_bridge: Bridge, logger: Logger = None) -> None:
        super().__init__(mac, RADIO_MOTOR, logger)
        self._bridge = siro_bridge
        self._type = ''
        self._operation = ''
        self._current_position = 0
        self._current_angle = ''
        self._current_state = ''
        self._voltage_mode = ''
        self._battery_level = ''
        self._wireless_mode = ''
        self._last_action = ''
        self._state_move = 0

    def init(self) -> None:
        self.update_status(force_update=True)

    def _set_device(self, action: int, position: int = 0) -> dict:
        if action == POSITION:
            data = {'targetPosition': position}
        else:
            data = {'operation': action}

        payload = json.dumps(
            {
                "msgType": MSG_TYPES['WRITE'],
                "mac": self.get_mac(),
                "deviceType": self.get_devicetype(),
                "AccessToken": self._bridge.get_access_token(),
                "msgID": self.get_timestamp(),
                "data": data
            }
        )
        msg = self._bridge.send_payload(payload)
        self._set_last_msg_status(msg[0])
        self.update_status()
        return msg[0]

    def _callback_after_stop(self, timeout: int = 60) -> dict:
        msg = self._bridge.get_callback_from_bridge(timeout=timeout)
        self._set_last_msg_status(msg)
        self.update_status()
        return msg

    def update_status(self, force_update: bool = False) -> None:
        if force_update:
            status = self.get_status(force_update=True)
        else:
            status = self._msg_status
        try:
            self._type = status['data']['type']
            self._operation = status['data']['operation']
            self._current_position = status['data']['currentPosition']
            self._current_angle = status['data']['currentAngle']
            self._current_state = status['data']['currentState']
            self._voltage_mode = status['data']['voltageMode']
            self._battery_level = status['data']['batteryLevel']
            self._wireless_mode = status['data']['wirelessMode']
            self._rssi = status['data']['RSSI']
            self._last_action = status['msgType']
        except Exception:
            raise

    def move_down(self) -> dict:
        msg = self._set_device(DOWN)
        if msg['data']['currentPosition'] == STATE_DOWN:
            self._state_move = CURRENT_STATE['State']['CLOSED']
        else:
            self._state_move = CURRENT_STATE['State']['CLOSING']
            msg = self._callback_after_stop()
            self._state_move = CURRENT_STATE['State']['CLOSED']
        return msg

    def move_up(self) -> dict:
        msg = self._set_device(UP)
        if msg['data']['currentPosition'] == STATE_UP:
            self._state_move = CURRENT_STATE['State']['OPEN']
        else:
            self._state_move = CURRENT_STATE['State']['OPENING']
            msg = self._callback_after_stop()
            self._state_move = CURRENT_STATE['State']['OPEN']
        return msg

    def move_stop(self) -> dict:
        msg_1 = self._set_device(STOP)
        msg_2 = self._callback_after_stop(timeout=1)

        # noinspection PyBroadException
        try:
            if msg_2['msgType'] == 'Report':
                msg = msg_2
            else:
                msg = msg_1
        except Exception:
            msg = msg_1

        if self._current_position == UP:
            self._state_move = CURRENT_STATE['State']['OPEN']
        elif self._current_position == DOWN:
            self._state_move = CURRENT_STATE['State']['CLOSED']
        else:
            self._state_move = CURRENT_STATE['State']['STOP']
        return msg

    def move_to_position(self, position: int) -> dict:
        old_position = self._set_device(POSITION, position)['data']['currentPosition']
        if old_position < position:
            self._state_move = CURRENT_STATE['State']['CLOSING']
        else:
            self._state_move = CURRENT_STATE['State']['OPENING']

        msg = self._callback_after_stop()

        return msg

    def get_status(self, force_update: bool = False) -> dict:
        if force_update:
            payload = json.dumps(
                {
                    'msgType': MSG_TYPES['READ'],
                    "mac": self.get_mac(),
                    "deviceType": self.get_devicetype(),
                    'msgID': self.get_timestamp(),
                }
            )
            msg = self._bridge.send_payload(payload)
            self._set_last_msg_status(msg[0])
            self.update_status()

        return self._msg_status

    def get_firmware(self) -> str:
        return self._bridge.get_firmware()

    def get_position(self, force_update: bool = False) -> int:
        if force_update:
            self.update_status(force_update=True)
        return self._current_position

    def get_bridge(self) -> Bridge:
        return self._bridge

    def get_moving_state(self) -> int:
        return self._state_move


class Connector:
    def __init__(self) -> None:
        pass

    @staticmethod
    def bridge_factory(key: str, log: Logger = None, bridge_address: str = '') -> Bridge:
        new_bridge = Bridge(Connector, log, bridge_address)
        new_bridge.init(key)
        return new_bridge

    @staticmethod
    def device_factory(mac: str, devicetype: str, bridge: Bridge, log: Logger = None) -> Device:
        if devicetype == RADIO_MOTOR:
            new_device = RadioMotor(mac, bridge, log)
            new_device.init()
            return new_device
        else:
            raise NotImplemented('By now there are just the 433Mhz Radio Motors implemented.')

    @staticmethod
    def get_device_name(device: Device):
        return device.get_name()

    def start_cli(self, key: str, bridge_address: str = '') -> None:
        bridge = self.bridge_factory(
            key=key,
            bridge_address=bridge_address,
        )
        devices: list = bridge.get_devices()

        keep_running = True
        while keep_running:
            print("List of available devices: ")
            devices.sort(key=self.get_device_name)
            for device in devices:
                index = devices.index(device) + 1
                name = f"{device.get_name()} " \
                       f"(mac: {device.get_mac()}, " \
                       f"type: {DEVICE_TYPES[device.get_devicetype()]})"
                print(f"  {index}: {name}")
            print(f"--------------------------------------------------------------------\n"
                  f"  0: for exit")
            device_selection = int(input(f"Which device do you want to control (1-{len(devices)}): ")) - 1
            if device_selection == -1:
                keep_running = False
                exit()

            selected_device: RadioMotor = devices[device_selection]
            print("List of possible operations: \n"
                  "  1: up\n"
                  "  2: down\n"
                  "  3: set position\n"
                  "  4: get position\n"
                  "  5: get status\n"
                  "  9: set name\n"
                  "  0: cancel")
            operation = int(input("What do you want to do? (0-5,9): "))

            if operation == 1:
                print(selected_device.move_up())
            elif operation == 2:
                print(selected_device.move_down())
            elif operation == 3:
                value = int(input("Which position should the roller blind move to? (0-100): "))
                print(selected_device.move_to_position(value))
            elif operation == 4:
                print(selected_device.get_status())
            elif operation == 9:
                name = input("Please indicate the name: ")
                selected_device.set_name(name)
                print(f"The name was changed to {selected_device.get_name()}.")
            else:
                keep_running = False

            if keep_running:
                exit_run = input("Continue? (y,N): ")
                if exit_run != 'y' or exit_run != 'y':
                    keep_running = False
                else:
                    print("--------------------------------------------------------------------------")
