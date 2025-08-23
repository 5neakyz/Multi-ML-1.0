import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
import os
import sys

import logging
logger = logging.getLogger(__name__)

class HelpMenu(tk.Toplevel):
    def __init__(self,master=None):
        super().__init__(master=None)
        # configure window
        self.title("Helpful Info - ML Multi Stager v2.0.0")
        self.geometry(f"{800}x{600}")

        #style
        self.option_add("*tearOff", False) # This is always a good idea
        icon_path = self.resource_path("assests/myicon.ico")
        self.iconbitmap(icon_path)
        style_path = self.resource_path('assests/Forest-ttk-theme-master/forest-dark.tcl')
        #self.tk.call('source', style_path)
        ttk.Style().theme_use('forest-dark')
        s = ttk.Style()
        self.protocol("WM_DELETE_WINDOW",self.close_window)
        s.configure('red.TFrame', background='red')#2B2B2B
        s.configure('green.TFrame',background="green")
        s.configure('blue.TFrame',background="blue")
        s.configure('Header.TFrame',)

        self.header_text = 'ML Unit Multi Stager'
        self.p1 ='The Stager is a crudely put together Python Application. To be able to configure multiple ML units at once.'
        self.p2 = 'For connecting to a COM port and staging units you will get the results of the outcome in the following red / green format:'
        self.p3 = '- Success: Connection Established, Staged Successfully.'
        self.p4 = '- Failure: Cannot Establish Connection, Staging Failed.    '
        self.p5 ='For the Stager to successfully establish a connection with an ML unit, it must be able to read the main menu.\nSo, a connection failure may not necessarily be an indication of a faulty connection or lack of power, but a unit behaving erratically.'
        self.p6 = 'Baud rate is 115200\nFile Transfer Protocol is Xmodem1k'
        self.p7 = 'If you select to push either Firmware or Personality, The Stager will Erase Config before pushing anything.\nIf you are only pushing a BLE file it will Not Erase Config.\nThis is to prevent cases were the unit locks up as firmware and personality are not compatible.'
        self.p8 = 'The exact file size and the exact number of bytes sent may not precisely match, but it is still a good indication of progress.'

        self.header_text_str = tk.StringVar(value=self.header_text)
        self.p1_str = tk.StringVar(value=self.p1)
        self.p2_str = tk.StringVar(value=self.p2)
        self.p3_str = tk.StringVar(value=self.p3)
        self.p4_str = tk.StringVar(value=self.p4)
        self.p5_str = tk.StringVar(value=self.p5)
        self.p6_str = tk.StringVar(value=self.p6)
        self.p7_str = tk.StringVar(value=self.p7)
        self.p8_str = tk.StringVar(value=self.p8)
        

        self.header_lbl = ttk.Label(self,textvariable=self.header_text_str).pack(padx=10,pady=10,side='top',anchor="nw")
        self.p1_lbl = ttk.Label(self,textvariable=self.p1_str).pack(padx=10,pady=5,side='top',anchor="nw")
        self.p2_lbl = ttk.Label(self,textvariable=self.p2_str).pack(padx=10,pady=5,side='top',anchor="nw")

        self.pf_frame = ttk.Frame(self)
        self.pf_frame.pack(fill='x',side='top',anchor='nw',padx=10,pady=5)
        self.pf_frame.columnconfigure((1,2),weight=0)
        self.pf_frame.rowconfigure((1,2),weight=0)

        self.pass_lbl = ttk.Label(self.pf_frame,text=" COM ",background='#217346').grid(column=1,row=1,padx=5,pady=5)
        self.p3_lbl = ttk.Label(self.pf_frame,textvariable=self.p3_str).grid(column=2,row=1,padx=5,pady=5)
        self.fail_lbl = ttk.Label(self.pf_frame,text=" COM ",background='#b40d1b').grid(column=1,row=2,padx=5,pady=5)
        self.p4_lbl = ttk.Label(self.pf_frame,textvariable=self.p4_str).grid(column=2,row=2,padx=5,pady=5)

        self.p5_lbl = ttk.Label(self,textvariable=self.p5_str).pack(padx=10,pady=5,side='top',anchor="nw")
        self.p6_lbl = ttk.Label(self,textvariable=self.p6_str).pack(padx=10,pady=5,side='top',anchor="nw")
        self.p7_lbl = ttk.Label(self,textvariable=self.p7_str).pack(padx=10,pady=5,side='top',anchor="nw")
        self.p8_lbl = ttk.Label(self,textvariable=self.p8_str).pack(padx=10,pady=5,side='top',anchor="nw")

        self.mainloop()

    def close_window(self):
        self.destroy()

    def resource_path(self,relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
if __name__ == "__main__":
    HelpMenu()   