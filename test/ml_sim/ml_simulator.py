
import serial.tools.list_ports
import serial
from xmodem import XMODEM
import time
import os
import threading
import logging
import concurrent.futures

"""
basic (trash) simulator of an ML unit for testing purposes

COM 0 COM
virtual com connections between
home pc
COM3 - COM4

Sim - COM3 
Tera Term - COM4 

"""

class SerialPortManger():
    def __init__(self,comport_name):
        self.serial_connection = False
        self.serial_port = None
        self.serial_port_name = comport_name
        self.serial_port_baud = 115200

        try:
            self.serial_port = serial.Serial(port = self.serial_port_name, baudrate=self.serial_port_baud, timeout=0.05)
            self.serial_connection = True
            logging.info(f'{self.serial_port_name}: Connection Established')
        except Exception:
            logging.info("CANNOT CONNECT")
            self.serial_connection=False

    def disconnect(self):
        logging.info(f'{self.serial_port_name}: Disconnected')
        self.serial_port.close()

class Device(SerialPortManger):
    def __init__(self,parent):
        super().__init__(parent)
        logging.info(f'{self.serial_port_name}: Creating Device Object')
        #only creates listener if there is connection
        if self.serial_connection:
            self.listener = Listener(self)
            self.listener.start_listening()

    def is_alive (self):
        if self.serial_connection:
            for _ in range(1):
                self.write_commands(["esc"])
                time.sleep(0.5)
                x = self.listener.get_buffer()
                if "Main Menu" in str(x):
                    logging.info(f'{self.serial_port_name}: is Alive')
                    return True
        return False

    def erase_config(self):
        if self.serial_connection:
            for _ in range(5):
                if self.is_alive():
                    break
            else: return False
            self.write_commands(["esc","9","h","y"])
            time.sleep(0.5)
            return True
        return False

    def write_commands(self,commands):
        if self.serial_connection:
            logging.info(f'{self.serial_port_name}: Sending Command(s): {commands}')
            for command in (commands):
                if command =="esc":
                    command = (chr(27))
                command = "command"+command   
                try:
                    self.serial_port.write(command.encode())
                except Exception:
                    logging.info(f'{self.serial_port_name}: Failed Sending Commands')
                    return False
            return True
        return False

class Listener():
    def __init__(self,device):
        logging.info(f'{device.serial_port_name}: Creating Listener Object')
        self.device = device
        self.is_running = False
        self.needs_interrupt = False 
        self.buffer_txt = ""
        self.mainmenu = [b'[2J\r\t\t\tMain Menu\r\r\n',
                    b'\r\n',
                    b'\n',
                    b'1 - one \r\n',
                    b'2 - two\r\n',
                    b'3 - three\r\n',
                    b'4 - four\r\n',
                    b'5 - five\r\n',
                    b'6 - six\r\n',
                    b'7 - seven\r\n',
                    b'8 - eight\r\n',
                    b'9 - nine\r\n',
                    b'\n'
                    b'Enter >']

        self.status = [b'[2J\r\t\t\tMain Menu\r\r\n',
                    b'\r\n',
                    b'\n',
                    (f'TIME - {time.strftime("%D %T", time.localtime(time.time()))} \r\n').encode(),
                    b'2 - two\r\n',
                    b'3 - three\r\n',
                    b'4 - four\r\n',
                    b'5 - five\r\n',
                    b'6 - six\r\n',
                    b'7 - seven\r\n',
                    b'8 - eight\r\n',
                    b'9 - nine\r\n',
                    b'\n'
                    b'Enter >']
        
    def get_buffer(self):
        return self.buffer_txt
    
    def interrupt(self):
        logging.info(f'{self.device.serial_port_name}: Interrupting Listener')
        self.needs_interrupt = True

    def start_listening(self):
        logging.info(f'{self.device.serial_port_name}: Starting Listener')
        threading.Thread(target=self.listening).start()

    def listening(self):
        self.is_running = True
        logging.info(f'{self.device.serial_port_name}: Thread Started, Listening')

        while self.is_running and not self.needs_interrupt:
            lines = self.device.serial_port.readline()
            if lines:
                self.buffer_txt = lines
                logging.info(f'{self.device.serial_port_name} : {lines}')
                if b"\x1b" in (lines):
                    logging.info(f'{self.device.serial_port_name}: sending mainmeu')
                    for line in self.mainmenu:
                        try:
                            self.device.serial_port.write(line)
                        except Exception:
                            logging.info(f'{self.device.serial_port_name}: Failed Sending Commands')

                if b'4' in (lines):
                    logging.info(f'{self.device.serial_port_name}: sending status')

                    for _ in range (100):
                        if self.needs_interrupt:
                            break
                        try:
                            self.device.serial_port.write((f'TIME - {time.strftime("%D %T", time.localtime(time.time()))} \r\n').encode())
                        except Exception:
                            logging.info(f'{self.device.serial_port_name}: Failed Sending Commands')
                        time.sleep(1)
    
    def format_readlines(self,lines):
        output = ''

        for line in lines:
            text = line.strip().replace(b'\t', b'').replace(b'\n',b'').replace(b'\r',b'').replace(b'\x1b',b'').replace(b'\xfe',b'')
            try:
                output +=(text.decode('utf-8')+ ' \n')
            except Exception as e: print(e,text)

        return output

if __name__ == '__main__':

    #self.button.clicked.connect(self.copy_text)

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    
    port = "COM4"
    logging.info(f'Starting ML simulator on: {port}')
    unit = Device(port)
    unit.write_commands(["esc","4"])
    time.sleep(30)
    unit.listener.interrupt()
    unit.disconnect()
