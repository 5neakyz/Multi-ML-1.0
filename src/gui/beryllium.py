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
from gui.notebook_handler import NotebookHandler
from stager import Stager
from utils.pb_data import Pb_data
from gui.help_menu import HelpMenu
from gui.menu_bar import MenuBar
from gui.footer import Footer
from gui.option_selection import Option_Selection
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
        #ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("src/themes/lavender.json") 
        self.protocol("WM_DELETE_WINDOW",self.close_window)


        ##vars
        self.selected_comports = [] # user selection
        self.selected_comports_str = ctk.StringVar(value=self.selected_comports) # string list
        self.devices = []
        self.notebook_Handler = None
        self.connect_btn_text_str = ctk.StringVar(value='Connect')
        self.help_doc = "../assests/doc.html"

        self.progress_bar_object = Pb_data()
        
#frames / gui setup

# Menu Bar
        self.menu_bar = MenuBar(self)
        self.config(menu=self.menu_bar)
# Footer Info Bar
        self.footer_bar = Footer(self)
        self.footer_bar.pack(fill="x",side="bottom")
# option selection
        self.option_selection = Option_Selection(self,height=60)
        self.option_selection.pack()

# Main

    #display tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both",expand=True,padx=5,pady=5)

        #self.new_pad = ctk.CTkFrame(self.tab_view)

        self.tab_view.add("Tab 1")


        self.mainloop()

    def populate_notebook(self):
        self.clear_child_in_frame(self.tab_view)
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        labels = []
        for device in self.devices:
            pad = ctk.CTkFrame(self.tab_view)
            self.tab_view.add(pad,text=device.serial_port_name)
            label = tk.Text(pad)
            label.pack(expand=True,fill="both")
            labels.append(label)

        self.notebook_Handler = NotebookHandler(labels,self.devices)
        self.notebook_Handler.start_handler()

    def run_btn_press(self):
        #button setup
        self.side_bar_run_btn.configure(state="disabled")
        #footer loop / info setup
        self.footer_bar.start_update_info_loop()
        #stager setup
        stager_thread = Stager(self.devices)
        #tasks(pers , firm , BLE)
        stager_thread.tasks  = [self.check_push_firm.get(),self.check_push_pers.get(),self.check_push_BLE.get()]
        stager_thread.progress_bar_object = self.progress_bar_object
        stager_thread.firmware_path = self.firmware_path
        stager_thread.personality_path = self.personality_path
        stager_thread.BLE_path = self.ble_path
        # start stager
        results = stager_thread.start()
        logger.info(results)
        #self.display_results(self.stager_results_frame,results,warplen=400,align="left")
        self.info_running = False
        self.side_bar_run_btn.configure(state="enable")
  
    def connect_disconnect_btn(self):
        if self.connect_btn_text_str.get() == 'Connect':
            self.connect_btn_text_str.set('Disconnect')
            self.connect_btn_press()
        else:
            self.connect_btn_text_str.set('Connect')
            self.disconnect_btn_press()

    def connect_btn_press(self):
        self.progress_bar_object.total = 100
        self.progress_bar_object.add_to_progress(10)
        print(self.progress_bar_object.perc_current_progress())
        self.footer_bar.start_update_info_loop()

        time.sleep(2)

        self.progress_bar_object.add_to_progress(10)

        # self.side_bar_connect_btn.configure(state='disable')
        # logger.info(f'Connecting : {self.selected_comports}')
        # #change frame text 
        # self.side_bar_selected_devices_frame.configure(text="Connecting")
        # #remove all in selected devices frame
        # self.clear_child_in_frame(self.side_bar_selected_devices_frame)
        # #ensures no duplicates of already existing objects, has no function on first use
        # temp_devices_list = []
        # for device in self.devices:
        #     temp_devices_list.append(device.serial_port_name)
        # #creates device objects for devices that dont already exist
        # for device in self.selected_comports:
        #     if device not in temp_devices_list:
        #         self.devices.append(Device(device))
        # #create threadpool for all devices threadpool(function , devices)
        # results = self.create_threadpool(self.is_connection_live,self.devices)
        # #display results
        # self.display_results(self.side_bar_selected_devices_frame,results)

        # #insert logic for buttons
        # if all(result[1] for result in results):
        #     self.side_bar_run_btn.configure(state='enable')

        # #reset frame text
        # self.side_bar_selected_devices_frame.configure(text="Selected Devices")
        # self.side_bar_connect_btn.configure(state='enable')
        # #notebook
        # self.populate_notebook()

    def disconnect_btn_press(self):
        self.clear_child_in_frame(self.side_bar_selected_devices_frame)
        self.side_bar_run_btn.configure(state='disable')
        # safely disconnect current units
        for device in self.devices:
            device.listener.interrupt()
            device.disconnect()
            logger.info(f'{device.serial_port_name} TEXT BOX UPDATE READ {device.listener.needs_interrupt,device.serial_connection}')
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        #resets all comport variables and re-searches for any new comports
        self.raw_comports = serial.tools.list_ports.comports() # comports on pc
        self.comports = self.get_comport_names() #comport names
        self.list_box_items.set(self.comports)
        self.devices = []
        #
        self.clear_child_in_frame(self.tab_view)
        #needs placeholder
        self.side_bar_selected_devices_placeholder = ctk.CTkLabel(self.side_bar_selected_devices_frame,textvariable=self.selected_comports_str,wraplength=55)
        self.side_bar_selected_devices_placeholder.pack(padx=20,pady=20)

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
    
    def send_commands(self,commands):
        for device in self.devices:
            device.write_commands(commands)

    def close_window(self):
        for device in self.devices:
            try:
                device.listener.interrupt()
                device.disconnect()
            except Exception as e: print(e)
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        self.info_interrupt = True
        self.devices.clear()
        self.destroy()
        logger.info(f'Safely closed')

if __name__ == "__main__":
    format = "%(asctime)s.%(msecs)04d - %(message)s"
    logging.basicConfig(format=format,level=logging.INFO,datefmt="%H:%M:%S")
    Beryllium()
