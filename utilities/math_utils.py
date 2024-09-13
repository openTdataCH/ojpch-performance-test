"""Utility functions for math.

"""


def rnd(f: float, decimal_digits=6):
    """Round float number to the given decimal_digits."""
    return float(('{:.' + str(decimal_digits) + 'f}').format(f))

