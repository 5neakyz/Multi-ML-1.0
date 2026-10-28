"""Control a Tenma 72-2535 or 72-2550 power supply.

Uses the Windows serial-port API through ctypes, so no third-party packages are
required. Enabling the output delivers the currently configured voltage to the
connected load.

py program-powersupply.py 5.00
py program-powersupply.py 5.00 --dry-run
py program-powersupply.py
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from decimal import Decimal, InvalidOperation
import logging
import os
from pathlib import Path
import re
import sys
import threading
import time
from collections.abc import Callable


BAUD_RATE = 9600
MAX_VOLTAGE = Decimal("30.00")
VOLTAGE_STEP = Decimal("0.01")
READ_BUFFER_SIZE = 64
READ_TIMEOUT_MS = 500
READ_INTERVAL_TIMEOUT_MS = 50
PURGE_RXCLEAR = 0x0008
OPEN_EXISTING = 3
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

POWER_STATE_LOG_FILE = Path(__file__).resolve().with_name("power-state.log")
power_state_logger = logging.getLogger(f"{__name__}.power_state")
power_state_logger.setLevel(logging.INFO)
power_state_logger.propagate = False
power_state_log_handler: logging.FileHandler | None = None
power_state_logger_lock = threading.Lock()


class DCB(ctypes.Structure):
    _fields_ = [
        ("DCBlength", wintypes.DWORD),
        ("BaudRate", wintypes.DWORD),
        ("fBinary", wintypes.DWORD, 1),
        ("fParity", wintypes.DWORD, 1),
        ("fOutxCtsFlow", wintypes.DWORD, 1),
        ("fOutxDsrFlow", wintypes.DWORD, 1),
        ("fDtrControl", wintypes.DWORD, 2),
        ("fDsrSensitivity", wintypes.DWORD, 1),
        ("fTXContinueOnXoff", wintypes.DWORD, 1),
        ("fOutX", wintypes.DWORD, 1),
        ("fInX", wintypes.DWORD, 1),
        ("fErrorChar", wintypes.DWORD, 1),
        ("fNull", wintypes.DWORD, 1),
        ("fRtsControl", wintypes.DWORD, 2),
        ("fAbortOnError", wintypes.DWORD, 1),
        ("fDummy2", wintypes.DWORD, 17),
        ("wReserved", wintypes.WORD),
        ("XonLim", wintypes.WORD),
        ("XoffLim", wintypes.WORD),
        ("ByteSize", wintypes.BYTE),
        ("Parity", wintypes.BYTE),
        ("StopBits", wintypes.BYTE),
        ("XonChar", ctypes.c_char),
        ("XoffChar", ctypes.c_char),
        ("ErrorChar", ctypes.c_char),
        ("EofChar", ctypes.c_char),
        ("EvtChar", ctypes.c_char),
        ("wReserved1", wintypes.WORD),
    ]


class CommTimeouts(ctypes.Structure):
    _fields_ = [
        ("ReadIntervalTimeout", wintypes.DWORD),
        ("ReadTotalTimeoutMultiplier", wintypes.DWORD),
        ("ReadTotalTimeoutConstant", wintypes.DWORD),
        ("WriteTotalTimeoutMultiplier", wintypes.DWORD),
        ("WriteTotalTimeoutConstant", wintypes.DWORD),
    ]


class WindowsSerialPort:
    """Small synchronous serial-port wrapper for the Tenma command protocol."""

    def __init__(self, port_name: str) -> None:
        if os.name != "nt":
            raise OSError("This script uses the Windows serial-port API.")

        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_api_signatures()

        device_path = rf"\\.\{port_name}"
        self._handle = self._kernel32.CreateFileW(
            device_path,
            GENERIC_READ | GENERIC_WRITE,
            0,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        if self._handle == INVALID_HANDLE_VALUE:
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            self._configure_port()
        except Exception:
            self.close()
            raise

    def _configure_api_signatures(self) -> None:
        kernel32 = self._kernel32
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.SetCommState.argtypes = [wintypes.HANDLE, ctypes.POINTER(DCB)]
        kernel32.SetCommState.restype = wintypes.BOOL
        kernel32.SetCommTimeouts.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(CommTimeouts),
        ]
        kernel32.SetCommTimeouts.restype = wintypes.BOOL
        kernel32.SetupComm.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        kernel32.SetupComm.restype = wintypes.BOOL
        kernel32.PurgeComm.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.PurgeComm.restype = wintypes.BOOL
        kernel32.WriteFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel32.WriteFile.restype = wintypes.BOOL
        kernel32.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel32.ReadFile.restype = wintypes.BOOL

    def _check(self, succeeded: bool) -> None:
        if not succeeded:
            raise ctypes.WinError(ctypes.get_last_error())

    def _configure_port(self) -> None:
        self._check(self._kernel32.SetupComm(self._handle, 4096, 4096))

        dcb = DCB()
        dcb.DCBlength = ctypes.sizeof(DCB)
        dcb.BaudRate = BAUD_RATE
        dcb.fBinary = 1
        dcb.ByteSize = 8
        dcb.Parity = 0
        dcb.StopBits = 0
        self._check(self._kernel32.SetCommState(self._handle, ctypes.byref(dcb)))

        timeouts = CommTimeouts()
        timeouts.ReadIntervalTimeout = READ_INTERVAL_TIMEOUT_MS
        timeouts.ReadTotalTimeoutConstant = READ_TIMEOUT_MS
        self._check(
            self._kernel32.SetCommTimeouts(self._handle, ctypes.byref(timeouts))
        )

    def write(self, data: bytes) -> None:
        buffer = ctypes.create_string_buffer(data)
        bytes_written = wintypes.DWORD()
        self._check(
            self._kernel32.WriteFile(
                self._handle,
                buffer,
                len(data),
                ctypes.byref(bytes_written),
                None,
            )
        )
        if bytes_written.value != len(data):
            raise OSError(f"Serial write was incomplete ({bytes_written.value} bytes).")

    def query(self, command: bytes) -> bytes:
        self._check(self._kernel32.PurgeComm(self._handle, PURGE_RXCLEAR))
        self.write(command)

        buffer = ctypes.create_string_buffer(READ_BUFFER_SIZE)
        bytes_read = wintypes.DWORD()
        self._check(
            self._kernel32.ReadFile(
                self._handle,
                buffer,
                READ_BUFFER_SIZE,
                ctypes.byref(bytes_read),
                None,
            )
        )
        if bytes_read.value == 0:
            raise TimeoutError("The power supply did not reply to the voltage query.")
        return buffer.raw[: bytes_read.value]

    def close(self) -> None:
        handle = getattr(self, "_handle", None)
        if handle is not None and handle != INVALID_HANDLE_VALUE:
            self._handle = None
            if not self._kernel32.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())

    def __enter__(self) -> WindowsSerialPort:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()


def parse_voltage(value: str) -> Decimal:
    try:
        voltage = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("voltage must be a number") from exc

    if not voltage.is_finite() or voltage < 0 or voltage > MAX_VOLTAGE:
        raise argparse.ArgumentTypeError("voltage must be between 0 and 30 volts")
    if voltage.quantize(VOLTAGE_STEP) != voltage:
        raise argparse.ArgumentTypeError("voltage must have at most two decimal places")
    return voltage


def parse_port(value: str) -> str:
    match = re.fullmatch(r"COM([1-9][0-9]*)", value, flags=re.IGNORECASE)
    if match is None:
        raise argparse.ArgumentTypeError("port must be a Windows COM port, such as COM7")
    return f"COM{match.group(1)}"


def set_supply_voltage(port: str, voltage: Decimal) -> Decimal:
    with WindowsSerialPort(port) as supply:
        supply.write(f"VSET1:{voltage:.2f}".encode("ascii"))
        time.sleep(0.1)
        response = supply.query(b"VSET1?")

    set_voltage = Decimal(response.decode("ascii").strip())
    if not set_voltage.is_finite():
        raise ValueError("The power supply returned a non-finite voltage.")
    if abs(set_voltage - voltage) > VOLTAGE_STEP:
        raise ValueError(
            f"Requested {voltage:.2f} V, but the supply reports {set_voltage:.2f} V."
        )
    return set_voltage


def set_supply_output(port: str, enabled: bool) -> str:
    with WindowsSerialPort(port) as supply:
        status = supply.query(b"STATUS?")
        if not status:
            raise RuntimeError("The power supply returned an empty status response.")

        previous_output_is_on = bool(status[0] & 0x40)
        output_is_on = previous_output_is_on
        if output_is_on != enabled:
            supply.write(b"OUT1" if enabled else b"OUT0")
            time.sleep(0.1)
            status = supply.query(b"STATUS?")

    if not status:
        raise RuntimeError("The power supply returned an empty status response.")

    output_is_on = bool(status[0] & 0x40)
    if output_is_on != enabled:
        requested = "on" if enabled else "off"
        raise RuntimeError(f"The power supply did not report that its output is {requested}.")
    if output_is_on != previous_output_is_on:
        _log_power_state_change(output_is_on)
    if output_is_on:
        return "Output is ON. Power is being delivered."
    return "Output is OFF. Power delivery is disabled."


def toggle_supply_output(port: str) -> str:
    with WindowsSerialPort(port) as supply:
        status = supply.query(b"STATUS?")
        if not status:
            raise RuntimeError("The power supply returned an empty status response.")
        previous_output_is_on = bool(status[0] & 0x40)
        requested_state = not previous_output_is_on
        supply.write(b"OUT1" if requested_state else b"OUT0")
        time.sleep(0.1)
        status = supply.query(b"STATUS?")

    if not status:
        raise RuntimeError("The power supply returned an empty status response.")
    if bool(status[0] & 0x40) != requested_state:
        requested = "on" if requested_state else "off"
        raise RuntimeError(f"The power supply did not report that its output is {requested}.")
    _log_power_state_change(requested_state)
    if requested_state:
        return "Output is ON. Power is being delivered."
    return "Output is OFF. Power delivery is disabled."


def _log_power_state_change(output_is_on: bool) -> None:
    global power_state_log_handler
    with power_state_logger_lock:
        if power_state_log_handler is None:
            handler = logging.FileHandler(POWER_STATE_LOG_FILE, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            power_state_logger.addHandler(handler)
            power_state_log_handler = handler
    power_state_logger.info("Power output changed to %s", "ON" if output_is_on else "OFF")


def parse_interval_minutes(value: str) -> int:
    try:
        minutes = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("duration must be a whole number of minutes") from exc
    if minutes < 1:
        raise argparse.ArgumentTypeError("duration must be at least 1 minute")
    return minutes


def format_countdown(seconds: float) -> str:
    remaining = max(0, int(seconds + 0.999))
    hours, remainder = divmod(remaining, 3600)
    minutes, seconds_remaining = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_remaining:02d}"


def run_gui() -> int:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Tenma Power Supply")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=16)
    frame.grid()

    ttk.Label(frame, text="Serial port:").grid(row=0, column=0, sticky="w", pady=4)
    port_entry = ttk.Entry(frame, width=12)
    port_entry.insert(0, "COM7")
    port_entry.grid(row=0, column=1, sticky="w", pady=4)

    ttk.Label(frame, text="Voltage (V):").grid(row=1, column=0, sticky="w", pady=4)
    voltage_entry = ttk.Entry(frame, width=12)
    voltage_entry.insert(0, "5.00")
    voltage_entry.grid(row=1, column=1, sticky="w", pady=4)

    status = tk.StringVar(value="Ready")
    status_label = ttk.Label(frame, textvariable=status, wraplength=300)
    ttk.Label(frame, text="Power ON for (minutes):").grid(
        row=4, column=0, sticky="w", pady=4
    )
    on_duration_entry = ttk.Entry(frame, width=12)
    on_duration_entry.insert(0, "30")
    on_duration_entry.grid(row=4, column=1, sticky="w", pady=4)

    ttk.Label(frame, text="Power OFF for (minutes):").grid(
        row=5, column=0, sticky="w", pady=4
    )
    off_duration_entry = ttk.Entry(frame, width=12)
    off_duration_entry.insert(0, "10")
    off_duration_entry.grid(row=5, column=1, sticky="w", pady=4)

    timer = tk.StringVar(value="Time left: --:--:--")
    timer_label = ttk.Label(frame, textvariable=timer)
    timer_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
    status_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))
    cycle_stop: threading.Event | None = None
    closing_requested = False
    countdown_after_id: str | None = None
    countdown_generation = 0

    def cancel_countdown() -> None:
        nonlocal countdown_after_id, countdown_generation
        countdown_generation += 1
        if countdown_after_id is not None:
            root.after_cancel(countdown_after_id)
            countdown_after_id = None
        timer.set("Time left: --:--:--")

    def begin_countdown(
        stop: threading.Event,
        phase: str,
        deadline: float,
    ) -> None:
        nonlocal countdown_after_id, countdown_generation
        if countdown_after_id is not None:
            root.after_cancel(countdown_after_id)
        countdown_generation += 1
        generation = countdown_generation

        def update_countdown() -> None:
            nonlocal countdown_after_id
            if generation != countdown_generation or stop.is_set():
                return
            seconds_left = max(0, deadline - time.monotonic())
            timer.set(f"{phase} time left: {format_countdown(seconds_left)}")
            countdown_after_id = root.after(1000, update_countdown)

        update_countdown()

    def finish_action(message: str, button: ttk.Button) -> None:
        button.state(["!disabled"])
        status.set(message)
        if message.startswith("Output is ON."):
            button.configure(text="Output OFF")
        elif message.startswith("Output is OFF."):
            button.configure(text="Output ON")

    def update_cycle_status(message: str, output_is_on: bool | None = None) -> None:
        status.set(message)
        if output_is_on is not None:
            output_button.configure(text="Output OFF" if output_is_on else "Output ON")

    def start_action(
        button: ttk.Button,
        busy_message: str,
        operation: Callable[[], str],
    ) -> None:
        button.state(["disabled"])
        status.set(busy_message)

        def worker() -> None:
            try:
                result = operation()
            except (
                OSError,
                TimeoutError,
                UnicodeDecodeError,
                InvalidOperation,
                ValueError,
                RuntimeError,
            ) as exc:
                root.after(
                    0,
                    finish_action,
                    f"Error: {exc}",
                    button,
                )
            else:
                root.after(
                    0,
                    finish_action,
                    result,
                    button,
                )

        threading.Thread(target=worker, daemon=True).start()

    def apply_voltage(button: ttk.Button) -> None:
        try:
            port = parse_port(port_entry.get().strip())
            voltage = parse_voltage(voltage_entry.get().strip())
        except argparse.ArgumentTypeError as exc:
            status.set(str(exc))
            return

        start_action(
            button,
            f"Setting {voltage:.2f} V on {port}...",
            lambda: f"Voltage setpoint: {set_supply_voltage(port, voltage):.2f} V",
        )

    set_button = ttk.Button(frame, text="Set voltage")
    set_button.configure(command=lambda: apply_voltage(set_button))
    set_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 4))

    output_button = ttk.Button(frame, text="Toggle output")

    def toggle_output() -> None:
        try:
            port = parse_port(port_entry.get().strip())
        except argparse.ArgumentTypeError as exc:
            status.set(str(exc))
            return
        start_action(
            output_button,
            f"Checking output on {port}...",
            lambda: toggle_supply_output(port),
        )

    output_button.configure(command=toggle_output)
    output_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)

    run_button = ttk.Button(frame, text="Run")
    run_button.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 4))

    cycle_inputs = [
        port_entry,
        voltage_entry,
        on_duration_entry,
        off_duration_entry,
        set_button,
        output_button,
    ]

    def finish_cycle(message: str, output_is_on: bool | None) -> None:
        nonlocal cycle_stop, closing_requested
        cancel_countdown()
        cycle_stop = None
        for widget in cycle_inputs:
            widget.state(["!disabled"])
        run_button.configure(text="Run")
        run_button.state(["!disabled"])
        update_cycle_status(message, output_is_on=output_is_on)
        if closing_requested and output_is_on is False:
            root.destroy()
        else:
            closing_requested = False

    def run_cycle(port: str, on_minutes: int, off_minutes: int, stop: threading.Event) -> None:
        failure: Exception | None = None
        try:
            while not stop.is_set():
                set_supply_output(port, True)
                on_deadline = time.monotonic() + on_minutes * 60
                root.after(
                    0,
                    update_cycle_status,
                    f"Output ON for {on_minutes} minute(s).",
                    True,
                )
                root.after(0, begin_countdown, stop, "ON", on_deadline)
                if stop.wait(on_minutes * 60):
                    break

                set_supply_output(port, False)
                off_deadline = time.monotonic() + off_minutes * 60
                root.after(
                    0,
                    update_cycle_status,
                    f"Output OFF for {off_minutes} minute(s).",
                    False,
                )
                root.after(0, begin_countdown, stop, "OFF", off_deadline)
                if stop.wait(off_minutes * 60):
                    break
        except (
            OSError,
            TimeoutError,
            UnicodeDecodeError,
            InvalidOperation,
            ValueError,
            RuntimeError,
        ) as exc:
            failure = exc

        try:
            set_supply_output(port, False)
        except (
            OSError,
            TimeoutError,
            UnicodeDecodeError,
            InvalidOperation,
            ValueError,
            RuntimeError,
        ) as exc:
            message = f"Failed to turn output off: {exc}"
            output_is_on = None
            if failure is not None:
                message = f"Cycle failed: {failure}. {message}"
        else:
            output_is_on = False
            if failure is not None:
                message = f"Cycle failed: {failure}. Output is OFF."
            else:
                message = "Cycle stopped. Output is OFF."

        root.after(0, finish_cycle, message, output_is_on)

    def run_or_stop_cycle() -> None:
        nonlocal cycle_stop
        if cycle_stop is not None:
            cycle_stop.set()
            run_button.configure(text="Stopping...")
            run_button.state(["disabled"])
            status.set("Stopping cycle and turning output off...")
            return

        try:
            port = parse_port(port_entry.get().strip())
            on_minutes = parse_interval_minutes(on_duration_entry.get().strip())
            off_minutes = parse_interval_minutes(off_duration_entry.get().strip())
        except argparse.ArgumentTypeError as exc:
            status.set(str(exc))
            return

        stop = threading.Event()
        cycle_stop = stop
        for widget in cycle_inputs:
            widget.state(["disabled"])
        run_button.configure(text="Stop")
        status.set("Starting cycle...")
        threading.Thread(
            target=run_cycle,
            args=(port, on_minutes, off_minutes, stop),
            daemon=True,
        ).start()

    run_button.configure(command=run_or_stop_cycle)

    def close_window() -> None:
        nonlocal closing_requested
        if cycle_stop is None:
            root.destroy()
            return
        closing_requested = True
        cycle_stop.set()
        run_button.configure(text="Stopping...")
        run_button.state(["disabled"])
        status.set("Turning output off before closing...")
        root.after(100, wait_for_cycle_then_close)

    def wait_for_cycle_then_close() -> None:
        if cycle_stop is None and closing_requested:
            root.destroy()
        elif cycle_stop is not None:
            root.after(100, wait_for_cycle_then_close)

    root.protocol("WM_DELETE_WINDOW", close_window)
    voltage_entry.bind(
        "<Return>",
        lambda _event: apply_voltage(set_button),
    )
    voltage_entry.focus_set()
    root.mainloop()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Set the voltage setpoint on a Tenma 72-2535 or 72-2550."
    )
    parser.add_argument(
        "voltage",
        nargs="?",
        type=parse_voltage,
        help="target voltage (0 to 30 V); omit to open the GUI",
    )
    parser.add_argument(
        "--port",
        type=parse_port,
        default="COM7",
        help="serial port (default: COM7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the command without opening a serial port",
    )
    args = parser.parse_args(argv)

    if args.voltage is None:
        if args.dry_run:
            parser.error("--dry-run requires a voltage argument")
        return run_gui()

    if args.dry_run:
        command = f"VSET1:{args.voltage:.2f}".encode("ascii")
        print(f"Would send {command.decode('ascii')} to {args.port} (9600 baud, 8-N-1).")
        return 0

    try:
        set_voltage = set_supply_voltage(args.port, args.voltage)
    except (OSError, TimeoutError, UnicodeDecodeError, InvalidOperation, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Voltage setpoint read back: {set_voltage:.2f} V")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())