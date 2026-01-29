import concurrent.futures
import time
import logging

logger = logging.getLogger(__name__)

class Stager():
    '''
    if we are pushing either personality or firmware erase config
    to prevent unit from locking up if incompatible 

    tasks[0] - Push Personality

    tasks[1] - Push Firmware

    tasks[2] - Push BLE

    '''
    def __init__(self,devices:list,progress_bar_object:object=None,personality_path:str=None,firmware_path:str=None,BLE_path:str=None,tasks:list=[0,0,0],):
        self.devices = devices

        self.personality_path = personality_path
        self.firmware_path = firmware_path
        self.BLE_path = BLE_path

        self.tasks = tasks
        '''
        tasks[0] - Push Personality
        tasks[1] - Push Firmware
        tasks[2] - Push BLE
        '''
        self.progress_bar_object = progress_bar_object
    
    def _stage(self,device:object):
        device.progress_bar_object = self.progress_bar_object   
        '''
        if we are pushing either personality or firmware eras config
        to prevent unit from locking up if incompatible 
        '''
        if self.tasks[0] or self.tasks[1]: # erase config
            logger.info(f"STAGER: Erasing Config")
            if not device.erase_config():
                return [device.serial_port_name,False]
            
        if self.tasks[0] : # Push Firmware
            logger.info(f"STAGER: Pushing Firmware")
            if not device.push(self.firmware_path):
                return [device.serial_port_name,False]
            
        if self.tasks[1]: # Push personality
            logger.info(f"STAGER: Pushing Personality")
            if not device.push(self.personality_path):
                return [device.serial_port_name,False]
                  
        if self.tasks[2]: # Push BLE
            logger.info(f"STAGER: Pushing BLE")
            if not device.push(self.BLE_path):
                return [device.serial_port_name,False]
            
        return [device.serial_port_name,True]
 
    def start(self):
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:# parallelism 
            tasks = [executor.submit(self._stage,device) for device in self.devices]
            for x in concurrent.futures.as_completed(tasks):
                results.append(x.result())
        return results