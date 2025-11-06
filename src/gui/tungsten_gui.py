import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext

import serial.tools.list_ports
import time
import os
import sys
import webbrowser
import threading
import logging
import concurrent.futures

#my classes
from ..device import Device
from gui.notebook_handler import NotebookHandler
from stager import Stager
from utils.pb_data import Pb_data
from gui.help_menu import HelpMenu
#247F4C

logger = logging.getLogger(__name__)

class TungstenGui(tk.Tk):
    def __init__(self):
        super().__init__()
        # configure window
        self.title("ML Multi Stager v2.1.0")
        self.geometry(f"{800}x{600}")

        #self.bind('<KeyPress>', self.onKeyPress)
        self.bind('<Double-1>',self.copy_on_double_click)

        #style
        self.option_add("*tearOff", False) # This is always a good idea
        #icon_path = self.resource_path("assests/MultiUnits.ico")
        #self.iconbitmap(icon_path)
        style_path = self.resource_path('../assests/Forest-ttk-theme-master/forest-dark.tcl')
        self.tk.call('source', style_path)
        ttk.Style().theme_use('forest-dark')
        s = ttk.Style()
        self.protocol("WM_DELETE_WINDOW",self.close_window)
        s.configure('red.TFrame', background='red')#2B2B2B
        s.configure('green.TFrame',background="green")
        s.configure('blue.TFrame',background="blue")


        ##vars
        self.raw_comports = serial.tools.list_ports.comports() # comports on pc
        self.comports = self.get_comport_names() #comport names
        self.list_box_items = tk.Variable(self,value=self.comports)#comport names as string for listbox
        self.selected_comports = [] # user selection
        self.selected_comports_str = tk.StringVar(value=self.selected_comports) # string list
        self.devices = []
        self.notebook_Handler = None
        self.connect_btn_text_str = tk.StringVar(value='Connect')
        self.help_doc = "assests/doc.html"
        #vars for info footer
        self.info_running = False
        self.info_interrupt = False
        self.progress_bar_object = None
        self.current_progress = '0 / 0'
        self.current_progress_str = tk.StringVar(value=self.current_progress)
        self.current_progress_perc = '0%'
        self.current_progress_perc_str = tk.StringVar(value=self.current_progress_perc)
        self.elapsed_time = '00:00:00'
        self.elapsed_time_str = tk.StringVar(value=self.elapsed_time)
        self.footer_start_time = ''
        
#frames / gui setup

