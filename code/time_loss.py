

class PointDetails:
    def __init__(self, x, y, timestamp) -> None:
        self.x = x
        self.y = y
        self.timestamp = timestamp


def recordFirstLap():
    firstPointTimestap = 0.
    isLapfinished = 0
