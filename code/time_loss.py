from math import sqrt, pow, cos

approx_lon = 18.712
approx_lat = 54.178
lat_prev = 54.1784441
lon_prev = 18.7133100

conv_rate_lon = cos(approx_lat) * (40075000/360) # deg to met
conv_rate_lat = 111111.0

class TrackPoint:
    def __init__(self, x:float, y:float, timestamp, distance:float, ) -> None:
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
        self.delta = 0
        self.last_used_point = None
        self.best_lap = []
    
    def recordFirstLap(self, x:float, y:float, timestamp):
        current_point = TrackPoint(x, y, timestamp)
        self.best_lap.append(current_point)
    
    def calucate_gain_loss(self, x:float, y:float, timestamp):
        if self.last_used_point == None:
            self.delta = 0
        

    def calc_distance(self, current_x, current_y, current_timestamp):
        def dist(x1: float, y1: float, x2: float, y2: float) -> float:
            return sqrt(pow((x1 - x2)*conv_rate_lon, 2) + pow((y1 - y2)*conv_rate_lat, 2))
        current_point = TrackPoint(current_x, current_y, current_timestamp)
        # finding 3 nearest points
        for i in range (len(self.best_lap)):
            if i == 0:
                nearest_point = self.best_lap[i]
            elif i == 1:
                if dist(current_x, current_y, self.best_lap[0].x, self.best_lap[0].y) <\
                dist(current_x, current_y, self.best_lap[1].x, self.best_lap[1].y):
                    nearest_point = self.best_lap[0]
                    second_nearest_point = self.best_lap[1]
                else:
                    nearest_point = self.best_lap[1]
                    second_nearest_point = self.best_lap[0]
            elif i == 2:
                if dist(current_x, current_y, self.best_lap[2].x, self.best_lap[2].y) <\
                dist(current_x, current_y, nearest_point.x, nearest_point.y):
                    third_nearest_point = second_nearest_point
                    second_nearest_point = nearest_point
                    nearest_point = self.best_lap[2]
                elif dist(current_x, current_y, self.best_lap[2].x, self.best_lap[2].y) >\
                dist(current_x, current_y, second_nearest_point.x, second_nearest_point.y):
                    third_nearest_point = self.best_lap[2]
                else:
                    third_nearest_point = second_nearest_point
                    second_nearest_point = self.best_lap[2]
            else:
                if dist(current_x, current_y, self.best_lap[i].x, self.best_lap[i].y) <\
                dist(current_x, current_y, nearest_point.x, nearest_point.y):
                    third_nearest_point = second_nearest_point
                    second_nearest_point = nearest_point
                    nearest_point = self.best_lap[i]
                elif dist(current_x, current_y, self.best_lap[i].x, self.best_lap[i].y) <\
                dist(current_x, current_y, second_nearest_point.x, second_nearest_point.y):
                    third_nearest_point = second_nearest_point
                    second_nearest_point = self.best_lap[i]
                elif dist(current_x, current_y, self.best_lap[i].x, self.best_lap[i].y) <\
                dist(current_x, current_y, third_nearest_point.x, third_nearest_point.y):
                    third_nearest_point = self.best_lap[i]
        
        # lines equations
        def line1(x, y):
            equation = (y - nearest_point.y)*(second_nearest_point.x - nearest_point.x)-(second_nearest_point.y-nearest_point.y)*(x-nearest_point.x)
            A = (second_nearest_point.y - nearest_point.y) / (second_nearest_point.x - nearest_point.x)
            C = (0 - nearest_point.y)*(second_nearest_point.x - nearest_point.x)-(second_nearest_point.y-nearest_point.y)*(0-nearest_point.x)
            B = (equation - C - A*x)/y
            return equation, A, B, C
        def line2(x, y):
            equation = (y - nearest_point.y)*(third_nearest_point.x - nearest_point.x)-(third_nearest_point.y-nearest_point.y)*(x-nearest_point.x)
            A = (third_nearest_point.y - nearest_point.y) / (third_nearest_point.x - nearest_point.x)
            C = (0 - nearest_point.y)*(third_nearest_point.x - nearest_point.x)-(third_nearest_point.y-nearest_point.y)*(0-nearest_point.x)
            B = (equation - C - A*x)/y
            return equation, A, B, C
        
        eq1, A1, B1, C1 = line1(current_x, current_y)
        eq2, A2, B2, C2 = line2(current_x, current_y)

        # finding proper distance
        distance1 = abs(eq1)/sqrt(A1**2 + B1**2)
        distance2 = abs(eq2)/sqrt(A2**2 + B2**2)

        def perpendicular_line(A, x, y):
            a_new_line = A ** (-1)
            # Ax + By + C = 0
            # y = ax + b => b = y - ax
            b_new_line = y - A*x
            return a_new_line, b_new_line

        if distance1 < distance2:
            a1, b1 = perpendicular_line(A1, current_x, current_y)
            # fastest lap racing line
            a2 = A1/B1
            b2 = C1
            points = '1-2'
            lenght_best_lap = dist(nearest_point.x, nearest_point.y, second_nearest_point.x, second_nearest_point.y)
        else:
            a1, b1 = perpendicular_line(A2, current_x, current_y)
            # fastest lap racing line
            a2 = A2/B2
            b2 = C2
            points = '3-1'
            lenght_best_lap = dist(third_nearest_point.x, third_nearest_point.y, nearest_point.x, nearest_point.y)

        # finding intersection
        x_inter = (b2 - b1)/(a1 - a2)
        y_inter = a1*x_inter + b1

        lenght_closest_point = dist(nearest_point.x, nearest_point.y, x_inter, y_inter)

        if points == '1-2':
            alfa = (lenght_best_lap - lenght_closest_point)/lenght_best_lap
        else:
            alfa = lenght_closest_point/lenght_best_lap

        return alfa

        

        




