from threading import Thread, Event
import logging
from utils.wsClass import WebSocketClass as WS
from utils.menu import ask_login_credentials


def run(user=None, password=None, account=None, entorno=None,db=None):
    try:
        logger = logging.getLogger(__name__)
        logger.debug("Hello!, please don't kill me")
        
        stopping = Event()
        if user is None:
            user, password, account, entorno,db = ask_login_credentials()
        
        ws = WS(user=user,account=account,entorno=entorno,password=password,
                db=db,stopping=stopping)
        
        # Subscribe to the OrderReport messages
        ws.subscribeOR()
        
        #Subscribe to MD
        entries = ["LA","BI","OF","SE","OI","TV","IV"]
        tickers = ["RFX20Jun19","RFX20Sep19","I.RFX20","RFXP 06/09 19","DOJun19","DOJul19","DOP 06/07 19"]
        ws.subscribeMD(entries=entries,tickers=tickers)
        
        
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.debug("Clossing the botMiron")
            stopping.set()
            try:
                if 'ws' in locals():
                    ws.delete()
            except:
                logger.exception("Error killing the bot...")
        logger.debug("You've killed me. I will revenge. Hasta la vista, baby.")
    except:
        logger.exception("Exception in the botMiron")
        
if __name__ == '__main__':
    from utils.createLogger import createLogger
    logger = createLogger()
    run()