# Menu Bar

        self.menu_bar = tk.Menu(self)

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

        self.menu_help.add_command(label="Help",command=lambda: HelpMenu(self))

        #self.menu_bar.add_command(label="esc: Main Menu",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc"],)).start())
        self.menu_bar.add_command(label="3: View Config",command = lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","3"],)).start())
        self.menu_bar.add_command(label="4: Status Screen",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","4"],)).start())
        self.menu_bar.add_command(label="F: Prod TS",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","f"],)).start())
        self.menu_bar.add_command(label="G: Sys Info",command=lambda: threading.Thread(daemon=True,target=self.send_commands,args=(["esc","g "],)).start())
        


        self.config(menu=self.menu_bar)
# Footer Info Bar
        self.footer_bar = ttk.Frame()
        self.footer_bar.pack(fill="x",side="bottom")

        self.stager_results_frame = ttk.Frame(self.footer_bar)
        self.stager_results_frame.pack(fill="x",side="left")

        self.info_frame = ttk.Frame(self.footer_bar)
        self.info_frame.pack(fill="x",side="right")

        self.elapsed_time_label = ttk.Label(self.info_frame,textvariable=self.elapsed_time_str).pack(padx=10,pady=10,side="right")
        self.current_progress_perc_label = ttk.Label(self.info_frame,textvariable=self.current_progress_perc_str).pack(padx=10,pady=10,side="right")
        self.current_progress_label = ttk.Label(self.info_frame,textvariable=self.current_progress_str).pack(padx=10,pady=10,side="right")

# Side bar

        self.side_bar = ttk.Frame()
        self.side_bar.pack(fill="y",side="left")
        #create widgets
        self.side_bar_run_btn  = ttk.Button(self.side_bar,state='disable',text="Run",command=lambda: threading.Thread(daemon=True,target=self.run_btn_press).start())
        self.side_bar_connect_btn = ttk.Button(self.side_bar,textvariable=self.connect_btn_text_str,command=lambda: threading.Thread(daemon=True,target=self.connect_disconnect_btn).start())
        self.side_bar_listbox = tk.Listbox(self.side_bar,listvariable=self.list_box_items,font=('',14),height=5,width=12)
        self.side_bar_selected_devices_frame= ttk.LabelFrame(self.side_bar,text="Selected Devices")
        self.side_bar_selected_devices_placeholder = ttk.Label(self.side_bar_selected_devices_frame,textvariable=self.selected_comports_str,wraplength=55)
        #functions on click listbox
        self.side_bar_listbox.bind('<<ListboxSelect>>', lambda event: self.items_selected(event))

        #create grid
        self.columnconfigure(1,weight=1)
        self.rowconfigure((1,2,3,4,5,6,7,8,9),weight=0)

        #place widgets
        self.side_bar_run_btn.grid(row=1,column=1,sticky="new",padx=20, pady=(20, 0))
        self.side_bar_connect_btn.grid(row=2,column=1,sticky="new",padx=20, pady=(20, 0))
        # list box
        self.side_bar_listbox.grid(row=4,column=1,sticky="nw",padx=20, pady=(20, 0))
        # alternate line colors
        try:
            for i in range(0,len(self.comports),2):
                self.side_bar_listbox.itemconfigure(i, background='#242424')
        except Exception as e: print(f'LIST BOX EXCEPTION{e}')

        self.side_bar_selected_devices_frame.grid(row=5,column=1,sticky="new",padx=20, pady=(20, 0))
        self.side_bar_selected_devices_placeholder.pack(padx=20,pady=20)

# Main

    # check buttons
        self.check_buttons = ttk.Frame()
        self.check_buttons.pack(fill="both")

        self.check_buttons.columnconfigure((1,2,3),weight=0)
        self.check_buttons.rowconfigure((1),weight=1)

        #check options values
        self.check_push_pers = tk.IntVar()
        self.check_push_firm = tk.IntVar()
        self.check_push_BLE = tk.IntVar()

        self.check_3=ttk.Checkbutton(self.check_buttons, text="Push Firmware",variable=self.check_push_firm).grid(row=1,column=1,padx=1,pady=1,sticky="w")
        self.check_2=ttk.Checkbutton(self.check_buttons, text="Push Personality",variable=self.check_push_pers).grid(row=1,column=2,padx=1,pady=1,sticky="w")
        self.check_4=ttk.Checkbutton(self.check_buttons, text="Push BLE",variable=self.check_push_BLE).grid(row=1,column=3,padx=1,pady=1,sticky="w")

    # file selection 
        self.file_selection = ttk.Frame()
        self.file_selection.pack(fill="both")
        #create grid on frame
        self.file_selection.columnconfigure((1,2),weight=0)
        self.file_selection.rowconfigure((1,2,3),weight=0)        

        #vars
        self.firmware_path = None
        self.personality_path = None
        self.ble_path = None
        self.firmware_path_str = tk.StringVar(value=self.firmware_path)
        self.personality_path_str = tk.StringVar(value=self.personality_path)
        self.ble_path_str = tk.StringVar(value=self.ble_path)

        #create widgets
        self.select_firmware_btn  = ttk.Button(self.file_selection,text="Firmware",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("firm",)).start())
        self.select_personality_btn  = ttk.Button(self.file_selection,text="Personality",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("pers",)).start())
        self.select_ble_btn  = ttk.Button(self.file_selection,text="BLE",command=lambda: threading.Thread(daemon=True,target=self.get_path,args=("ble",)).start())
        self.firmware_label = ttk.Label(self.file_selection,textvariable=self.firmware_path_str)
        self.personality_label = ttk.Label(self.file_selection,textvariable=self.personality_path_str)
        self.ble_label = ttk.Label(self.file_selection,textvariable=self.ble_path_str)

        #place widgets
        self.select_firmware_btn.grid(row=1,column=1,padx=2,pady=2)
        self.select_personality_btn.grid(row=2,column=1,padx=2,pady=2)
        self.select_ble_btn.grid(row=3,column=1,padx=2,pady=2)
        self.firmware_label.grid(row=1,column=2,padx=2,pady=2,sticky="w")
        self.personality_label.grid(row=2,column=2,padx=2,pady=2,sticky="w")
        self.ble_label.grid(row=3,column=2,padx=2,pady=2,sticky="w")
    #display tabs
        self.tab_view = ttk.Notebook()
        self.tab_view.pack(fill="both",expand=True,padx=5,pady=5)

        self.new_pad = ttk.Frame(self.tab_view)

        self.tab_view.add(self.new_pad,text="Tab 1")


        self.mainloop()

    def populate_notebook(self):
        self.clear_child_in_frame(self.tab_view)
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        labels = []
        for device in self.devices:
            pad = ttk.Frame(self.tab_view)
            self.tab_view.add(pad,text=device.serial_port_name)
            label = tk.Text(pad)
            label.pack(expand=True,fill="both")
            labels.append(label)

        self.notebook_Handler = NotebookHandler(labels,self.devices)
        self.notebook_Handler.start_handler()

    def run_btn_press(self):
        #button setup
        self.side_bar_run_btn.configure(state="disable")
        #footer loop / info setup
        self.info_running = True
        self.info_interrupt = False
        self.footer_start_time = time.time()
        self.clear_child_in_frame(self.stager_results_frame)
        self.pb_setup()
        threading.Thread(daemon=True,target=self.update_footer_info_loop).start()
        #stager setup
        stager_thread = Stager(self.devices)
        #tasks(pers , firm , BLE)
        stager_thread.tasks  = [self.check_push_firm.get(),self.check_push_pers.get(),self.check_push_BLE.get()]
        stager_thread.progress_bar_object = self.progress_bar_object
        stager_thread.firmware_path = self.firmware_path
        stager_thread.personality_path = self.personality_path
        stager_thread.BLE_path = self.ble_path
        # start stager
        results = stager_thread.start()
        logger.info(results)
        self.display_results(self.stager_results_frame,results,warplen=400,align="left")
        self.info_running = False
        self.side_bar_run_btn.configure(state="enable")

    def pb_setup(self):
        if not self.firmware_path and not self.personality_path and not self.ble_path:
            return False
        
        self.progress_bar_object = Pb_data()
        file_size = 0
        if self.check_push_firm.get():
            file_size += os.stat(self.firmware_path).st_size
        if self.check_push_pers.get():
            file_size += os.stat(self.personality_path).st_size
        if self.check_push_BLE.get():
            file_size += os.stat(self.ble_path).st_size

        self.progress_bar_object.total = file_size * len(self.devices)
        #gui setup
        self.current_progress = f'{self.progress_bar_object.progress} / {self.progress_bar_object.total}'
        self.current_progress_str.set(self.current_progress)
        
    def update_footer_info_loop(self):
        while self.info_running and not self.info_interrupt:
            self.current_progress = f'{self.progress_bar_object.progress} / {self.progress_bar_object.total}'
            self.current_progress_str.set(self.current_progress)

            self.current_progress_perc = self.progress_bar_object.perc_current_progress()
            self.current_progress_perc_str.set(self.current_progress_perc)

            self.elapsed_time = time.strftime('%H:%M:%S', time.gmtime(time.time() - self.footer_start_time))
            self.elapsed_time_str.set(self.elapsed_time)
            time.sleep(0.2)
        logger.info(f'stopping footer info update loop')

    def connect_disconnect_btn(self):
        if self.connect_btn_text_str.get() == 'Connect':
            self.connect_btn_text_str.set('Disconnect')
            self.connect_btn_press()
        else:
            self.connect_btn_text_str.set('Connect')
            self.disconnect_btn_press()

    def connect_btn_press(self):
        self.side_bar_connect_btn.configure(state='disable')
        logger.info(f'Connecting : {self.selected_comports}')
        #change frame text 
        self.side_bar_selected_devices_frame.configure(text="Connecting")
        #remove all in selected devices frame
        self.clear_child_in_frame(self.side_bar_selected_devices_frame)
        #ensures no duplicates of already existing objects, has no function on first use
        temp_devices_list = []
        for device in self.devices:
            temp_devices_list.append(device.serial_port_name)
        #creates device objects for devices that dont already exist
        for device in self.selected_comports:
            if device not in temp_devices_list:
                self.devices.append(Device(device))
        #create threadpool for all devices threadpool(function , devices)
        results = self.create_threadpool(self.is_connection_live,self.devices)
        #display results
        self.display_results(self.side_bar_selected_devices_frame,results)

        #insert logic for buttons
        if all(result[1] for result in results):
            self.side_bar_run_btn.configure(state='enable')

        #reset frame text
        self.side_bar_selected_devices_frame.configure(text="Selected Devices")
        self.side_bar_connect_btn.configure(state='enable')
        #notebook
        self.populate_notebook()

    def disconnect_btn_press(self):
        self.clear_child_in_frame(self.side_bar_selected_devices_frame)
        self.side_bar_run_btn.configure(state='disable')
        # safely disconnect current units
        for device in self.devices:
            device.listener.interrupt()
            device.disconnect()
            logger.info(f'{device.serial_port_name} TEXT BOX UPDATE READ {device.listener.needs_interrupt,device.serial_connection}')
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        #resets all comport variables and re-searches for any new comports
        self.raw_comports = serial.tools.list_ports.comports() # comports on pc
        self.comports = self.get_comport_names() #comport names
        self.list_box_items.set(self.comports)
        self.devices = []
        #
        self.clear_child_in_frame(self.tab_view)
        #needs placeholder
        self.side_bar_selected_devices_placeholder = ttk.Label(self.side_bar_selected_devices_frame,textvariable=self.selected_comports_str,wraplength=55)
        self.side_bar_selected_devices_placeholder.pack(padx=20,pady=20)

    def create_threadpool(self,function,items:list) ->list:
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:# parallelism 
            tasks = [executor.submit(function,item) for item in items]
            for x in concurrent.futures.as_completed(tasks):
                results.append(x.result())
        return results

    def display_results(self,parent_label,results,warplen:int = 55,align="top"):
    # Result[0] (string) = COM PORT
    # Result[1] (bool)= outcome
        for result in (results):
            if result[1] == True:
                color = '#217346'
            else:
                color = '#b40d1b'
            label = ttk.Label(parent_label,text=result[0],background=color,wraplength=warplen)
            label.pack(padx=5, pady=5,side=align)

    def clear_child_in_frame(self,*frames):
        for frame in frames:
            for widgets in frame.winfo_children():
                widgets.destroy()

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
        
    def items_selected(self,event):
        try:
            selected_item = event.widget.get(self.side_bar_listbox.curselection()[0])
            logger.info(f'Selected: {selected_item}')
            if selected_item in self.selected_comports:
                (self.selected_comports.remove(selected_item))
            else:
                (self.selected_comports.append(selected_item))
            self.selected_comports_str.set(self.selected_comports)
        except Exception as e: print(e)

    def resource_path(self,relative_path) -> str:
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def get_comport_names(self)-> list:
        comport_list = []
        for item in self.raw_comports:
            comport_list.append(item.device)
        return self.sort_comports(comport_list)
    
    def sort_comports(self,list):
        sorted_list = []
        for comport in list:
            comport = comport.replace("COM","")
            try:
                sorted_list.append(int(comport))
            except:
                sorted_list.append(comport)

        sorted_list.sort()
        list = []
        
        for item in sorted_list:
            item =f"COM{item}"
            list.append(item)
        return list

    def onKeyPress(self,event):
        print(f'You pressed: {event.keysym}')

    def copy_on_double_click(self,event):
        try:
            field_value = event.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()  # clear clipboard contents
            self.clipboard_append(field_value)  # append new value to clipbaord
        except Exception:
            pass

    def is_connection_live(self,unit):
        return unit.serial_port_name,unit.is_alive()
    
    def send_commands(self,commands):
        for device in self.devices:
            device.write_commands(commands)

    def close_window(self):
        for device in self.devices:
            try:
                device.listener.interrupt()
                device.disconnect()
            except Exception as e: print(e)
        if self.notebook_Handler:
            self.notebook_Handler.interrupt()
        self.info_interrupt = True
        self.devices.clear()
        self.destroy()
        logger.info(f'Safely closed')

if __name__ == "__main__":
    format = "%(asctime)s.%(msecs)04d - %(message)s"
    logging.basicConfig(format=format,level=logging.INFO,datefmt="%H:%M:%S")
    TungstenGui()
