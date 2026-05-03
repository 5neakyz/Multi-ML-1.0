

def write_commands(self,commands:list):
    if self.serial_connection:
        logger.info(f'{self.serial_port_name}: Sending Command(s): {commands}')
        for command in commands:
            if command =="esc":
                command = (chr(27))     
            try:
                self.serial_port.write(command.encode())
            except Exception:
                logger.warning(f'{self.serial_port_name}: Failed Sending Commands')
                return False
        return True
    return False

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