import threading
import logging

class Listener():
    def __init__(self,device):
        self.device = device
        self.is_running = False
        self.needs_interrupt = False 
        self.stop_threads = False
        self.thread = None
        self.log = logging.getLogger('Listener')
        self.log.info(f'{device.serial_port_name}: Creating Listener Object')
    
    def interrupt(self):
        self.log.info(f'{self.device.serial_port_name}: Interrupting Listener')
        self.needs_interrupt = True
        self.stop_threads = True

    def start_listening(self):
        self.log.info(f'{self.device.serial_port_name}: Starting Listener')
        self.thread = threading.Thread(target=self.listening, daemon=True)
        self.thread.start()

    def join(self, timeout=None):
        if self.thread is not None:
            self.thread.join(timeout)

    def listening(self):
        self.is_running = True
        self.log.info(f'{self.device.serial_port_name}: Thread Started, Listening')

        while self.is_running and not self.needs_interrupt:
            line = self.device.serial_port.readline()
            if line:
                self.log.info(f'{self.device.serial_port_name}: {line}')
                self.device.record_serial_io("RX", line)
                self.device.receiver(line, lambda: self.stop_threads)

        self.is_running = False
