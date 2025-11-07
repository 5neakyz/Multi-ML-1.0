import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
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

        self.side_bar_run_btn  = ctk.CTkButton(self,state='disabled',text="Run",height=26,command=lambda: threading.Thread(daemon=True,target=self.place_holder_function_for_test).start())
        self.side_bar_run_btn.pack(fill="x",side="right",padx=3,pady=1)
        self.side_bar_connect_btn = ctk.CTkButton(self,height=26,textvariable=self.connect_btn_text_str,command=lambda: threading.Thread(daemon=True,target=self.connect_disconnect_btn).start())
        self.side_bar_connect_btn.pack(fill="x",side="right",padx=10,pady=1)
        self.side_bar_selected_devices_label =ctk.CTkLabel(self,text="Selected:").pack(side="left",padx=10,pady=1)
        self.side_bar_selected_devices_placeholder = ctk.CTkLabel(self,textvariable=self.selected_comports_str).pack(side="left",padx=10,pady=1)

    def place_holder_function_for_test(self):
        print("you called?")

    def connect_disconnect_btn(self):
        if self.connect_btn_text_str.get() == 'Connect':
            self.connect_btn_text_str.set('Disconnect')
            print(self.side_bar_connect_btn.cget("width"))
            #self.connect_btn_press()
        else:
            self.connect_btn_text_str.set('Connect')
            #self.disconnect_btn_press()

    def connect_btn_press(self):
        pass

    def disconnect_btn_press(self):
        pass

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
    ConnectBar(root)
    root.mainloop()