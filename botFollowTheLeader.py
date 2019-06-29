#!/usr/bin/python
# coding: utf-8
from threading import Thread, Event
import logging
from utils.wsClass import WebSocketClass as WS
from utils.menu import select_ticker, ask_login_credentials
from strategies.followtheleader import FollowTheLeader

def run(user=None, password=None, account=None, entorno=None,db=None):
    try:
        logger = logging.getLogger(__name__)
        logger.debug("Hello!, please don't kill me")
        stopping = Event()
        if user is None:
            user, password, account, entorno,db = ask_login_credentials()
        ticker, max_loss = select_ticker()
        
        ws = WS(user=user,account=account,entorno=entorno,password=password,
                db=db)
        
        #Subscribe to the OrderReport messages
        ws.subscribeOR()

        est = FollowTheLeader(ws,account=account,ticker=ticker,stopping=stopping, max_loss=max_loss, db=db)
        t_est = Thread(target=est.run,name='Estrategia')
        t_est.daemon = True
        t_est.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.debug("Clossing the main bot app")
            stopping.set()
            try:
                try:
                    t_est.join()
                except:
                    pass
                if 'ws' in locals():
                    ws.delete()
            except:
                logger.exception("Error killing the bot...")
        logger.debug("You've killed me. I will revenge. Hasta la vista, baby.")
    except:
        logger.exception("Exception in the botFTL")

if __name__ == '__main__':
    from utils.createLogger import createLogger
    logger = createLogger()
    run()
