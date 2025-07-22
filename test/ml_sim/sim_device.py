import time
import logging
from xmodem import XMODEM
from sim_serial_port_manager import SerialPortManger
import threading
from sim_listener import Listener

'''
Currently only implemented:
ESC - for main menu
3 - config
4- status - does have currentt date/time updates every second
6- download - no function as of yet
'''

class Device(SerialPortManger):
    def __init__(self,parent):
        super().__init__(parent)
        self.log = logging.getLogger('Device')
        self.log.info(f'{self.serial_port_name}: Creating Device Object')
        self.in_menu = False
        self.loop = False
        self.current_time = time.strftime("%D %T", time.localtime(time.time()))

        self.listener = Listener(self)
        self.listener.start_listening()

    def receiver(self,line,stop):
        self.log.info(f'{self.serial_port_name}: Receiving ')
        if b"\x1b" in line:
            self.in_menu = True
            self.loop = False
            self.write(self.main_menu_lines())

        if self.in_menu:
            self.in_menu = True
            if b'3' in line:
                self.write(self.config_screen_lines())
            if b'4' in line:
                self.loop = True
                threading.Thread(target=self.constant_write, args=(stop,)).start()
            if b'6' in line:
                self.write(self.download_screen_lines())

    def write(self,lines):
        self.log.info(f'{self.serial_port_name}: Writing ')
        for line in lines:
            try:
                self.serial_port.write(line)
            except Exception:
                return False
        return True

    def constant_write(self,stop):
        self.log.info(f'{self.serial_port_name}: entering write loop ')
        while self.loop:
            self.write(self.status_screen_lines(time.strftime("%D %T", time.localtime(time.time()))))
            if stop():
                break
            time.sleep(1)

    def main_menu_lines(self):
        return [
                    b'\x1b[2J\r\t\t\tMain Menu\r\r\n',
        b'\r\n',
        b'\n',
        b'\t\t  1 - Debugs\r\n',
        b'\t\t  2 - Logs\r\n',
        b'\t\t  3 - View Config\r\n',
        b'\t\t  4 - Status Screen\r\n',
        b'\t\t  5 - Configure\r\n',
        b'\t\t  6 - Download\r\n',
        b'\t\t  7 - Telematic Event Data\r\n',
        b'\t\t  8 - Telematic Summary Data\r\n',
        b'\t\t  9 - Advanced Menu\r\n',
        b'\t\t  b - Performance Counters Screen\r\n',
        b'\t\t  c - Commissioning Menu\r\n',
        b'\t\t  f - Production Test Screen\r\n',
        b'\t\t  g - System Info Screen\r\n',
        b'\r\n',
        b'\r\n',
        b' Enter option >',
        ]

    def status_screen_lines(self,time):
        return [
        b'\x1b[2',
        b'J\r\t\t\tStatus Screen\r\n',
        b'\r\n',
        f'MTU4 Time\t:{time} \tUptime: 00:00:00\r\n'.encode(),
        b'IMEI\t\t: 1234567890\tTelit 864: 10.01.020\r\n',
        b'Ver\t\t:3.90.2\tcrc 0x96c0 size:545436\r\n',
        b'Sig Q\t\t:255 = 0 Percent \r\n',
        b'GPRS\t\t:Trying\r\n',
        b'IP\t\t:\r\n',
        b'IMSI\t\t:\r\n',
        b'ICCID\t\t:\r\n',
        b'SRVR\t\t:172.17.144.97\t\tNot Connected \t5432\r\n',
        b'Power Retain\t:7200\tSleep: 43200=0\tRe-try: 6 \r\n',
        b'VIN\t\t:                 \tDriverId :Unknown\r\n',
        b'VRN\t\t:               \r\n',
        b'\r\n',
        b'GPSVer\t\t:HW:00040007\tSW:7.03 (45969)\r\n',
        b'Latitude\t: 53.03206253\tPower\t\t:On (24.81v)\r\n',
        b'Longitude\t: -1.46555280\tIgnition\t:On\r\n',
        b"GPSFix\t\t:TRUE FC 25  \tCh1 'Camera'\t:Low\t(DPD)\r\n",
        b"Num Sats\t:8\t\tCh2 'Unknown'\t:High\t(DPU)\r\n",
        b"Speed\t\t:  0.275948\tCh3 'Unknown'\t:High\t(DPU)\r\n",
        b"Course\t\t:  0.000000\tCh4 'PTO'\t:High\t(DPU)\r\n",
        b'Distance\t:0000010301\tShut Down\t:7200s\r\n',
        b'GPS Antenna\t:0\t\tBatt Capacity\t:unknown (3.78v)\r\n',
        b'GPS err (fHacc)\t:6.30\t\tCharge State\t:Fault\r\n',
        b'GPS AvCNO\t:22.00\t\tBT name\t\t:MTU4-728670\r\n',
        b'GPS err (HDOP)\t:0.96\r\n',
        b'Commissioning field: \r\n',
        b'\r\n',
        ]

    def config_screen_lines(self):
        return [
        b'\x1b[2J\r\t\t\tCONFIG\r\n',
        b'\r\n',
        b'HostIP              172.17.168.157\r\n',
        b'HostPort            5432\r\n',
        b'APN                 microlise.lte1.gdsp\r\n',
        b'\r\n',
        b'PersonalityVer      SG14_NO_CAN_MICROLISE_STOCK_Rev_1\r\n',
        b'\r\n',
        b'CAN1Mode            Off\r\n',
        b'\r\n',
        b'DistanceSource      3\r\n',
        b'SpeedSource         1\r\n',
        b'\r\n',
        b'IgnitionOn          0 0\r\n',
        b'IgnitionOff         0 0\r\n',
        b'MovingAfterStopped  1.0 60 1.0\r\n',
        b'Stopped             1.0 60 1.0\r\n',
        b'WakeupMask          4\r\n',
        b'BLEMode             1 \r\n',
        b'\r\n',
        b'################### Metrics ###################\r\n',
        b'\r\n',
        b'ExcessiveIdle       0.1 180 0.15\r\n',
        b'ExcessiveSpeedD     96.56 10 1.0\r\n',
        b'HarshBrake         -14.0 0 13.9\r\n',
        b'HarshCorneringG     8.0 0.4 0.3\r\n',
        ]
    
    def download_screen_lines(self):
        return [
        b'\x1b[2J\x1b[2J\r\t\t\tDownload\r\r\n',
        b'\r\n',
        b'\n',
        b'Firmware or Config via 1K Xmodem:\r\n',
        ]


if __name__ == '__main__':

    #self.button.clicked.connect(self.copy_text)

    # format = "%(asctime)s: %(message)s"
    # logging.basicConfig(format=format, level=logging.INFO,
    #                     datefmt="%H:%M:%S")
    
    logger = logging.getLogger(__name__)
    logger_format = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.basicConfig(format = logger_format, level=logging.INFO)
    # Create handlers
    f_handler = logging.FileHandler('file.log')
    f_handler.setLevel(logging.INFO)
    f_handler.setFormatter(logging.Formatter(logger_format))
    # Add handlers to the logger
    logger.addHandler(f_handler)

    port = "COM3"
    logger.info(f'Starting ML simulator on: {port}')
    unit = Device(port)
    #threading.Thread(target=unit.constant_write,args=(False,)).start()
    time.sleep(60)
    unit.listener.interrupt()
    unit.disconnect()