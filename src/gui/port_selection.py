import customtkinter as ctk
import serial.tools.list_ports


class PortSelection(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = controller if controller is not None else parent
        self.configure(border_width=1)

        self.port_vars = {}

        self.title_label = ctk.CTkLabel(self, text="Available Ports")
        self.title_label.pack(side="left", padx=5, pady=5)

        self.port_list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.port_list_frame.pack(side="left", fill="x", expand=True, padx=5, pady=3)

        self.refresh_button = ctk.CTkButton(
            self,
            text="Refresh",
            width=80,
            command=self.refresh_ports,
        )
        self.refresh_button.pack(side="right", padx=3, pady=3)
        self.disconnect_all_button = ctk.CTkButton(
            self,
            text="Disconnect All",
            width=110,
            command=self.clear_selected_ports,
        )
        self.disconnect_all_button.pack(side="right", padx=3, pady=3)

        self.refresh_ports()

    def get_comport_names(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]

        # TEMPORARY test data: remove this block after validating the port layout.
        ports.extend(
            f"COM{number}"
            for number in range(30, 40)
            if f"COM{number}" not in ports
        )

        def sort_key(port):
            name = port.upper()
            if name.startswith("COM") and name[3:].isdigit():
                return 0, int(name[3:])
            return 1, port.lower()

        return sorted(ports, key=sort_key)

    def refresh_ports(self):
        for widget in self.port_list_frame.winfo_children():
            widget.destroy()
        self.port_vars.clear()

        selected_ports = self.parent.selected_comports
        for index, port in enumerate(self.get_comport_names()):
            selected = ctk.BooleanVar(value=port in selected_ports)
            self.port_vars[port] = selected
            checkbox = ctk.CTkCheckBox(
                self.port_list_frame,
                text=port,
                variable=selected,
                command=lambda selected_port=port: self.toggle_port(selected_port),
            )
            checkbox.grid(row=index // 6, column=index % 6, padx=5, pady=2, sticky="w")

    def toggle_port(self, port):
        selected_ports = list(self.parent.selected_comports)
        if port in selected_ports:
            selected_ports.remove(port)
        else:
            selected_ports.append(port)
        self.parent.set_selected_ports(selected_ports)

    def clear_selected_ports(self):
        self.parent.clear_selected_ports()
        for selected in self.port_vars.values():
            selected.set(False)
