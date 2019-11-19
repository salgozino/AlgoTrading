from threading import Event
import logging
from utils.wsClass import WebSocketClass as WS
from utils.menu import ask_login_credentials
import utils.PMY_REST as pmy

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

        
    def run(self):
        try:
            self.logger.debug("Hello!, please don't kill me")
            

            if self.user is None:
                self.user, self.password, self.account, self.entorno, self.db = ask_login_credentials()
            
            self.ws = WS(user=self.user,account=self.account,entorno=self.entorno,password=self.password,
                    db=self.db,stopping=self.stopping, export_to_db = True)
            pmy.init(userParam=self.user, passwordParam = self.password, accountParam=self.account, entornoParam=self.entorno, verifyHTTPsParam=True)
            pmy.login()
            valid_instruments = pmy.instrumentos()
            
            tickers = []
            instruments = ['RFX20', 'RFXP', 'GGAL', 'AY24', 'AO20', 'YPF', 'WTI', 'ORO']
            for inst in valid_instruments['instruments']:
                ticker = inst['instrumentId']['symbol']
                for s in instruments:
                    if s in ticker:
                        tickers.append(ticker)
            
            if not self.stopping.is_set():
                # Subscribe to the OrderReport messages
                self.ws.subscribeOR()
                
                #Subscribe to MD
                entries = ["LA","BI","OF","SE","OI","TV","IV"]
                #tickers = ["RFX20Dic19","RFX20Mar20","I.RFX20","RFXP 12/03 19","DOOct19","DONov19","DOP 10/11 19","AY24Dic19","ORONov19","WTINov19","GGALOct19",'MERV - XMEV - GGAL']
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
