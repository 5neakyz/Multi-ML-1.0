import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk

import serial.tools.list_ports
import time
import os
import sys
import webbrowser
import threading
import logging
import concurrent.futures

#my classes
from device import Device
from stager import Stager

from utils.pb_data import Pb_data

from display_handler import DisplayHandler
from gui.help_menu import HelpMenu
from gui.menu_bar import MenuBar
from gui.footer import Footer
from gui.option_selection import OptionSelection
from gui.connect_bar import ConnectBar
from gui.display_devices import DisplayDevices
#247F4C

logger = logging.getLogger(__name__)

class Beryllium(ctk.CTk):
    def __init__(self):
        super().__init__()
# configure window
        self.title("ML Multi Stager v2.0.0")
        self.geometry(f"{800}x{600}")

        #self.bind('<KeyPress>', self.onKeyPress)
        self.bind('<Double-1>',self.copy_on_double_click)

#style
        self.option_add("*tearOff", False) # This is always a good idea
        icon_path = self.resource_path("../assests/MultiUnits.ico")
        self.iconbitmap(icon_path)
        ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("src/themes/lavender.json") 
        self.configure(fg_color="gray17")
        self.protocol("WM_DELETE_WINDOW",self.close_window)
        ctk.set_widget_scaling(1)

##vars
        self.selected_comports = [] # user selection
        self.selected_comports_str = ctk.StringVar(value=self.selected_comports) # string list
        self.devices = []

        self.display_handler = None

        self.help_doc = "../assests/doc.html"

        self.progress_bar_object = Pb_data()
        
#frames / gui setup
 
# Menu Bar
        self.menu_bar = MenuBar(self)
        self.config(menu=self.menu_bar)
# Connect bar
        self.connect_bar = ConnectBar(self)
        self.connect_bar.pack(fill="x",side="top")
# Footer Info Bar
        self.footer_bar = Footer(self)
        self.footer_bar.pack(fill="x",side="bottom")
# Option Selection
        self.option_selection = OptionSelection(self,height=80)
        self.option_selection.pack()
# Main display
        self.display_devices =DisplayDevices(self)
        self.display_devices.pack(expand=True,fill="both")

        self.mainloop()
# funcs
    def create_threadpool(self,function,items:list) ->list:
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:# parallelism 
            tasks = [executor.submit(function,item) for item in items]
            for x in concurrent.futures.as_completed(tasks):
                results.append(x.result())
        return results

    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()
        
    def resource_path(self,relative_path) -> str:
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def onKeyPress(self,event):
        print(f'You pressed: {event.keysym}')

    def copy_on_double_click(self,event):
        try:
            field_value = event.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()  # clear clipboard contents
            self.clipboard_append(field_value)  # append new value to clipbaord
        except Exception:
            pass
    
    def is_connection_live(self,unit):
        return unit.serial_port_name,unit.is_alive()
    
    #used by menu bar
    def send_commands(self,commands):
        for device in self.devices:
            device.write_commands(commands)
    # kill everything on close
    def close_window(self):
        for device in self.devices:
            try:
                device.listener.interrupt()
                device.disconnect()
            except Exception as e: print(e)
        if self.display_handler:
            self.display_handler.interrupt()
        self.info_interrupt = True
        self.devices.clear()
        self.destroy()
        logger.info(f'Safely closed')

if __name__ == "__main__":
    format = "%(asctime)s.%(msecs)04d - %(message)s"
    logging.basicConfig(format=format,level=logging.INFO,datefmt="%H:%M:%S")
    Beryllium()
