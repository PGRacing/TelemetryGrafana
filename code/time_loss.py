

class PointDetails:
    def __init__(self, x, y, timestamp) -> None:
        self.x = x
        self.y = y
        self.timestamp = timestamp

class TimeLoss:
    def __init__(self,
        x1: float = 18.713115,
        y1: float = 54.178896,
        ) -> None:
        self.current_x = 0
        self.current_y = 0
        self.current_timestamp = 0
        self.best_lap = []
    
    def recordFirstLap(x, y, timestamp):
        firstPointTimestap = 0.
        isLapfinished = 0
        self.best_lap





def calc_time_loss():
