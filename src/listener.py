import threading
import logging
import time

logger = logging.getLogger(__name__)

class Listener():
    def __init__(self,device:object):
        logger.info(f'{device.serial_port_name}: Creating Listener Object')
        self.device = device
        self.is_running = False
        self.needs_interrupt = False 
        self.buffer_txt = ""
        self.download_temp_interrupt = False

    def continue_read(self):
        logger.info(f'{self.device.serial_port_name}: continuing Listener')
        self.download_temp_interrupt = False        

    def pause_read(self):
        logger.info(f'{self.device.serial_port_name}: Pausing Listener')
        self.download_temp_interrupt = True  

    def get_buffer(self):
        return self.buffer_txt
    
    def interrupt(self):
        logger.info(f'{self.device.serial_port_name}: Interrupting Listener')
        self.needs_interrupt = True

    def start_listening(self):
        logger.info(f'{self.device.serial_port_name}: Starting Listener')
        threading.Thread(daemon=True,target=self.listening).start()

    def listening(self):
        self.is_running = True
        logger.info(f'{self.device.serial_port_name}: Thread Started, Listening')

        while self.is_running and not self.needs_interrupt:
            if self.download_temp_interrupt:
                time.sleep(0.5)
                continue

            line = self.device.serial_port.readline()
            if line:
                if b'\x1b' in line:
                    self.buffer_txt = ""
                    split = line.split(b'\x1b')
                    line = split[-1]
            stripped = line.replace(b'\r',b' ').replace(b'\x1b',b'').replace(b'[2J',b'').replace(b':',b': ')
            if stripped:
                self.buffer_txt += stripped.decode("utf-8",errors='replace')