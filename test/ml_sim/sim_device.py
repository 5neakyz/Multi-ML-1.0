import io
import logging
import re
import threading
import time
from pathlib import Path

from xmodem import XMODEM

from sim_listener import Listener
from sim_serial_port_manager import SerialPortManger


DEFAULT_FIRMWARE_VERSION = "3.90.2"
DEFAULT_FIRMWARE_SIZE = 545436
FIRMWARE_VERSION_PATTERN = re.compile(rb"(?<![\d.])\d+(?:\.\d+){2,}(?![\d.])")

DEFAULT_CONFIG_LINES = [
    b"HostIP              172.17.168.157\r\n",
    b"HostPort            5432\r\n",
    b"APN                 microlise.lte1.gdsp\r\n",
    b"\r\n",
    b"PersonalityVer      SG14_NO_CAN_MICROLISE_STOCK_Rev_1\r\n",
    b"\r\n",
    b"CAN1Mode            Off\r\n",
    b"\r\n",
    b"DistanceSource      3\r\n",
    b"SpeedSource         1\r\n",
    b"\r\n",
    b"IgnitionOn          0 0\r\n",
    b"IgnitionOff         0 0\r\n",
    b"MovingAfterStopped  1.0 60 1.0\r\n",
    b"Stopped             1.0 60 1.0\r\n",
    b"WakeupMask          4\r\n",
    b"BLEMode             1 \r\n",
    b"\r\n",
    b"################### Metrics ###################\r\n",
    b"\r\n",
    b"ExcessiveIdle       0.1 180 0.15\r\n",
    b"ExcessiveSpeedD     96.56 10 1.0\r\n",
    b"HarshBrake         -14.0 0 13.9\r\n",
    b"HarshCorneringG     8.0 0.4 0.3\r\n",
]


