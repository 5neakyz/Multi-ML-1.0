import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
logger = logging.getLogger(__name__)

class Option_Selection(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.pack(fill="both")

        self.columnconfigure((1,2,3),weight=0)
        self.rowconfigure((1,2),weight=1)

        #check options values
        self.check_push_pers = ctk.IntVar()
        self.check_push_firm = ctk.IntVar()
        self.check_push_BLE = ctk.IntVar()

        self.check_1=ctk.CTkCheckBox(self, text="Push Firmware",variable=self.check_push_firm)
        self.check_2=ctk.CTkCheckBox(self, text="Push Personality",variable=self.check_push_pers)
        #self.check_4=ctk.CTkCheckBox(self.check_buttons, text="Push BLE",variable=self.check_push_BLE).grid(row=1,column=3,padx=1,pady=1,sticky="w")
                
        self.firmware_path = None
        self.personality_path = None
        self.ble_path = None
        self.firmware_path_str = ctk.StringVar(value=self.firmware_path)
        self.personality_path_str = ctk.StringVar(value=self.personality_path)
        self.ble_path_str = ctk.StringVar(value=self.ble_path)

        #create widgets
        self.select_firmware_btn  = ctk.CTkButton(self,text="Firmware",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("firm",)).start())
        self.select_personality_btn  = ctk.CTkButton(self,text="Personality",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("pers",)).start())
        #self.select_ble_btn  = ctk.CTkButton(self,text="BLE",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("ble",)).start())
        self.firmware_label = ctk.CTkLabel(self,textvariable=self.firmware_path_str)
        self.personality_label = ctk.CTkLabel(self,textvariable=self.personality_path_str)
        self.ble_label = ctk.CTkLabel(self,textvariable=self.ble_path_str)

        #place widgets
        self.check_1.grid(row=0,column=0,padx=1,pady=1,sticky="w")
        self.select_firmware_btn.grid(row=0,column=1,padx=2,pady=2)
        self.firmware_label.grid(row=0,column=2,padx=2,pady=2,sticky="w")

        self.check_2.grid(row=1,column=0,padx=1,pady=1,sticky="w")
        self.select_personality_btn.grid(row=1,column=1,padx=2,pady=2)
        self.personality_label.grid(row=1,column=2,padx=2,pady=2,sticky="w")
        #self.select_ble_btn.grid(row=3,column=1,padx=2,pady=2)
        #self.ble_label.grid(row=3,column=2,padx=2,pady=2,sticky="w")


    def get_path(self,type):
        path = fd.askopenfilename()
        head,tail = os.path.split(path)
        if type == "firm":
            self.firmware_path = path
            self.firmware_path_str.set(tail)
        if type == "pers":
            self.personality_path = path
            self.personality_path_str.set(tail)
        if type == "ble":
            self.ble_path = path
            self.ble_path_str.set(tail)
    
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    Option_Selection(master=root)
    root.mainloop()