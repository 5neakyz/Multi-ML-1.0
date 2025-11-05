import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
import os
import sys
import threading
import logging
logger = logging.getLogger(__name__)

class MenuBar(tk.Menu):
    def __init__(self, parent,send_commands):
        tk.Menu.__init__(self, parent)
        self.send_commands = send_commands
        self.menu_bar = self

        self.menu_settings = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_file = tk.Menu(self.menu_bar)
        self.menu_help = tk.Menu(self.menu_bar)
        
        #self.menu_bar.add_cascade(menu=self.menu_file, label='File')
        self.menu_bar.add_cascade(menu=self.menu_settings, label='Settings')
        self.menu_bar.add_cascade(menu=self.menu_help, label='Help')
        
        self.menu_settings.add_command(label="9HY",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","h","y"],)).start())
        self.menu_settings.add_command(label="9IY",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","i","y"],)).start())
        self.menu_settings.add_command(label="9JY",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","j","y"],)).start())
        self.menu_settings.add_command(label="9KA",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","k","a"],)).start())
        self.menu_settings.add_command(label="9KB",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","k","b"],)).start())
        self.menu_settings.add_command(label="9L",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","9","l"],)).start())

        #self.menu_help.add_command(label="Help",command=lambda: HelpMenu(self))

        #self.menu_bar.add_command(label="esc: Main Menu",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc"],)).start())
        self.menu_bar.add_command(label="3: View Config",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","3"],)).start())
        self.menu_bar.add_command(label="4: Status Screen",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","4"],)).start())
        self.menu_bar.add_command(label="F: Prod TS",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","f"],)).start())
        self.menu_bar.add_command(label="G: Sys Info",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","g "],)).start())

    def close_window(self):
        self.destroy()

    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
if __name__ == "__main__":
    def send_commands(command):
        print(command)

    root = tk.Tk()
    root.geometry(f"{500}x{200}")
    root.config(menu = MenuBar(root,send_commands))
    root.mainloop()

