import logging
from datetime import datetime
import os

def createLogger():
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