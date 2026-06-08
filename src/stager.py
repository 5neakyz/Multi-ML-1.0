import concurrent.futures
import time
import logging

logger = logging.getLogger(__name__)

class Stager():
    '''
    if we are pushing either personality or firmware erase config
    to prevent unit from locking up if incompatible 
    Attributes:
    ------------
    devices: 
        list of device objects to stage
    progress_bar_object: 
        object reference to the progress bar to update during staging
    tasks:
        dict of tasks to perform with boolean values for each task
        (push_cert, push_firmware, push_personality, push_BLE, reset_BLE, clear_logs_9HY, clear_logs_9IY)
    paths:
        dict of file paths for each task that requires a file path
        (cert_path, firmware_path, personality_path, BLE_path)

    Methods:
    ------------
    start() -> None
        starts the staging process for all devices and returns a list of results with device name and success status

    '''
    def __init__(self,devices:list,progress_bar_object:object=None,tasks:dict=None,paths:dict=None):
        self.devices = devices

        self.tasks = tasks
        self.paths = paths

        self.progress_bar_object = progress_bar_object
    
    def _stage(self,device:object):
        
        if not self._is_tasks():
            return [device.serial_port_name,False,"no tasks selected"]
        
        if not self._is_paths():
            return [device.serial_port_name,False,"no paths selected"]
        
        if not self.progress_bar_object:
            return [device.serial_port_name,False,"no progress bar selected"]

        device.progress_bar_object = self.progress_bar_object   
        '''
        if we are pushing either personality or firmware eras config
        to prevent unit from locking up if incompatible 
        '''
        if self.tasks.get("push_cert"): # Push Cert
            logger.info(f"STAGER: Pushing Certificate")
            if not device.push(self.paths.get("cert_path")):
                return [device.serial_port_name,False]

        if self.tasks.get("push_firm") or self.tasks.get("push_pers"): # erase config
            logger.info(f"STAGER: Erasing Config")
            if not device.erase_config():
                return [device.serial_port_name,False]
            
        if self.tasks.get("push_firm"): # Push Firmware
            logger.info(f"STAGER: Pushing Firmware")
            if not device.push(self.paths.get("firmware_path")):
                return [device.serial_port_name,False]
            
        if self.tasks.get("push_pers"): # Push personality
            logger.info(f"STAGER: Pushing Personality")
            if not device.push(self.paths.get("personality_path")):
                return [device.serial_port_name,False]
                  
        if self.tasks.get("push_BLE"): # Push BLE
            logger.info(f"STAGER: Pushing BLE")
            if not device.push(self.paths.get("BLE_path")):
                return [device.serial_port_name,False]
            
        return [device.serial_port_name,True]
 
    def start(self):
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:# parallelism 
            tasks = [executor.submit(self._stage,device) for device in self.devices]
            for x in concurrent.futures.as_completed(tasks):
                results.append(x.result())
        return results
    

    def _is_tasks(self):
        if 1 in self.tasks.values() :
            return True
        return False
    
    def _is_paths(self):
        if any(isinstance(v, str) for v in self.paths.values()):
            return True
        return False