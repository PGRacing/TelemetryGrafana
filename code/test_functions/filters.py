import math


def get_alpha(period, cutoff_freq):
    return (2 * math.pi * cutoff_freq * period) / (2 * math.pi * cutoff_freq * period + 1)


def low_pass_filter(value, last_value, alpha):
    return alpha * value + (1 - alpha) * last_value


class FirFilter:
    def __init__(self, coefficients):
        self.coefficients = coefficients
        self.last_values = [0] * (len(coefficients) - 1)
        self.sum = 0

    def filter(self, value):
        self.sum = value * self.coefficients[0]
        for i in range(len(self.last_values)):
            self.sum += self.last_values[i] * self.coefficients[i + 1]
        self.last_values = [value] + self.last_values[:-1]
        return self.sum

    def get_last_value(self):
        return self.sum