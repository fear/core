from abc import ABC
import json
import logging

from .const import *


class Device(ABC):
    def __init__(self, mac: str, devicetype: str, logger: logging.Logger = None) -> None:
        self._log = self._init_log(logger)
        self._mac = mac
        self._devicetype = devicetype
        self._name = self._read_name_from_file()
        self._rssi = None
        self._msg_status = None
        self._online = True

    @staticmethod
    def _init_log(logger_: logging.Logger) -> logging.Logger:
        if logger_:
            return logger_
        else:
            logger = logging.getLogger(__name__)
            logger.setLevel(LOG_LEVEL)
            file_handler = logging.FileHandler(LOG_FILE)
            formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            return logger

    def _read_name_from_file(self) -> str:
        try:
            known_devices = json.load(open(CONFIGFILE_DEVICE_NAMES))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            self._log.debug(f'{self._mac}: There is no File {CONFIGFILE_DEVICE_NAMES}. Setting name to Unknown.')
            return '-unknown-'
        else:
            for known_device in known_devices:
                if known_device['mac'] == self._mac:
                    self._log.debug(f'{self._mac}: Name found. Setting name to {known_device["name"]}.')
                    return known_device['name']
            self._log.debug(f'{self._mac}: No Name found. Setting name to Unknown.')
            return '-unknown-'

    def set_name(self, device_name: str) -> None:
        self._name = device_name

        device_exists = False
        try:
            known_devices = json.load(open(CONFIGFILE_DEVICE_NAMES))
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
        name_file = open(CONFIGFILE_DEVICE_NAMES, 'w')
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

    def get_logger(self) -> logging.Logger:
        return self._log

    def is_online(self):
        return self._online

    @staticmethod
    def get_timestamp() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d%H%M%S%f")[0:17]


