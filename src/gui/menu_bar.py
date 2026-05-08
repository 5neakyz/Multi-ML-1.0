import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
import os
import sys
import threading
import logging
import serial.tools.list_ports
logger = logging.getLogger(__name__)

class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        self.menu_bar = self
        self.parent = parent
        
        #delete later ????
        self.raw_comports = serial.tools.list_ports.comports() # comports on pc
        self.comports = self.get_comport_names() #comport names

        self.commands = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_file = tk.Menu(self.menu_bar)
        self.menu_help = tk.Menu(self.menu_bar)
        self.menu_ports= tk.Menu(self.menu_bar)
        self.settings= tk.Menu(self.menu_bar)

        self.populate_port_menu()
        #self.menu_bar.add_cascade(menu=self.menu_file, label='File')
        self.menu_bar.add_cascade(menu=self.settings, label='Settings')
        self.menu_bar.add_cascade(menu=self.menu_help, label='Help')
        self.menu_bar.add_cascade(menu=self.menu_ports, label='Ports')
        self.menu_bar.add_cascade(menu=self.commands, label='Commands')
        
        self.settings.add_command(label="90")
        #commands
        self.commands.add_command(label="9HY",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","h","y"],)).start())
        self.commands.add_command(label="9IY",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","i","y"],)).start())
        self.commands.add_command(label="9JY",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","j","y"],)).start())
        self.commands.add_command(label="9KA",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","k","a"],)).start())
        self.commands.add_command(label="9KB",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","k","b"],)).start())
        self.commands.add_command(label="9L",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","l"],)).start())

        #self.menu_help.add_command(label="Help",command=lambda: HelpMenu(self))

        #self.menu_bar.add_command(label="esc: Main Menu",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc"],)).start())
        self.menu_bar.add_command(label="3: View Config",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","3"],)).start())
        self.menu_bar.add_command(label="4: Status Screen",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","4"],)).start())
        self.menu_bar.add_command(label="F: Prod TS",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","f"],)).start())
        self.menu_bar.add_command(label="G: Sys Info",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","g "],)).start())

    def populate_port_menu(self):
        for port in self.comports:
            self.menu_ports.add_command(label=f'{port}',command=lambda port = port: threading.Thread(daemon=True,target=self.selected_port,args=(f'{port}',)).start())
        self.menu_ports.add_command(label="resfresh",command=lambda: threading.Thread(daemon=True,target=self.refresh_port).start())
        self.menu_ports.add_command(label="disconnect all",command=lambda: threading.Thread(daemon=True,target=self.clear_selected_ports).start())


    def close_window(self):
        self.destroy()

    def get_comport_names(self)-> list:
        comport_list = []
        for item in self.raw_comports:
            comport_list.append(item.device)
        return self.sort_comports(comport_list)
    
    def sort_comports(self,list):
        sorted_list = []
        for comport in list:
            comport = comport.replace("COM","")
            try:
                sorted_list.append(int(comport))
            except:
                sorted_list.append(comport)
        sorted_list.sort()
        list = []
        for item in sorted_list:
            item =f"COM{item}"
            list.append(item)
        return list
        
    def selected_port(self,port):
        logger.info(f'Selected: {port}')
        if port in self.parent.selected_comports:
            (self.parent.selected_comports.remove(port))
        else:
            (self.parent.selected_comports.append(port))
        
        self.parent.selected_comports_str.set(self.parent.selected_comports)
        self.parent.connect_bar.set_selected_ports(self.parent.selected_comports)

    def clear_selected_ports(self):
        self.parent.selected_comports = []
        self.parent.selected_comports_str.set(self.parent.selected_comports)
        self.parent.connect_bar.set_selected_ports(self.parent.selected_comports)

    def refresh_port(self):
        self.raw_comports = serial.tools.list_ports.comports() # comports on pc
        self.comports = self.get_comport_names() #comport names
        self.menu_ports.delete(0,"end")
        self.populate_port_menu()


if __name__ == "__main__":
    def send_commands(command):
        print(command)

    root = tk.Tk()
    root.geometry(f"{500}x{200}")
    root.config(menu = MenuBar(root))
    root.mainloop()

