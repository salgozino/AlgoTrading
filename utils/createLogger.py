import logging
from datetime import datetime
import os

def createLogger():
    """
    Function to create a logger that create a log file in the logs dir. The log
    filename gets the structure of "%Y-%m%d log.log".
    The log inside the file has a header with %asctime - name - levelname - message.
    Also, the same logs are printed in the console with a printout handler. In
    the filename and in the console, are printed message of debug and higger levels.
    
    If the logs folder is not found, is created.
    """
    logger = logging.getLogger()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create a file handler
    #create the dir for logs if not exist.
    if not os.path.exists('logs'):
        os.makedirs('logs')
    today = datetime.today().strftime('%Y-%m-%d')
    fh = logging.FileHandler('logs/' + today + ' log.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)

    # create Consolo # printout handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    return logger