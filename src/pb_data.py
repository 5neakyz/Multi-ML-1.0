import dataclasses

@dataclasses.dataclass
class pb_data():

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
        return f'{round(perc)}%'

if __name__ == '__main__':
    pb = pb_data()
    pb.total = 200
    for _ in range(100):
        pb.add_to_progress(3)
        print(pb.current_progress())
        print(pb.perc_current_progress())
