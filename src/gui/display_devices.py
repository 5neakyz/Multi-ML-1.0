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

class FixedDeviceDisplay(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        '''
        This works best for 4 devices or less
        '''
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.pack(fill="both")
        self.configure(border_width=1)
        self.grid_columnconfigure((0,1),minsize=200,weight=1)
        self.grid_rowconfigure(0,minsize=200,weight=1)


    def populate_display_frame(self):
        self.clear_child_in_frame(self)
        if self.parent.display_handler:
            self.parent.display_handler.interrupt()
        text_boxes = []

        for device in self.parent.devices:
            text_box = ctk.CTkTextbox(self,border_width=1,height=self.winfo_height()/2)
            text_box._x_scrollbar.configure(height=1)
            #text_box.pack(expand=True,fill="both")
            text_boxes.append(text_box)

        # auto populate grid with each device
        col = 0
        row = 0
        cols = []
        rows = []
        for box in text_boxes:
            cols.append(col)
            rows.append(row)
            box.grid(column=col,row=row,padx=1,pady=1,sticky="NESW")
            col += 1
            if col > 1:
                col = 0
                row += 1

        self.grid_columnconfigure(list(set(cols)),minsize=200,weight=1)
        self.grid_rowconfigure(list(set(rows)),minsize=200,weight=1)

        self.parent.display_handler = DisplayHandler(text_boxes,self.parent.devices)
        self.parent.display_handler.start_handler()

    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()    


class ScrollableDeviceDisplay(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.pack(fill="both")
        self.configure(border_width=1)
        # bug in custom tkinter that scroll bar is 200 by defualt
        self._scrollbar.configure(height=1)
        #scroll wheel
        # self.bind('<Enter>', self._bound_to_mousewheel)
        # self.bind('<Leave>', self._unbound_to_mousewheel)
        self._parent_canvas.bind('<Enter>', self._bound_to_mousewheel)
        self._parent_canvas.bind('<Leave>', self._unbound_to_mousewheel)
        self.grid_columnconfigure((0,1),minsize=200,weight=1)
        self.grid_rowconfigure(0,minsize=200,weight=1)


    def populate_display_frame(self):
        self.clear_child_in_frame(self)
        if self.parent.display_handler:
            self.parent.display_handler.interrupt()
        text_boxes = []

        for device in self.parent.devices:
            text_box = ctk.CTkTextbox(self,border_width=1,height=400)
            text_box._x_scrollbar.configure(height=1)
            #text_box.pack(expand=True,fill="both")
            text_boxes.append(text_box)

        # auto populate grid with each device
        col = 0
        row = 0
        cols = []
        rows = []
        for box in text_boxes:
            print(f'col:{col} row:{row}')
            cols.append(col)
            rows.append(row)
            box.grid(column=col,row=row,padx=1,pady=1,sticky="NESW")
            col += 1
            if col > 1:
                col = 0
                row += 1

        self.grid_columnconfigure(list(set(cols)),minsize=200,weight=1)
        self.grid_rowconfigure(list(set(rows)),minsize=200,weight=1)
        
        self.parent.display_handler = DisplayHandler(text_boxes,self.parent.devices)
        self.parent.display_handler.start_handler()

    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()    

    def _bound_to_mousewheel(self, event):
        print("BOUND MAIN")
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        print("UNBOUND MAIN")
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
    ScrollableDeviceDisplay(parent=root)
    root.mainloop()