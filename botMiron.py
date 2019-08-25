from threading import Event
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
                db=db,stopping=stopping, export_to_db = True)
        
        if not stopping.is_set():
            # Subscribe to the OrderReport messages
            ws.subscribeOR()
            
            #Subscribe to MD
            entries = ["LA","BI","OF","SE","OI","TV","IV"]
            tickers = ["RFX20Sep19","RFX20Dic19","I.RFX20","RFXP 09/12 19","DOAgo19","DOSep19","DOP 08/09 19"]
            ws.subscribeMD(entries=entries,tickers=tickers)
        
        
        try:
            while not stopping.is_set():
                pass
        except KeyboardInterrupt:
            logger.debug("Clossing the botMiron")
            stopping.set()
            try:
                if 'ws' in locals():
                    ws.delete()
            except:
                logger.exception("Error killing the bot...")
        logger.info("You've killed me. I will revenge. Hasta la vista, baby.")
    except:
        logger.exception("Exception in the botMiron")
        
if __name__ == '__main__':
    from utils.createLogger import createLogger
    logger = createLogger()
    run()
