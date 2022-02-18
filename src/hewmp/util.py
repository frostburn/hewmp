from collections import defaultdict
import re
from scipy.interpolate import interp1d


class Splitter:
    def __init__(self, delimiters):
        self.delimiters = delimiters
        self.pattern = re.compile('(' + '|'.join(map(re.escape, delimiters)) + ')')

    def split(self, text):
        result = defaultdict(list)
        value = None
        for token in reversed(self.pattern.split(text)):
            if token in self.delimiters:
                result[token].append(value)
            else:
                value = token
        return value, result

    def __call__(self, text):
        return self.split(text)


def interp_lin_const(xs, ys):
    return interp1d(xs, ys, bounds_error=False, fill_value=(ys[0], ys[-1]))
