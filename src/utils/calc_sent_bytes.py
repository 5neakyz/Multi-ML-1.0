import math
'''
XMODEM sends packets with payload of 1024
final packet will also be 1024 but contains filler info
I could not figure out how to drop the filler data so file size was rounded up to number divs by 1024
so progress bar would flow over total file size - annoyed me

takes file size and calc how many packets it needed and the value of the last packet
to then be used to update the progress bar with an accurate number

i feel theres an easier way, this feels too complex

need to look at how xmodem gens filler
should try checking for filler data appears in a row 

'''
class Calc_sent_bytes():
    
    packet:int = 0
    packets:int = 0
    
    last_packet_content_size:int = 0
    
    def setup(self,file_size:int):
        self.packet = 0
        self.packets = math.ceil(file_size / 1024)
        self.last_packet_content_size = 1024 - ((self.packets)*1024 - file_size)
        return
    
    def get_current_payload_size(self):#
        self.packet += 1
        if self.packet == self.packets:
            return self.last_packet_content_size
        return 1024