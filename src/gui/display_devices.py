import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
import math
from display_handler import DisplayHandler

logger = logging.getLogger(__name__)

class DisplayDevices(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.pack(fill="both")
        self.configure(border_width=1)
        # bug in custom tkinter that scroll bar is 200 by defualt
        self._scrollbar.configure(height=1)
        #scroll wheel
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)
        self.grid_columnconfigure((0,1),minsize=200,weight=1)
        self.grid_rowconfigure(0,minsize=200,weight=1)

    def populate_notebook(self):
        self.clear_child_in_frame(self)
        if self.master.display_handler:
            self.master.display_handler.interrupt()
        text_boxes = []
        for device in self.master.devices:
            text_box = ctk.CTkTextbox(self,border_width=1,height=400)
            text_box._x_scrollbar.configure(height=1)
            #text_box.pack(expand=True,fill="both")
            text_boxes.append(text_box)

        amount = math.ceil(len(self.master.devices) / 2)
        print(amount)
        #how many rows
        rows = []
        for x in range (amount):
            rows.append(x)
        self.grid_columnconfigure((0,1),minsize=400,weight=1)
        self.grid_rowconfigure(rows,minsize=200,weight=1)
        # auto populate grid with each device
        x = 0
        y = 0
        for box in text_boxes:
            box.grid(column=y,row=x,padx=1,pady=1,sticky="NESW")
            y += 1
            if y > 1:
                y = 0
                x += 1
            print(f'Y:{y} X:{x}')


        self.master.display_handler = DisplayHandler(text_boxes,self.master.devices)
        self.master.display_handler.start_handler()

    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()    

    def _bound_to_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if int(-1*(event.delta/120)) > 0: # +1 scroll up
            self._parent_canvas.yview("scroll",50, "units")
        else:
            self._parent_canvas.yview("scroll",-50, "units")

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    DisplayDevices(master=root)
    root.mainloop()