from strategies.base import EstrategiaBase
from threading import Event
import logging

class FollowTheLeader(EstrategiaBase):
    """
    La idea de esta estrategua es que el usuario defina la tendencia (long / short) y el bot vaya actualizando el traillins stop en funcion de una perdida maxima permitida
    """
    
    def __init__(self,ws,account,stopping=Event(),ticker='RFX20Jun19',max_loss=50, db='remarkets.db'):
        super().__init__(ws,account,stopping, max_loss=max_loss, db=db)
        
        self.ticker_futuro = ticker
        self.ticker_spot= ''
        self.futuro_LA_price = 0.
        self.futuro_OF_price = 0.
        self.futuro_BI_price = 0.
        self.is_running = False
        self.update_current_prices()
        
        self.logger = logging.getLogger(__name__)
    
    def signal_maker(self):
        price = 0
        side = ''
        quantity = 0
        
        if not self.is_running:
            while side not in ["BUY","SELL","HOLD"]:
                try:
                    side = input('Ingrese BUY, SELL or HOLD: ')
                    if side != '':
                        side = str(side).upper()
                    if not((side == "BUY") or (side == "SELL")):
                        print('Opcion incorrecta, ingrese BUY, SELL o HOLD')
                    self.logger.info(f"Se eligio estar del lado: {side}")
                except KeyboardInterrupt:
                    side = 'HOLD'
                    break
                except EOFError:
                    side = "HOLD"
                    break
                except:
                    self.logger.exception("Exception rised when asked for the side.")
            
            if side != 'HOLD':
                self.update_current_prices()
                while quantity <= 0:
                    try:
                        quantity = float(input('Ingrese la cantidad que quiere operar: '))
                        if quantity <= 0:
                            print('La cantidad debe ser mayor a 0')
                        else:
                            self.logger.info(f"Se van a operar {quantity} unidades.")
                    except KeyboardInterrupt:
                        side = 'HOLD'
                        quantity = 0
                        self.logger.info("Cancelling the side selected due to user cancel")
                    except EOFError:
                        side = "HOLD"
                        break
                    except:
                        print('Error al ingresra la cantidad, asegurese de que ingreso un numero')
                        self.logger.exception("Exception rised when asked for the quantity.")
                
                while price == 0:
                    if not self.stopping.is_set():
                        if side == 'BUY':
                            price = self.futuro_BI_price+2
                        elif side == 'SELL':
                            price = self.futuro_OF_price-2
                        if price == 0:
                            try:
                                print("Waiting someone enqueue an order in the oposite side of we want")
                                self.update_current_prices()
                            except:
                                self.logger.exception("Exception waiting the price...")
                                side = "HOLD"
                                quantity = 0
                                price = 1
                    else:
                        self.logger.info("The user cancell the strategy")
                        side = "HOLD"
                        quantity = 0
                        price = 1
        else:
            side = 'HOLD'
        return quantity,side,price