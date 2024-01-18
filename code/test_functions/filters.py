import math


def get_alpha(period, cutoff_freq):
    return (2* math.pi * cutoff_freq * period) / (2* math.pi * cutoff_freq * period + 1)

def low_pass_filter(value, last_value, alpha):
    return alpha * value + (1 - alpha) * last_value


def fir_filter(value, last_values, coefficients):
    sum = value * coefficients[0]
    for i in range(len(last_values)):
        sum += last_values[i] * coefficients[i + 1]
    return sum
