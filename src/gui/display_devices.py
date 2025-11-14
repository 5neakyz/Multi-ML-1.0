import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import customtkinter as ctk
import time
import logging
import os
import threading
import math

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
            text_box = ctk.CTkTextbox(self,border_width=1,height=300)
            text_box._x_scrollbar.configure(height=1)
            #text_box.pack(expand=True,fill="both")
            text_boxes.append(text_box)

        amount = math.ceil(len(self.master.devices) / 2)
        print(amount)
        #how many rows
        rows = []
        for x in range (amount):
            rows.append(x)
        self.grid_columnconfigure((0,1),minsize=200,weight=1)
        self.grid_rowconfigure(rows,minsize=200,weight=1)
        # auto populate grid with each device
        x = 0
        y = 0
        for box in text_boxes:
            box.grid(column=x,row=y,padx=1,pady=1,sticky="NESW")
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


class DisplayHandler():
    def __init__(self,labels,devices):
        logger.info(f'Creating Handler')

        self.labels = labels
        self.devices = devices

        self.is_running = False
        self.needs_interrupt = False 

    def start_handler(self):
        self.is_running = True
        logger.info(f'Starting Handler')
        for device in self.devices:
            i = self.devices.index(device)
            label = self.labels[i]
            threading.Thread(target=self.handler, args=(label,device)).start()

    def interrupt(self):
        logger.info(f'Interrupting Handler')
        self.needs_interrupt = True

    def handler(self,text_box,device):
        logger.info(f'{device.serial_port_name}: Thread Started')
        tempbuffer = ""
        while self.is_running and not self.needs_interrupt:
            serialPortBuffer = device.listener.get_buffer()
            if serialPortBuffer != tempbuffer:
                text_box.delete('1.0',tk.END)
                text_box.insert(tk.INSERT, device.serial_port_name)
                text_box.insert(tk.INSERT, serialPortBuffer)
                tempbuffer = serialPortBuffer
            time.sleep(0.1)
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry(f"{500}x{200}")
    DisplayDevices(master=root)
    root.mainloop()