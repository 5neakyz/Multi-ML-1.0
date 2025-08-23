import math
import dataclasses

@dataclasses.dataclass
class Pb_data():

    progress: int = 0
    total: int = 0
            
    def add_to_progress(self, value:int) -> int:
        self.progress += value
        return self.progress
    
    def current_progress(self) -> str: 
        return f'{self.progress}/{self.total}'
    
    def perc_current_progress(self) -> str:
        if self.progress > self.total:
                return f'100%'
        perc = self.progress/self.total * 100
        return f'{round(perc,1)}%'
    