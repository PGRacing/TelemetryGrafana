import time
import json
from math import sqrt, pow
from typing import Tuple


class LapTimer:
    def __init__(
        self,
        x1: float = 18.712384,
        y1: float = 54.178948,
        x2: float = 18.712373,
        y2: float = 54.178809,
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

        self.time = 0.0
        self.last_time = 0.0
        self.best_time = 0.0

        self.lap_counter = -1
        self.last_x = 0.0
        self.last_y = 0.0

    def init_position(self, x: float, y: float) -> None:
        self.last_x = x
        self.last_y = y

    def check(self, x: float, y: float, timestamp: string) -> Tuple[float, float, float, int]:
        def dist(x1: float, y1: float, x2: float, y2: float) -> float:
            return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

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
            a1 + b1 <= c1 * 1.01
            and a1 + b1 >= c1 * 0.99
            and a2 + b2 <= c2 * 1.01
            and a2 + b2 >= c2 * 0.99
        ):
            self.last_time = timestamp - self.time
            self.time = timestamp
            if self.last_time < self.best_time or self.lap_counter == 0:
                self.best_time = self.last_time
            self.lap_counter += 1

        if self.lap_counter == 0:
            self.last_time = 0.

        self.last_x = x
        self.last_y = y

        return (self.time, self.last_time, self.best_time, self.lap_counter)