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

        # layout
        self.pack(fill="x",side="bottom",padx=1,pady=1)

        # info frame
        self.footer_info_bar = ctk.CTkFrame(self,border_width=1,height=30)
        self.footer_info_bar.pack(side="right",padx=1,pady=1)
        
        self.elapsed_time_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.elapsed_time_str).pack(padx=10,pady=1,side="right")
        self.current_progress_perc_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_perc_str).pack(padx=10,pady=1,side="right")
        self.current_progress_label = ctk.CTkLabel(self.footer_info_bar,textvariable=self.current_progress_str).pack(padx=10,pady=1,side="right")

        self.footer_results_bar = ctk.CTkFrame(self,border_width=1,height=30)
        self.footer_results_bar.pack(side="left",fill="x",expand=True,padx=1,pady=1)

    def _update_footer_info_loop(self):
        self.footer_start_time = time.time()
        while self.info_running and not self.info_interrupt:
            self.current_progress = f'{self.parent.get_progress_bar_progress()}'
            self.current_progress_str.set(self.current_progress)

            self.current_progress_perc = self.parent.get_progress_bar_percentage()
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

    def set_selected_ports(self,ports):
        self.selected_comports = ports
        self.selected_comports_str.set(self.selected_comports)
        self.side_bar_selected_devices_label

    def display_results(self,results):
        for result in results:
            if result.get("result") == True:
                color = '#217346'
            else:
                color = '#b40d1b'
            label = ctk.CTkLabel(self.footer_results_bar,text=(f'{result.get("device")} - {result.get("message")}'),bg_color=color)
            label.pack(padx=5,side="left")
        # self.results = results       
        # self.results_str.set(self.results)

    def clear_results(self):
        for widget in self.footer_results_bar.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    Footer(root)
    root.mainloop()