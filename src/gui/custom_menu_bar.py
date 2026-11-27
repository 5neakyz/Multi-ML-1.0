import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import os
import threading

from utils.custom_menu import Menu

class CustomMenuBar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # vars
        self.menu_bar = self
        self.parent = parent

        self.menu = Menu(self.menu_bar)

        #self.menu_file = self.menu.menu_bar(text="File", tearoff=0)
        self.settings= self.menu.menu_bar(text="Settings", tearoff=0)
        #self.menu_help = self.menu.menu_bar(text="Help", tearoff=0)
        self.commands = self.menu.menu_bar(text="Commands", tearoff=0)
            
        #self.settings.add_command(label="90")
        self.settings.add_command(label="Swap Theme",command=lambda: threading.Thread(daemon=True,target=parent.swap_theme).start())
        
        #commands
        self.menu.add_button(text="esc: Main Menu",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc"],)).start())
        self.menu.add_button(text="3: View Config",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","3"],)).start())
        self.menu.add_button(text="4: Status Screen",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","4"],)).start())
        self.menu.add_button(text="F: Prod TS",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","f"],)).start())
        self.menu.add_button(text="G: Sys Info",command=lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","g "],)).start())
        
        self.commands.add_command(label="9HY - Erase Config",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","h","y"],)).start())
        self.commands.add_command(label="9IY - Erase Reports",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","i","y"],)).start())
        self.commands.add_command(label="9JY - Erase DataStore",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","j","y"],)).start())
        self.commands.add_command(label="9KA - Erase Debugs(BlockStore)",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","k","a"],)).start())
        self.commands.add_command(label="9KB - Erase Debugs(Debugs)",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","k","b"],)).start())
        self.commands.add_command(label="9L - Immediate Reset",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","l"],)).start())
        self.commands.add_command(label="9Vy - Factory Reset",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","v","y"],)).start())
        self.commands.add_command(label="9dwbCtrl+a - Reset Bluetooth Name",command = lambda: threading.Thread(daemon=True,target=parent.send_commands,args=(["esc","9","d","w","b",chr(1)],)).start())

        #self.menu_help.add_command(label="Help",command=lambda: HelpMenu(self))

    def close_window(self):
        self.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    CustomMenuBar(master=root)
    root.mainloop()