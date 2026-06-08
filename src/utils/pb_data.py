import math
import dataclasses

@dataclasses.dataclass
class Pb_data():

    _progress: int = 0
    _total: int = 0
    
    def get_total(self) -> int:
        return self._total
    
    def set_total(self,total:int):
        self._total = total

    def get_progress(self) -> int:
        return self._progress

    def add_to_progress(self, value:int) -> int:
        self._progress += value
        return self._progress
    
    def current_progress(self) -> str: 
        return f'{self._progress}/{self._total}'
    
    def current_progress_as_percentage(self) -> str:
        if self._progress > self._total or self._total == 0:
                return f'100%'
        perc = self._progress/self._total * 100
        return f'{round(perc,1)}%'
    
    def reset_all(self):
        self._progress: int = 0
        self._total: int = 0
    