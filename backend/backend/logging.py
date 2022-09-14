import logging
import os
import errno


def mkdir_logs_path(path):
    try:
        os.makedirs(path, exist_ok=True)
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as os_error:
            if not (os_error.errno == errno.EEXIST and os.path.isdir(path)):
                raise


class MakeFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=0):
        mkdir_logs_path(os.path.dirname(filename))
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
