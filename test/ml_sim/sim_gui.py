import queue
import time
import tkinter as tk
from tkinter import messagebox, ttk

from serial.tools import list_ports

from sim_device import Device


class SimulatorGUI:
    def __init__(self, root, initial_port=None):
        self.root = root
        self.root.title("ML Unit Simulator")
        self.root.geometry("1000x650")
        self.events = queue.Queue()
        self.device = None
        self.port_choices = {}
        self.initial_port = initial_port

        self._build_widgets()
        self.refresh_ports()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(50, self._poll_events)

    def _build_widgets(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill="x")

        ttk.Label(controls, text="Serial port:").pack(side="left", padx=(0, 6))
        self.port_var = tk.StringVar()
        self.port_box = ttk.Combobox(
            controls,
            textvariable=self.port_var,
            state="readonly",
            width=44,
        )
        self.port_box.pack(side="left", padx=(0, 6))

        self.refresh_button = ttk.Button(controls, text="Refresh", command=self.refresh_ports)
        self.refresh_button.pack(side="left", padx=3)
        self.connect_button = ttk.Button(controls, text="Connect", command=self.connect)
        self.connect_button.pack(side="left", padx=3)
        self.disconnect_button = ttk.Button(
            controls,
            text="Disconnect",
            command=self.disconnect,
            state="disabled",
        )
        self.disconnect_button.pack(side="left", padx=3)
        ttk.Button(controls, text="Clear", command=self.clear_output).pack(side="right", padx=3)

        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(self.root, textvariable=self.status_var, padding=(10, 0, 10, 6)).pack(
            anchor="w"
        )
        ttk.Label(
            self.root,
            text="RX: application to simulator    TX: simulator to application",
            padding=(10, 0, 10, 6),
        ).pack(anchor="w")

        output_frame = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        output_frame.pack(fill="both", expand=True)
        self.output = tk.Text(
            output_frame,
            wrap="none",
            state="disabled",
            font=("Consolas", 9),
        )
        vertical_scroll = ttk.Scrollbar(output_frame, command=self.output.yview)
        horizontal_scroll = ttk.Scrollbar(
            output_frame,
            orient="horizontal",
            command=self.output.xview,
        )
        self.output.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )
        self.output.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        self.output.tag_configure("RX", foreground="#155724")
        self.output.tag_configure("TX", foreground="#174a7e")

    def refresh_ports(self):
        selected_port = self.port_choices.get(self.port_var.get()) or self.initial_port
        self.initial_port = None

        ports = list(list_ports.comports())
        self.port_choices = {
            f"{port.device} - {port.description}": port.device
            for port in ports
        }
        if selected_port and selected_port not in self.port_choices.values():
            self.port_choices[f"{selected_port} - (not currently listed)"] = selected_port

        choices = list(self.port_choices)
        self.port_box.configure(values=choices)
        selected_label = next(
            (label for label, port in self.port_choices.items() if port == selected_port),
            choices[0] if choices else "",
        )
        self.port_var.set(selected_label)
        if not choices:
            self.status_var.set("No serial ports detected")
        elif self.device is None:
            self.status_var.set("Disconnected")

    def connect(self):
        if self.device is not None:
            return

        port = self.port_choices.get(self.port_var.get())
        if port is None:
            messagebox.showwarning("Select a port", "Select a serial port before connecting.")
            return

        device = Device(
            port,
            on_serial_io=lambda direction, data: self.events.put((direction, data)),
        )
        if not device.serial_connection:
            error = device.connection_error
            detail = f"\n\n{error}" if error is not None else ""
            messagebox.showerror("Connection failed", f"Could not open {port}.{detail}")
            self.status_var.set(f"Failed to connect to {port}")
            return

        self.device = device
        self.status_var.set(f"Connected to {port} at {device.serial_port_baud} baud")
        self._set_connection_controls(True)

    def disconnect(self):
        if self.device is None:
            return
        if self.device.download_active:
            messagebox.showwarning(
                "Transfer in progress",
                "Wait for the XMODEM transfer to finish before disconnecting.",
            )
            return

        port = self.device.serial_port_name
        self.device.shutdown()
        self.device = None
        self.status_var.set(f"Disconnected from {port}")
        self._set_connection_controls(False)

    def _set_connection_controls(self, connected):
        self.port_box.configure(state="disabled" if connected else "readonly")
        self.refresh_button.configure(state="disabled" if connected else "normal")
        self.connect_button.configure(state="disabled" if connected else "normal")
        self.disconnect_button.configure(state="normal" if connected else "disabled")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    @staticmethod
    def _format_payload(data):
        if len(data) > 160:
            return f"{data[:80]!r} ... [{len(data)} bytes]"
        return repr(data)

    def _poll_events(self):
        self.output.configure(state="normal")
        count = 0
        while count < 250:
            try:
                direction, data = self.events.get_nowait()
            except queue.Empty:
                break

            timestamp = time.strftime("%H:%M:%S")
            self.output.insert(
                "end",
                f"[{timestamp}] {direction} {self._format_payload(data)}\n",
                direction,
            )
            count += 1

        if count:
            line_count = int(self.output.index("end-1c").split(".")[0])
            if line_count > 10000:
                self.output.delete("1.0", f"{line_count - 9000}.0")
            self.output.see("end")
        self.output.configure(state="disabled")

        if self.device is not None and self.device.download_active:
            self.status_var.set(f"XMODEM-1K transfer active on {self.device.serial_port_name}")
            self.disconnect_button.configure(state="disabled")
        elif self.device is not None:
            self.status_var.set(
                f"Connected to {self.device.serial_port_name} "
                f"at {self.device.serial_port_baud} baud"
            )
            self.disconnect_button.configure(state="normal")

        self.root.after(50, self._poll_events)

    def close(self):
        if self.device is not None and self.device.download_active:
            messagebox.showwarning(
                "Transfer in progress",
                "Wait for the XMODEM transfer to finish before closing the simulator.",
            )
            return
        if self.device is not None:
            self.device.shutdown()
            self.device = None
        self.root.destroy()
