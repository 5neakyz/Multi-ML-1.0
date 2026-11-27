import io
import logging
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from xmodem import XMODEM

from sim_device import DEFAULT_FIRMWARE_SIZE, DEFAULT_FIRMWARE_VERSION, Device


class MemorySerial:
    def __init__(self):
        self.incoming = bytearray()
        self.condition = threading.Condition()
        self.peer = None
        self.writes = []

    def write(self, data):
        data = bytes(data)
        self.writes.append(data)
        with self.peer.condition:
            self.peer.incoming.extend(data)
            self.peer.condition.notify_all()
        return len(data)

    def read(self, size, timeout=0.02):
        deadline = time.monotonic() + timeout
        with self.condition:
            while not self.incoming:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return b""
                self.condition.wait(remaining)
            data = bytes(self.incoming[:size])
            del self.incoming[:size]
            return data


def memory_serial_pair():
    first = MemorySerial()
    second = MemorySerial()
    first.peer = second
    second.peer = first
    return first, second


def make_device(serial_port, state_dir, on_serial_io=None):
    device = Device.__new__(Device)
    device.log = logging.getLogger("test.Device")
    device.serial_port = serial_port
    device.serial_port_name = "test-port"
    device.serial_io_callback = on_serial_io
    device.state_dir = Path(state_dir)
    device.config_path = device.state_dir / "config.txt"
    device.firmware_path = device.state_dir / "firmware.bin"
    device.config_data = None
    device.firmware_version = DEFAULT_FIRMWARE_VERSION
    device.firmware_size = DEFAULT_FIRMWARE_SIZE
    device.download_active = False
    return device


class SimulatedDownloadTests(unittest.TestCase):
    def transfer(self, payload, state_dir):
        receiver_port, sender_port = memory_serial_pair()
        serial_events = []
        device = make_device(
            receiver_port,
            state_dir,
            lambda direction, data: serial_events.append((direction, data)),
        )
        sender_result = []

        def send_file():
            def sender_getc(size, timeout=1):
                return sender_port.read(size, timeout)

            sender = XMODEM(
                sender_getc,
                sender_port.write,
                "xmodem1k",
            )
            sender_result.append(
                sender.send(
                    io.BytesIO(payload),
                    retry=3,
                    timeout=2,
                    quiet=True,
                )
            )

        sender_thread = threading.Thread(target=send_file)
        sender_thread.start()
        received = device.receive_download()
        sender_thread.join(timeout=5)

        self.assertFalse(sender_thread.is_alive(), "XMODEM sender did not finish")
        self.assertEqual(sender_result, [True])
        self.assertTrue(received)
        self.assertTrue(
            any(frame.startswith(b"\x02") and len(frame) >= 1029 for frame in sender_port.writes),
            "sender did not transmit an XMODEM-1K block",
        )
        self.assertIn("RX", [direction for direction, _ in serial_events])
        self.assertIn("TX", [direction for direction, _ in serial_events])
        return device

    def test_xmodem1k_config_transfer_updates_file_and_screen(self):
        config = (
            b"CONFIG\r\nHostIP              192.0.2.10\r\n"
            b"PersonalityVer      Test_Personality\r\n"
            b"Description         "
            + b"x" * 1200
            + b"\r\n"
        )
        with tempfile.TemporaryDirectory() as state_dir:
            device = self.transfer(config, state_dir)
            self.assertEqual(device.config_path.read_bytes(), config)
            screen = b"".join(device.config_screen_lines())
            self.assertIn(b"HostIP              192.0.2.10\r\n", screen)
            self.assertIn(b"PersonalityVer      Test_Personality\r\n", screen)

    def test_escape_then_six_enters_download_receiver(self):
        receiver_port, _ = memory_serial_pair()
        with tempfile.TemporaryDirectory() as state_dir:
            device = make_device(receiver_port, state_dir)
            device.in_menu = False
            with patch.object(device, "write") as write, patch.object(device, "receive_download") as receive:
                device.receiver(b"\x1b", lambda: False)
                self.assertTrue(device.in_menu)
                write.assert_called_once_with(device.main_menu_lines())

                device.receiver(b"16\r\n", lambda: False)
                receive.assert_not_called()
                device.receiver(b"6\r\n", lambda: False)
                receive.assert_called_once_with()

    def test_xmodem1k_firmware_transfer_updates_status_version(self):
        firmware = b"\x00\x01unit image version 24.5.2.1\x00" + b"\x80" * 1400
        with tempfile.TemporaryDirectory() as state_dir:
            device = self.transfer(firmware, state_dir)

            self.assertEqual(device.firmware_version, "24.5.2.1")
            self.assertTrue(device.firmware_path.is_file())
            status = b"".join(device.status_screen_lines("today"))
            self.assertIn(b"Ver\t\t:24.5.2.1", status)
            self.assertEqual(device.firmware_size, device.firmware_path.stat().st_size)


if __name__ == "__main__":
    unittest.main()
