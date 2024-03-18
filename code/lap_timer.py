import time
import json
from math import sqrt, pow
from typing import Tuple
from datetime import datetime
from dateutil import parser


class LapTimer:
    def __init__(
            self,
            x1: float = 18.713115,
            y1: float = 54.178896,
            x2: float = 18.713045,
            y2: float = 54.178709,
    ) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        if (
                self.x1 == -1.0
                or self.y1 == -1.0
                or self.x2 == -1.0
                or self.y2 == -1.0
        ):
            with open("Points.json") as read_file:
                data = json.load(read_file)
                self.x1 = data["finish"]["x1"]
                self.y1 = data["finish"]["y1"]
                self.x2 = data["finish"]["x2"]
                self.y2 = data["finish"]["y2"]

        self.last_time = 0.0
        self.best_time = 0.0
        self.last_lap_start = 0.
        self.lap_diff = 0
        self.lap_counter = 0
        self.last_x = 0.0
        self.last_y = 0.0
        self.best_lap = False

    def init_position(self, x: float, y: float, time: str) -> None:
        self.last_x = x
        self.last_y = y
        self.last_lap_start = parser.parse(time)

    def check(self, x: float, y: float, timestamp: str) -> Tuple[float, float, float, int]:
        def dist(x1: float, y1: float, x2: float, y2: float) -> float:
            return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

        self.lap_diff = 0
        self.best_lap = False

        cross_x = (
                          (self.x1 * self.y2 - self.y1 * self.x2) * (self.last_x - x)
                          - (self.x1 - self.x2) * (self.last_x * y - self.last_y * x)
                  ) / (
                          (self.x1 - self.x2) * (self.last_y - y)
                          - (self.y1 - self.y2) * (self.last_x - x)
                  )
        cross_y = (
                          (self.x1 * self.y2 - self.y1 * self.x2) * (self.last_y - y)
                          - (self.y1 - self.y2) * (self.last_x * y - self.last_y * x)
                  ) / (
                          (self.x1 - self.x2) * (self.last_y - y)
                          - (self.y1 - self.y2) * (self.last_x - x)
                  )

        a1 = dist(self.x1, self.y1, cross_x, cross_y)
        b1 = dist(self.x2, self.y2, cross_x, cross_y)
        c1 = dist(self.x1, self.y1, self.x2, self.y2)

        a2 = dist(self.last_x, self.last_y, cross_x, cross_y)
        b2 = dist(x, y, cross_x, cross_y)
        c2 = dist(self.last_x, self.last_y, x, y)

        if (
                c1 * 1.001 >= a1 + b1 >= c1 * 0.999
                and c2 * 1.001 >= a2 + b2 >= c2 * 0.999
        ):
            current_time = parser.parse(timestamp)
            if (current_time - self.last_lap_start).total_seconds() > 1.:
                self.last_time = (current_time - self.last_lap_start).total_seconds()
                self.last_lap_start = current_time
                self.lap_diff = 1
                self.lap_counter += 1

        current_time = parser.parse(timestamp)
        self.lap_duration_time = (current_time - self.last_lap_start).total_seconds()
        if self.lap_counter == 0:
            self.last_time = 0.

        self.last_x = x
        self.last_y = y

        return (self.last_time, self.lap_diff, self.lap_counter, self.lap_duration_time)
