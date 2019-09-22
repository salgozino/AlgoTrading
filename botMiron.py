from threading import Event
import logging
from utils.wsClass import WebSocketClass as WS
from utils.menu import ask_login_credentials

class botMiron():
    def __init__(self, stopping = Event(), logger = '', user=None, password=None, account=None, entorno=None,db=None):
        self.stopping = stopping
        self.user = user
        self.password = password
        self.account = account
        self.entorno = entorno
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.ws = None
        #self.run()
        
    def run(self):
        try:
            self.logger.debug("Hello!, please don't kill me")
            

            if self.user is None:
                self.user, self.password, self.account, self.entorno, self.db = ask_login_credentials()
            
            self.ws = WS(user=self.user,account=self.account,entorno=self.entorno,password=self.password,
                    db=self.db,stopping=self.stopping, export_to_db = True)
            
            if not self.stopping.is_set():
                # Subscribe to the OrderReport messages
                self.ws.subscribeOR()
                
                #Subscribe to MD
                entries = ["LA","BI","OF","SE","OI","TV","IV"]
                tickers = ["RFX20Sep19","RFX20Dic19","I.RFX20","RFXP 09/12 19","DOAgo19","DOSep19","DOP 08/09 19","AY24Sep19","AY24DSep19","OROSep19","WTISep19","MERV - XMEV - AY24 - CI","MERV - XMEV - AY24D - CI"]
                self.ws.subscribeMD(entries=entries,tickers=tickers)
    
            
            
            try:
                while not self.stopping.is_set():
                    pass
            except KeyboardInterrupt:
                self.logger.debug("Clossing the botMiron")
                self.stopping.set()
                try:
                    if self.ws is not None:
                        self.ws.delete()
                except:
                    self.logger.exception("Error killing the bot...")
            self.logger.info("You've killed me. I will revenge. Hasta la vista, baby.")
        except:
            self.logger.exception("Exception in the botMiron")
        
if __name__ == '__main__':
    from utils.createLogger import createLogger
    logger = createLogger()
    bot = botMiron()
    bot.run()
