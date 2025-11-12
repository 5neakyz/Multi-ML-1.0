import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
logger = logging.getLogger(__name__)

class Footer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # vars
        self.parent = parent
        self.info_running = False
        self.info_interrupt = False
        self.current_progress = '0 / 0'
        self.current_progress_str = ctk.StringVar(value=self.current_progress)
        self.current_progress_perc = '0%'
        self.current_progress_perc_str = ctk.StringVar(value=self.current_progress_perc)
        self.elapsed_time = '00:00:00'
        self.elapsed_time_str = ctk.StringVar(value=self.elapsed_time)
        self.footer_start_time = ''
        self.results = "MESSAGE"
        self.results_str = ctk.StringVar(value=self.results)

        # layout
        self.pack(fill="x",side="bottom",padx=1,pady=1)

        # info frame
        self.footer_info_bar = ctk.CTkFrame(self,border_width=1,height=30)
        self.footer_info_bar.pack(fill="x",side="bottom")
        
        self.results_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.results_str).pack(padx=10,pady=1,side="left")

        self.elapsed_time_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.elapsed_time_str).pack(padx=10,pady=1,side="right")
        self.current_progress_perc_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_perc_str).pack(padx=10,pady=1,side="right")
        self.current_progress_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_str).pack(padx=10,pady=1,side="right")

    def _update_footer_info_loop(self):
        self.footer_start_time = time.time()
        print(f'{self.parent.progress_bar_object.progress} / {self.parent.progress_bar_object.total}')
        while self.info_running and not self.info_interrupt:
            self.current_progress = f'{self.parent.progress_bar_object.progress} / {self.parent.progress_bar_object.total}'
            self.current_progress_str.set(self.current_progress)

            self.current_progress_perc = self.parent.progress_bar_object.perc_current_progress()
            self.current_progress_perc_str.set(self.current_progress_perc)

            self.elapsed_time = time.strftime('%H:%M:%S', time.gmtime(time.time() - self.footer_start_time))
            self.elapsed_time_str.set(self.elapsed_time)
            time.sleep(0.2)
        
        self.info_running = False
        logger.info(f'stopping footer info update loop')


    def start_update_info_loop(self):
        self.info_running = True
        self.info_interrupt = False
        threading.Thread(daemon=True,target=self._update_footer_info_loop,).start()

    def interrupt_info_loop(self):
        self.info_interrupt = True

    def reset_info(self):
        self.current_progress = '0 / 0'
        self.current_progress_perc = '0%'
        self.elapsed_time = '00:00:00'
        self.footer_start_time = ''
        self.results = "MESSAGE"

    def pb_setup(self):
        self.reset_info()
        self.parent.progress_bar_object.rest_all()
        if not self.firmware_path and not self.personality_path and not self.ble_path:
            return False
        
        file_size = 0
        if self.check_push_firm.get():
            file_size += os.stat(self.firmware_path).st_size
        if self.check_push_pers.get():
            file_size += os.stat(self.personality_path).st_size
        if self.check_push_BLE.get():
            file_size += os.stat(self.ble_path).st_size

        self.parent.progress_bar_object.total = file_size * len(self.parent.devices)
        #gui setup
        self.current_progress = f'{self.parent.progress_bar_object.progress} / {self.parent.progress_bar_object.total}'
        self.current_progress_str.set(self.current_progress)

    def set_selected_ports(self,ports):
        self.selected_comports = ports
        self.selected_comports_str.set(self.selected_comports)
        self.side_bar_selected_devices_label

    def display_results(self,parent_label,results,warplen:int = 55,align="top"):
    # Result[0] (string) = COM PORT
    # Result[1] (bool)= outcome
        for result in (results):
            if result[1] == True:
                color = '#217346'
            else:
                color = '#b40d1b'
            label = ctk.CTkLabel(parent_label,text=result[0],background=color,wraplength=warplen)
            label.pack(padx=5, pady=5,side=align)

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    Footer(root)
    root.mainloop()