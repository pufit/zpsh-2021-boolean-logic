import traceback
import sys


def get_traceback_string(exception):
    if hasattr(exception, '__traceback__'):
        tb_strings = traceback.format_tb(exception.__traceback__)
    else:
        tb_strings = traceback.format_exception(*sys.exc_info())
    return ''.join(tb_strings)


def format_exception(e, with_traceback=False):
    if hasattr(e, '__module__'):
        exc_string = u'{}.{}: {}'.format(e.__module__, e.__class__.__name__, e)
    else:
        exc_string = u'{}: {}'.format(e.__class__.__name__, e)

    if with_traceback:
        traceback_string = ':\n' + get_traceback_string(exception=e)
    else:
        traceback_string = ''

    return u'{}{}'.format(exc_string, traceback_string)


def get_middle(start, end):
    return (start + end) // 2


def get_center(start, end, size):
    middle = get_middle(start, end)
    return middle - size // 2, middle + size // 2


def get_dots(start, end, count):
    start, end = int(start), int(end)
    size = 2 * count - 1
    center_start, center_end = get_center(start, end, size)
    return list(range(center_start, center_end + 1, 2))
