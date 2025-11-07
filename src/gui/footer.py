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
        ctk.CTkFrame.__init__(self, parent)
        # vars
        self.parent = parent
        self.selected_comports = []
        self.selected_comports_str = ctk.StringVar(value=self.selected_comports) # string list
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
        self.connect_btn_text_str = ctk.StringVar(value='Connect')


        # layout
        self.footer_bar = self
        self.footer_bar.pack(fill="x",side="bottom",padx=1,pady=1)
        #buttons and connected frame
        self.footer_select_bar = ctk.CTkFrame(self.footer_bar,border_width=1,height=30)
        self.footer_select_bar.pack(fill="x",side="top",padx=1,pady=1)

        self.side_bar_run_btn  = ctk.CTkButton(self.footer_select_bar,state='disabled',text="Run",command=lambda: threading.Thread(daemon=True,target=self.place_holder_function_for_test).start())
        self.side_bar_run_btn.pack(fill="x",side="right",pady=1)
        self.side_bar_connect_btn = ctk.CTkButton(self.footer_select_bar,textvariable=self.connect_btn_text_str,command=lambda: threading.Thread(daemon=True,target=self.connect_disconnect_btn).start())
        self.side_bar_connect_btn.pack(fill="x",side="right",padx=10,pady=1)
        self.side_bar_selected_devices_label =ctk.CTkLabel(self.footer_select_bar,text="Selected:").pack(side="left",padx=10,pady=1)
        self.side_bar_selected_devices_placeholder = ctk.CTkLabel(self.footer_select_bar,textvariable=self.selected_comports_str).pack(side="left",padx=10,pady=1)


        # info frame
        self.footer_info_bar = ctk.CTkFrame(self.footer_bar,border_width=1,height=30)
        self.footer_info_bar.pack(fill="x",side="bottom")

        # bottom - footer
        # self.stager_results_frame = ctk.CTkFrame(self.footer_info_bar)
        # self.stager_results_frame.pack(fill="x",side="left")
        self.results_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.results_str).pack(padx=10,pady=1,side="left")
        # self.info_frame = ctk.CTkFrame(self.footer_info_bar)
        # self.info_frame.pack(fill="x",side="right")

        self.elapsed_time_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.elapsed_time_str).pack(padx=10,pady=1,side="right")
        self.current_progress_perc_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_perc_str).pack(padx=10,pady=1,side="right")
        self.current_progress_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_str).pack(padx=10,pady=1,side="right")

    def place_holder_function_for_test(self):
        print("you called?")

    def connect_disconnect_btn(self):
        if self.connect_btn_text_str.get() == 'Connect':
            self.connect_btn_text_str.set('Disconnect')
            #self.connect_btn_press()
        else:
            self.connect_btn_text_str.set('Connect')
            #self.disconnect_btn_press()

    def connect_btn_press(self):
        pass

    def disconnect_btn_press(self):
        pass

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

        self.progress_bar_object.total = file_size * len(self.parent.devices)
        #gui setup
        self.current_progress = f'{self.progress_bar_object.progress} / {self.progress_bar_object.total}'
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