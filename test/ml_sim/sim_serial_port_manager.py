import serial
import logging

logger = logging.getLogger('SerialPortManger')


class SerialPortManger():
    def __init__(self,comport_name):
        self.serial_connection = False
        self.serial_port = None
        self.serial_port_name = comport_name
        self.serial_port_baud = 115200
        self.connection_error = None

        try:
            self.serial_port = serial.Serial(port = self.serial_port_name, baudrate=self.serial_port_baud, timeout=0.1)
            self.serial_connection = True
            logger.info('%s: Connection Established', self.serial_port_name)
        except (serial.SerialException, OSError, ValueError) as error:
            self.connection_error = error
            logger.exception('%s: Cannot connect', self.serial_port_name)

    def disconnect(self):
        if self.serial_port is not None and self.serial_port.is_open:
            self.serial_port.close()
            logger.info('%s: Disconnected', self.serial_port_name)
        self.serial_connection = False
