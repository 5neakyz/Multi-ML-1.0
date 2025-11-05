import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk


import logging
logger = logging.getLogger(__name__)

class Footer(ctk.CTkFrame):
    def __init__(self, parent):
        ctk.CTkFrame.__init__(self, parent)
        # vars
        self.current_progress = '0 / 0'
        self.current_progress_str = ctk.StringVar(value=self.current_progress)
        self.current_progress_perc = '0%'
        self.current_progress_perc_str = ctk.StringVar(value=self.current_progress_perc)
        self.elapsed_time = '00:00:00'
        self.elapsed_time_str = ctk.StringVar(value=self.elapsed_time)
        self.footer_start_time = ''
        # layout
        self.footer_bar = self
        self.footer_bar.pack(fill="x",side="bottom")

        self.stager_results_frame = ctk.CTkFrame(self.footer_bar)
        self.stager_results_frame.pack(fill="x",side="left")

        self.info_frame = ctk.CTkFrame(self.footer_bar)
        self.info_frame.pack(fill="x",side="right")

        self.elapsed_time_label = ctk.CTkLabel(self.info_frame,textvariable=self.elapsed_time_str).pack(padx=10,pady=10,side="right")
        self.current_progress_perc_label = ctk.CTkLabel(self.info_frame,textvariable=self.current_progress_perc_str).pack(padx=10,pady=10,side="right")
        self.current_progress_label = ctk.CTkLabel(self.info_frame,textvariable=self.current_progress_str).pack(padx=10,pady=10,side="right")

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    Footer(root)
    root.mainloop()