class Device(SerialPortManger):
    def __init__(self, parent, state_dir=None, on_serial_io=None):
        super().__init__(parent)
        self.log = logging.getLogger("Device")
        self.log.info("%s: Creating Device Object", self.serial_port_name)
        self.serial_io_callback = on_serial_io
        self.in_menu = False
        self.loop = False
        self.download_active = False
        self.state_dir = Path(state_dir) if state_dir else Path(__file__).with_name("sim_state")
        self.config_path = self.state_dir / "config.txt"
        self.firmware_path = self.state_dir / "firmware.bin"
        self.config_data = self.config_path.read_bytes() if self.config_path.exists() else None
        self.firmware_version = DEFAULT_FIRMWARE_VERSION
        self.firmware_size = DEFAULT_FIRMWARE_SIZE
        if self.firmware_path.exists():
            firmware = self.firmware_path.read_bytes()
            self.firmware_size = len(firmware)
            self._update_firmware_version(firmware)

        self.listener = None
        if self.serial_connection:
            self.listener = Listener(self)
            self.listener.start_listening()

    def receiver(self, line, stop):
        self.log.info("%s: Receiving %r", self.serial_port_name, line)
        if b"\x1b" in line:
            self.in_menu = True
            self.loop = False
            self.write(self.main_menu_lines())
            return

        if not self.in_menu:
            return

        option = line.strip()
        if option == b"3":
            self.write(self.config_screen_lines())
        elif option == b"4":
            self.loop = True
            threading.Thread(target=self.constant_write, args=(stop,), daemon=True).start()
        elif option == b"6":
            self.write(self.download_screen_lines())
            self.receive_download()

    def record_serial_io(self, direction, data):
        if self.serial_io_callback is not None:
            self.serial_io_callback(direction, data)

    def getc(self, size, timeout=1):
        deadline = time.monotonic() + timeout
        received = bytearray()
        while len(received) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            chunk = self.serial_port.read(size - len(received))
            if chunk:
                received.extend(chunk)
                self.record_serial_io("RX", chunk)
        return bytes(received) if received else None

    def putc(self, data):
        written = self.serial_port.write(data)
        if written:
            self.record_serial_io("TX", data[:written])
        return written or None

    def receive_download(self):
        self.log.info("%s: Starting XMODEM-1K receive", self.serial_port_name)
        stream = io.BytesIO()
        self.download_active = True
        try:
            received = XMODEM(self.getc, self.putc, "xmodem1k").recv(
                stream, timeout=2, retry=16, delay=0.1
            )
        except OSError:
            self.log.exception("%s: Serial error during XMODEM receive", self.serial_port_name)
            return False
        finally:
            self.download_active = False

        if received is None or received == 0:
            self.log.warning("%s: XMODEM receive failed", self.serial_port_name)
            self.write([b"Download failed\r\n"])
            return False

        try:
            self._store_download(stream.getvalue())
        except OSError:
            self.log.exception("%s: Could not store received file", self.serial_port_name)
            self.write([b"Download failed\r\n"])
            return False

        self.write([b"Hello from simulated unit\r\n"])
        return True

    def _store_download(self, payload):
        content = payload.rstrip(b"\x1a")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = None

        if text is not None and text.lstrip().startswith("CONFIG"):
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.config_path.write_bytes(content)
            self.config_data = content
            self.log.info("%s: Updated simulated config", self.serial_port_name)
            return

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.firmware_path.write_bytes(payload)
        self.firmware_size = len(payload)
        if not self._update_firmware_version(payload):
            self.log.warning("%s: No firmware version found in received image", self.serial_port_name)
        self.log.info("%s: Updated simulated firmware", self.serial_port_name)

    def _update_firmware_version(self, firmware):
        match = FIRMWARE_VERSION_PATTERN.search(firmware)
        if not match:
            return False
        self.firmware_version = match.group().decode("ascii")
        return True

    def write(self, lines):
        self.log.info("%s: Writing", self.serial_port_name)
        for line in lines:
            try:
                written = self.serial_port.write(line)
                if written:
                    self.record_serial_io("TX", line[:written])
            except OSError:
                self.log.exception("%s: Serial write failed", self.serial_port_name)
                return False
        return True

    def shutdown(self):
        self.loop = False
        if self.listener is not None:
            self.listener.interrupt()
            self.listener.join(timeout=1)
        self.disconnect()

    def constant_write(self, stop):
        self.log.info("%s: Entering status write loop", self.serial_port_name)
        while self.loop:
            self.write(self.status_screen_lines(time.strftime("%D %T", time.localtime())))
            if stop():
                break
            time.sleep(1)

    def main_menu_lines(self):
        return [
            b"\x1b[2J\r\t\t\tMain Menu\r\r\n",
            b"\r\n",
            b"\n",
            b"\t\t  1 - Debugs\r\n",
            b"\t\t  2 - Logs\r\n",
            b"\t\t  3 - View Config\r\n",
            b"\t\t  4 - Status Screen\r\n",
            b"\t\t  5 - Configure\r\n",
            b"\t\t  6 - Download\r\n",
            b"\t\t  7 - Telematic Event Data\r\n",
            b"\t\t  8 - Telematic Summary Data\r\n",
            b"\t\t  9 - Advanced Menu\r\n",
            b"\t\t  b - Performance Counters Screen\r\n",
            b"\t\t  c - Commissioning Menu\r\n",
            b"\t\t  f - Production Test Screen\r\n",
            b"\t\t  g - System Info Screen\r\n",
            b"\r\n",
            b"\r\n",
            b" Enter option >",
        ]

    def status_screen_lines(self, current_time):
        return [
            b"\x1b[2J\r\t\t\tStatus Screen\r\n",
            b"\r\n",
            f"MTU4 Time\t:{current_time} \tUptime: 00:00:00\r\n".encode(),
            b"IMEI\t\t: 1234567890\tTelit 864: 10.01.020\r\n",
            f"Ver\t\t:{self.firmware_version}\tcrc 0x96c0 size:{self.firmware_size}\r\n".encode(),
            b"Sig Q\t\t:255 = 0 Percent \r\n",
            b"GPRS\t\t:Trying\r\n",
            b"IP\t\t:\r\n",
            b"IMSI\t\t:\r\n",
            b"ICCID\t\t:\r\n",
            b"SRVR\t\t:172.17.144.97\t\tNot Connected \t5432\r\n",
            b"Power Retain\t:7200\tSleep: 43200=0\tRe-try: 6 \r\n",
            b"VIN\t\t:                 \tDriverId :Unknown\r\n",
            b"VRN\t\t:               \r\n",
            b"\r\n",
            b"GPSVer\t\t:HW:00040007\tSW:7.03 (45969)\r\n",
            b"Latitude\t: 53.03206253\tPower\t\t:On (24.81v)\r\n",
            b"Longitude\t: -1.46555280\tIgnition\t:On\r\n",
            b"GPSFix\t\t:TRUE FC 25  \tCh1 'Camera'\t:Low\t(DPD)\r\n",
            b"Num Sats\t:8\t\tCh2 'Unknown'\t:High\t(DPU)\r\n",
            b"Speed\t\t:  0.275948\tCh3 'Unknown'\t:High\t(DPU)\r\n",
            b"Course\t\t:  0.000000\tCh4 'PTO'\t:High\t(DPU)\r\n",
            b"Distance\t:0000010301\tShut Down\t:7200s\r\n",
            b"GPS Antenna\t:0\t\tBatt Capacity\t:unknown (3.78v)\r\n",
            b"GPS err (fHacc)\t:6.30\t\tCharge State\t:Fault\r\n",
            b"GPS AvCNO\t:22.00\t\tBT name\t\t:MTU4-728670\r\n",
            b"GPS err (HDOP)\t:0.96\r\n",
            b"Commissioning field: \r\n",
            b"\r\n",
        ]

    def config_screen_lines(self):
        lines = DEFAULT_CONFIG_LINES
        if self.config_data is not None:
            lines = self.config_data.splitlines(keepends=True)
            if lines and lines[0].lstrip(b"\xef\xbb\xbf").strip() == b"CONFIG":
                lines = lines[1:]
            lines = [
                line if line.endswith((b"\r", b"\n")) else line + b"\r\n"
                for line in lines
            ]
        return [b"\x1b[2J\r\t\t\tCONFIG\r\n", b"\r\n", *lines]

    def download_screen_lines(self):
        return [
            b"\x1b[2J\r\t\t\tDownload\r\r\n",
            b"\r\n",
            b"\n",
            b"Firmware or Config via 1K Xmodem:\r\n",
        ]
