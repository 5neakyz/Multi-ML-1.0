import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
import concurrent.futures
import serial.tools.list_ports

from device import Device
from stager import Stager

logger = logging.getLogger(__name__)

class ConnectBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # vars
        self.parent = parent
        self.selected_comports = []
        self.selected_comports_str = ctk.StringVar(value=self.selected_comports) # string list
        self.connect_btn_text_str = ctk.StringVar(value='Connect')

        # layout
        self.configure(border_width=1,height=50)
        self.pack(fill="x",side="bottom",padx=1,pady=1)
        #buttons and connected frame

        self.run_btn  = ctk.CTkButton(self,state='disabled',text="Run",height=26,command=lambda: threading.Thread(daemon=True,target=self.run_btn_press).start())
        self.run_btn.pack(fill="x",side="right",padx=3,pady=1)
        self.connect_btn = ctk.CTkButton(self,height=26,textvariable=self.connect_btn_text_str,command=lambda: threading.Thread(daemon=True,target=self.connect_disconnect_btn).start())
        self.connect_btn.pack(fill="x",side="right",padx=10,pady=1)
        self.connect_selection_frame = ctk.CTkFrame(self)
        self.selected_devices_label =ctk.CTkLabel(self,text="Selected:").pack(side="left",padx=10,pady=1)
        self.selected_devices_placeholder = ctk.CTkLabel(self.connect_selection_frame,textvariable=self.selected_comports_str).pack(side="left",padx=10,pady=1)
        self.connect_selection_frame.pack(fill="x",side="left",padx=3,pady=3)


    def run_btn_press(self):
        self.run_btn.configure(state='disabled')
        self.parent.clear_footer_results()
        self.parent.start_footer_info_loop()
        stager = Stager(self.parent.devices,
                        progress_bar_object=self.parent.progress_bar_object,
                        tasks=self.parent.get_option_selection_tasks(),
                        paths=self.parent.get_option_selection_path())
        results = stager.start()
        self.parent.interrupt_footer_info_loop()
        self.parent.give_footer_results(results)
        #self.display_results(self.connect_selection_frame,results,align="right")
        self.run_btn.configure(state='normal')

    def connect_disconnect_btn(self):
        if self.connect_btn_text_str.get() == 'Connect':
            self.connect_btn_text_str.set('Disconnect')
            self.connect_btn_press()
        else:
            self.connect_btn_text_str.set('Connect')
            self.disconnect_btn_press()

    def connect_btn_press(self):

        print(self.selected_comports)
        if not self.selected_comports:
            return

        logger.info(f'Connecting : {self.selected_comports}')
        self.connect_btn.configure(state='disabled')
        #create list of objects
        temp_devices_list = []
        for device in self.parent.devices:
            temp_devices_list.append(device.serial_port_name)
        #creates device objects for devices that dont already exist
        for device in self.selected_comports:
            if device not in temp_devices_list:
                self.parent.devices.append(Device(device))
        #create threadpool for all devices threadpool(function , devices)
        results = self.create_threadpool(self.parent.is_connection_live,self.parent.devices)
        #display results
        self.display_results(self.connect_selection_frame,results)
        #insert logic for run button
        if all(result[1] for result in results):
            self.run_btn.configure(state='normal')
        # re-enable connect button
        self.connect_btn.configure(state='normal')
        self.parent.populate_display_frame()

    def disconnect_btn_press(self):
        self.clear_child_in_frame(self.connect_selection_frame)
        self.run_btn.configure(state='disabled',)
        self.selected_devices_placeholder = ctk.CTkLabel(self.connect_selection_frame,textvariable=self.selected_comports_str).pack(side="left",padx=10,pady=1)
        # safely disconnect current units
        for device in self.parent.devices:
            device.listener.interrupt()
            device.disconnect()
            logger.info(f'{device.serial_port_name} TEXT BOX UPDATE READ {device.listener.needs_interrupt,device.serial_connection}')

        self.parent.devices = []


    def set_selected_ports(self,ports):
        self.selected_comports = ports
        self.selected_comports_str.set(self.selected_comports)
        self.selected_devices_label

    def display_results(self,parent_label,results,align="left"):
    # Result[0] (string) = COM PORT
    # Result[1] (bool)= outcome
        self.clear_child_in_frame(parent_label)
        for result in (results):
            if result[1] == True:
                color = '#217346'
            else:
                color = '#b40d1b'
            frame = ctk.CTkFrame(parent_label,fg_color=color)
            frame.pack(padx=3, pady=3,side=align)
            label = ctk.CTkLabel(frame,text_color='white',text=result[0],bg_color=color)
            label.pack(padx=5, pady=3,side=align)


    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()

    def create_threadpool(self,function,items:list) ->list:
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:# parallelism 
            tasks = [executor.submit(function,item) for item in items]
            for x in concurrent.futures.as_completed(tasks):
                results.append(x.result())
        return results
    
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    ConnectBar(root)
    root.mainloop()