from strategies.base import EstrategiaBase
import utils.DBtools
from threading import Event
import logging

class ManualMode(EstrategiaBase):
    """
    La idea de esta estrategua es que el usuario defina la tendencia (long / short) y el bot vaya actualizando el traillins stop en funcion de una perdida maxima permitida
    """
    
    def __init__(self,WS,account,stopping=Event(),ticker='RFX20Sep19',max_loss=50, db='remarkets.db'):
        super().__init__(WS,account,stopping, max_loss=max_loss, db=db)
        
        self.ticker = ticker
        self.ticker_spot = ''
        self.futuro_LA_price = 0.
        self.futuro_OF_price = 0.
        self.futuro_BI_price = 0.
        self.is_running = True
        self.update_current_prices()
        self.logger = logging.getLogger(__name__)
    
    def signal_maker(self, price=0., side='', quantity=0.):
        price = 0
        side = ''
        quantity = 0
        return quantity,side,price

    def update_current_prices(self):
        """
        Read the current prices from the database
        The info readed from the DB is a dict with the last, offer and bid data (and size, and other parameters)
        """
        if self.ticker != '':
            futuro_data = utils.DBtools.read_last_row(self.ticker,db=self.db)
            if futuro_data is not None:
                if 'LA_price' in futuro_data:
                    self.futuro_LA_price = futuro_data['LA_price'] if futuro_data['LA_price'] is not None else self.futuro_LA_price
                if 'BI_price' in futuro_data:
                    self.futuro_BI_price = futuro_data['BI_price'] if futuro_data['BI_price'] is not None else self.futuro_BI_price
                if 'OF_price' in futuro_data:
                    self.futuro_OF_price = futuro_data['OF_price'] if futuro_data['OF_price'] is not None else self.futuro_OF_price
