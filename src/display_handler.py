import tkinter as tk
import time
import threading
import logging

logger = logging.getLogger(__name__)

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
        while self.is_running and not self.needs_interrupt:
            serialPortBuffer = device.listener.get_buffer()
            text_box.delete('1.0',tk.END)
            text_box.insert(tk.INSERT, device.serial_port_name)
            text_box.insert(tk.INSERT, serialPortBuffer)
            #label.see(tk.END)
            time.sleep(1)    