class Bridge(Device):
    # noinspection PyTypeChecker,PyMissingConstructor
    def __init__(self, connector, logger: logging.Logger = None, host_address_: str = '') -> None:
        super().__init__('', WIFI_BRIDGE, logger)
        self._connector = connector
        self._key = ''
        self._access_token = ''
        self._host_address = host_address_
        self._callback_address = ''
        self._protocol_version = ''
        self._firmware = ''
        self._token = ''
        self._msg_device_list = ''
        self._rssi = 0
        self._current_state = 0
        self._devices = []
        self._number_of_devices = ''
        self._key_accepted = ''

        # self._init_bridge(self.get_callback_address(callback_address), key)

    def init(self, key: str, callback_address: str = '') -> None:
        self._key = key
        self._callback_address = self.get_callback_address(callback_address)
        self._msg_device_list, self._host_address = self._get_device_list()
        self._mac = self._msg_device_list["mac"]
        self._read_name_from_file()
        self._token = self._msg_device_list["token"]
        self._protocol_version = self._msg_device_list['ProtocolVersion']
        self._firmware = self._msg_device_list['fwVersion']
        self._access_token = self._get_access_token()
        self._number_of_devices = len(self._msg_device_list['data'])-1
        self._devices = self.get_devices()
        self._msg_status = self.get_status()
        self._key_accepted = self.validate_key()

    def get_callback_address(self, callback_address: str = "") -> str:
        if callback_address == '':
            import socket as so
            s = so.socket(so.AF_INET, so.SOCK_DGRAM)
            s.connect(("208.67.222.222", 80))
            address_ = s.getsockname()[0]
        else:
            address_ = callback_address

        self._log.info(f"Set callback address to: {address_}")
        return address_

    def get_connector(self) -> any:
        return self._connector

    def _get_device_list(self) -> (dict, str):
        payload = json.dumps({
            'msgType': MSG_TYPES['LIST'],
            'msgID': self.get_timestamp()}
        )
        return self.send_payload(payload)

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

    def get_status(self) -> dict:
        payload = json.dumps(
            {
                "msgType": MSG_TYPES['WRITE'],
                "mac": self.get_mac(),
                "deviceType": self.get_devicetype(),
                "AccessToken": self.get_access_token(),
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

        return status

    def validate_key(self) -> bool:
        try:
            status = self.get_status()
            if status['actionResult'] == 'AccessToken error':
                raise ValueError('The key was rejected!')
        except KeyError:
            return True

    def print_variable(self) -> None:
        print(f"Mac: {self._mac}")
        print(f"Device Type: {self._devicetype}")
        print(f"Key: {self._key}")
        print(f"Access Token: {self._access_token}")
        print(f"current State: {self._current_state}")
        print(f"RSSI: {self._rssi}")
        print(f"Bridge Address: {self._host_address}")
        print(f"Callback Address: {self._callback_address}")
        print(f"Protocol Version: {self._protocol_version}")
        print(f"Firmware Version: {self._firmware}")
        print(f"Token: {self._token}")
        print(f"Message Heartbeat: {self._msg_status}")
        print(f"Message Device list: {self._msg_device_list}")

    def send_payload(self, payload: str) -> (dict, str):
        import socket

        if self._host_address == '':
            remote_ip = MULTICAST_GRP
        else:
            remote_ip = self._host_address

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
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
                    self._devices.append(new_device)
                    self.get_logger().info(f'{self._mac}: Created Device with mac {known_device["mac"]}.')

    def get_devices(self) -> list:
        if self._devices:
            return self._devices
        else:
            self.load_devices()
            return self._devices

    def get_device(self, mac: str) -> Device:
        for known_device in self._devices:
            if known_device.get_mac() == mac:
                return known_device

    def set_access_token(self, access_token: str) -> None:
        self._access_token = access_token

    def get_access_token(self) -> str:
        return self._access_token

    def get_host_address(self) -> str:
        return self._host_address

    def get_firmware(self) -> str:
        return self._firmware


class RadioMotor(Device):
    def __init__(self, mac: str, siro_bridge: any, logger: logging.Logger = None) -> None:
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
        self._last_msg_id = ''
        self._last_action = ''
        self._state_move = 0

    def init(self) -> None:
        self.update_status(self.get_status())

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
        return msg[0]

    def _callback_after_stop(self, sock=None, timeout: int = 60) -> dict:
        from socket import (
            AF_INET,
            IP_ADD_MEMBERSHIP,
            IPPROTO_IP,
            SOCK_DGRAM,
            inet_aton,
            socket,
        )

        if sock is None:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', CALLBACK_PORT))
            mreq = inet_aton(MULTICAST_GRP) + inet_aton(self._bridge.get_callback_address())
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

        if data['msgType'] == MSG_TYPES['REPORT']:
            s.close()
            self.update_status(data)
            return data
        else:
            self._callback_after_stop(sock=s, timeout=timeout)

    def update_status(self, status: dict = None) -> None:
        if not status:
            status = self.get_status()
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
        self._last_msg_id = status['msgID']

    def down(self) -> dict:
        msg = self._set_device(DOWN)
        if msg['data']['currentPosition'] == STATE_DOWN:
            self._state = CURRENT_STATE['State']['CLOSED']
            return msg
        else:
            self._state = CURRENT_STATE['State']['CLOSING']
            msg = self._callback_after_stop()
            self._state = CURRENT_STATE['State']['CLOSED']
            return msg

    def up(self) -> dict:
        msg = self._set_device(UP)
        if msg['data']['currentPosition'] == STATE_UP:
            self._state = CURRENT_STATE['State']['OPEN']
            return msg
        else:
            self._state = CURRENT_STATE['State']['OPENING']
            msg = self._callback_after_stop()
            self._state = CURRENT_STATE['State']['OPEN']
            return msg

    def stop(self) -> dict:
        timeout = 1

        msg_1 = self._set_device(STOP)
        msg_2 = self._callback_after_stop(timeout=timeout)

        # noinspection PyBroadException
        try:
            if msg_2['msgType'] == 'Report':
                msg = msg_2
            else:
                msg = msg_1
        except Exception:
            msg = msg_1

        self.update_status(msg)

        if self._current_position == UP:
            self._state = CURRENT_STATE['State']['OPEN']
        elif self._current_position == DOWN:
            self._state = CURRENT_STATE['State']['CLOSED']
        else:
            self._state = CURRENT_STATE['State']['STOP']
        return msg

    def position(self, position: int) -> dict:
        old_position = self._set_device(POSITION, position)['data']['currentPosition']
        if old_position < position:
            self._state = CURRENT_STATE['State']['CLOSING']
        else:
            self._state = CURRENT_STATE['State']['OPENING']

        msg = self._callback_after_stop()
        return msg

    def get_status(self) -> dict:
        payload = json.dumps(
            {
                'msgType': MSG_TYPES['READ'],
                "mac": self.get_mac(),
                "deviceType": self.get_devicetype(),
                'msgID': self.get_timestamp(),
            }
        )
        msg = self._bridge.send_payload(payload)
        return msg[0]

    def get_status_set(self) -> dict:
        return self._set_device(STATUS)

    def get_firmware(self) -> str:
        return self._bridge.get_firmware()

    def get_position(self, force_update: bool = False) -> int:
        if force_update:
            self.update_status()
        return self._current_position

    def get_bridge(self) -> Bridge:
        return self._bridge

    def get_moving_state(self) -> int:
        return self._state_move


class Connector:
    def __init__(self) -> None:
        pass

    @staticmethod
    def bridge_factory(key: str, log: logging.Logger = None, host_address: str = '') -> Bridge:
        new_bridge = Bridge(Connector, log, host_address)
        new_bridge.init(key)
        return new_bridge

    @staticmethod
    def device_factory(mac: str, devicetype: str, bridge: Bridge, log: logging.Logger = None) -> Device:
        if devicetype == RADIO_MOTOR:
            new_device = RadioMotor(mac, bridge, log)
            new_device.init()
            return new_device
        else:
            raise NotImplemented('By now there are just the 433Mhz Radio Motors implemented.')

    def start_cli(self, key: str, host_address: str = '') -> None:
        bridge = self.bridge_factory(
            key=key,
            host_address=host_address,
        )
        devices = bridge.get_devices()

        keep_running = True
        while keep_running:
            print("List of available devices: ")
            for device in devices:
                index = devices.index(device) + 1
                name = f"{device.get_name()} " \
                       f"(mac: {device.get_mac()}, " \
                       f"type: {DEVICE_TYPES[device.get_devicetype()]})"
                print(f"  {index}: {name}")
            device_selection = int(input(f"Which device do you want to control (1-{len(devices)}): ")) - 1
            print("List of possible operations: \n"
                  "  1: up\n"
                  "  2: down\n"
                  "  3: set position\n"
                  "  4: get Status\n"
                  "  9: set name\n"
                  "  0: cancel")
            operation = int(input("What do you want to do? (0-5): "))

            if operation == 1:
                print(devices[device_selection].up())
            elif operation == 2:
                print(devices[device_selection].down())
            elif operation == 3:
                value = int(input("Which position should the roller blind move to? (0-100): "))
                print(devices[device_selection].position(value))
            elif operation == 4:
                print(devices[device_selection].get_status())
            elif operation == 9:
                name = input("Please indicate the name: ")
                devices[device_selection].set_name(name)
                print(f"The name was changed to {devices[device_selection].get_name()}.")
            else:
                keep_running = False

            if keep_running:
                exit_run = input("Continue? (y,N): ")
                if exit_run != 'y' or exit_run != 'y':
                    keep_running = False
                else:
                    print("-------------------------------------------------------------------")
