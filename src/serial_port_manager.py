import serial.tools.list_ports
import serial
import logging

logger = logging.getLogger(__name__)

class SerialPortManger():
    def __init__(self,comport_name:str):
        self.serial_connection = False
        self.serial_port = None
        self.serial_port_name = comport_name
        self.serial_port_baud = 115200

        try:
            self.serial_port = serial.Serial(port = self.serial_port_name, baudrate=self.serial_port_baud, timeout=0.1,write_timeout=0.2)
            self.serial_connection = True
            logger.info(f'{self.serial_port_name}: Connection Established')
        except Exception:
            logger.info("CANNOT CONNECT")
            self.serial_connection=False

    def disconnect(self):
        logger.info(f'{self.serial_port_name}: Disconnected')
        self.serial_port.close()
        self.serial_connection = False