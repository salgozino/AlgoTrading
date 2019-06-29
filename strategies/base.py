import logging
from threading import Event
import simplejson
from time import sleep
from datetime import datetime
import utils.DBtools

class EstrategiaBase():
    def __init__(self, WS,account='', stopping=Event(), comision = 0.109/100, cash_available=100000, max_loss = 150,db='remarkets.db'):
        #Websocket and account data.
        self.account = account
        self.WS = WS
        self.db = db
        
        #Porfolio data.
        # A unified new class is better option to handle this variables.
        self.cash_available = cash_available
        self.trade_profit = 0.
        self.total_profit = 0.
        self.comision = comision
        
        #Thread stopping event
        self.stopping = stopping
        
        #Datos de la estrategia que estamos ejecutando
        self.is_running = False
        self.open_price = 0.
        self.trailing_stop = 0.
        self.quantity = 0
        self.side = ''
        self.max_loss = max_loss
        
        #Datos de la orden que estamos ejecutando.
        self.q_or = WS.q_or
        self.order_status = ''  #Current order_status
        self.clOrdId = ''   #Current orderID
        self.property = ''  #Current property of the order
        
        #Logger
        self.logger = logging.getLogger(__name__)

    def create_variables(self,variables):
        pass

    def update_current_prices(self):
        """
        
        Read the current prices from the database
        The info readed from the DB is a dict with the last, offer and bid data (and size, and other parameters)
        """
        if self.ticker_spot != '':
            spot_data = utils.DBtools.read_last_row(self.ticker_spot,db=self.db)
            if spot_data is not None:
                if 'LA_price' in spot_data:
                    self.spot_LA_price = spot_data['LA_price'] if spot_data['LA_price'] is not None else self.spot_LA_price
        if self.ticker_futuro != '':
            futuro_data = utils.DBtools.read_last_row(self.ticker_futuro,db=self.db)
            if futuro_data is not None:
                if 'LA_price' in futuro_data:
                    self.futuro_LA_price = futuro_data['LA_price'] if futuro_data['LA_price'] is not None else self.futuro_LA_price
                if 'BI_price' in futuro_data:
                    self.futuro_BI_price = futuro_data['BI_price'] if futuro_data['BI_price'] is not None else self.futuro_BI_price
                if 'OF_price' in futuro_data:
                    self.futuro_OF_price = futuro_data['OF_price'] if futuro_data['OF_price'] is not None else self.futuro_OF_price

    def get_order_status(self, max_timeout=30,confirmation_status = ['FILLED','REJECTED'], avoid_stopping = False):
        #The avoid_stopping is to avoid re cancel the order, due to the stopping event.
        init_time = datetime.now()
        timeout = max_timeout
        #Reinicio el order_status
        self.order_status = ''
        #Lo transformo a lista por si envio un string unico.
        confirmation_status = confirmation_status if isinstance(confirmation_status, list) else [confirmation_status]
        try:
            while self.order_status not in confirmation_status:
                if not self.q_or.empty():
                    #self.logger.debug("The strategy catch the new message in the order report!")
                    data = self.q_or.get()
                    or_msg = data['orderReport']
                    # if 'origclOrdId' in or_msg:
                        # origclOrdId = or_msg['clOrdId']
                    self.order_status = or_msg['status']
                    self.clOrdId = or_msg['clOrdId']
                    self.property = or_msg['proprietary']
                    self.logger.info("Order status: {}".format(self.order_status))
                if 'PENDING' in self.order_status:
                    pass
                elif self.order_status == 'CANCELLED':
                    self.clOrdId = ''
                    self.property = ''
                    break
                else:
                    timeout = max_timeout - (datetime.now()-init_time).seconds
                    if timeout<=0:
                        self.logger.info("TIMEOUT waiting to fill the order. I'm Cancelling the order")
                        print("TIMEOUT!, I'm cancelling the order")
                        self.cancel_order()
                        print("Order Status: {}".format(self.order_status))
                        break
                
                if not avoid_stopping:
                    if self.stopping.is_set():
                         if self.clOrdId != '':
                             self.logger.info("Order Status while loop cancelled by the user. Cancelling the order sent")
                             self.cancel_order()
                         else:
                             self.logger.info("Order Status while loop cancelled by the user")
                         break                         
        except:
            self.logger.error("Error in the get_order_status. The order and positions are cancelled")
            self.cancel_order()

            

    def place_order(self,price,side,quantity,ticker=''):
        ticker = self.ticker_futuro if ticker == '' else ticker
        self.WS.placeOrder(ticker=ticker, price=price, side=side, quantity=quantity)
        self.logger.info("An order of {} was sent for {} of {} at price {}".format(side, quantity, ticker, price))


    def cancel_order(self):
        self.logger.debug("The actual order_status is {}".format(self.order_status))
        if 'NEW' in self.order_status:
            cancelMsg = {"type":"co",
                "clientId":self.clOrdId,
                "proprietary":self.property}
            msg = simplejson.dumps(cancelMsg)
            self.WS.ws.send(msg)
            self.logger.info("Sending message to cancell the order {} of property {}".format(self.clOrdId, self.property))
            #Tuve que agregar que el queue este vacio, pq me llegan varios mensajes de cancelado, no se pq. Si el cancell es via matriz llega uno solo.
            while (self.order_status != 'CANCELLED') or not self.q_or.empty():
                self.get_order_status(avoid_stopping=True)
                if self.order_status == 'REJECTED':
                    self.logger.error("Error trying to cancell the order. The message sent was rejected")
                    break
            self.logger.info("The order {} was cancelled".format(self.clOrdId))
            self.clOrdId = ''
            self.property = ''
        else:
            self.logger.info("There is no order to cancell.")


    def get_opossite_side(self):
        if self.side == 'BUY':
            return 'SELL'
        elif self.side == 'SELL':
            return 'BUY'


    def close_position(self, timeout = 20):
        """
        method to close the current position.
        We need to specify the timeout in seconds, that we are aceptting to wait until the order is filled.
        If the timeout is small, we are more agressive, to close the current position.
        """
        if self.is_running:
            #Busco el lado opuesto al que tengo abierto
            new_side = self.get_opossite_side()
            self.update_current_prices()
            price = self.futuro_OF_price if new_side == 'BUY' else self.futuro_BI_price
            self.place_order(price,new_side,self.quantity)
            or_status = ''
            while or_status not in ["CANCELLED","FILLED"]:
                or_status = self.get_order_status(max_timeout=10)
                if or_status == 'CANCELLED':
                    self.update_current_prices()
                    price = self.futuro_OF_price if new_side == 'BUY' else self.futuro_BI_price
                    self.place_order(price,new_side,self.quantity)

            self.update_profit()
            self.logger.info("{} {} Position/s was closed at price {}".format(self.quantity, self.side, self.futuro_LA_price))
            self.logger.info("The profit of the trade was {}".format(self.trade_profit))
            self.is_running = False
            self.trailing_stop = 0.
            self.open_price = 0.
            self.side = ''
            self.quantity = 0.
            self.total_profit = self.total_profit + self.trade_profit
            self.logger.info("The profit since i'm running is: {}".format(self.total_profit))
            self.trade_profit = 0.
            self.property = ''
            self.clOrdId = ''
        else:
            self.logger.info("There is no position to close")

    def check_SL(self):
        if self.side == 'BUY':
            if self.futuro_LA_price < self.trailing_stop:
                self.logger.info("Trailling stop activated in the {} position at price {}").format(self.side, self.futuro_LA_price)
                self.close_position()
                print("Trailling Stop activated!")
        elif self.side == 'SELL':
            if self.futuro_LA_price > self.trailing_stop:
                self.logger.info("Trailling stop activated in the {} position at price {}".format(self.side, self.futuro_LA_price))
                self.close_position()
                print("Trailling Stop activated!")

    def update_trailling_stop(self):
        if self.trailing_stop == 0:
            self.trailing_stop = self.open_price - self.max_loss if self.side == "BUY" else self.open_price + self.max_loss
            self.logger.info("Trailling Stop Updated at level {}".format(self.trailing_stop))
            print("Trailling Stop Updated at level {}".format(self.trailing_stop))
        else:
            if self.side == 'BUY':
                if self.futuro_LA_price-self.max_loss > self.trailing_stop:
                    self.trailing_stop = self.futuro_LA_price - self.max_loss
                    self.logger.info("Trailling Stop Updated at level {}".format(self.trailing_stop))
                    print("Trailling Stop Updated at level {}".format(self.trailing_stop))
            elif self.side == 'SELL':
                if self.futuro_LA_price+self.max_loss < self.trailing_stop:
                    self.trailing_stop = self.futuro_LA_price + self.max_loss
                    self.logger.info("Trailling Stop Updated at level {}".format(self.trailing_stop))
                    print("Trailling Stop Updated at level {}".format(self.trailing_stop))

    def update_profit(self):
        if self.side == 'BUY':
            self.trade_profit = self.futuro_LA_price - self.open_price
        elif self.side == 'SELL':
            self.trade_profit = self.open_price - self.futuro_LA_price
        print("Current proffit: {}".format(self.trade_profit))

    def signal_maker(self):
        """
        Se debe generar una nueva clase con herencia de esta estrategia base. Y se debe agregar el metodo signal_maker, que genere las variables:
        quantity: integer
        side: string ("BUY", "HOLD" or "SELL")
        price: float
        """
        quantity = 0
        side = "HOLD"
        price = 0.
        return quantity, side, price

    def stop_strategy(self):
        cancelled = False
        if self.property != '':
            self.logger.info("Cancelling the order sent to the market")
            self.cancel_order()
            cancelled = True
        if self.is_running == True:
            self.logger.info("Closing my opening position at market price")
            self.close_position()
            self.is_running = False
            cancelled = True
        if not cancelled:
            self.logger.info("There was nothing to cancell")
        self.logger.info("The strategy was stopped succesfully")

    def check_price(self,side,price_operation,operational_factor=0.1):
        if side == "BUY":
            return price_operation>self.futuro_LA_price*(1-operational_factor)
        else:
            return price_operation<self.futuro_LA_price*(1+operational_factor)
        
    def position_manager(self,price,side,quantity):
        if self.is_running:
            if (side == 'HOLD') or (side == self.side):
                self.update_profit()
                self.update_trailling_stop()
                self.check_SL()
            elif side != self.side and self.is_running:
                # self.logger.info(f'The strategy said that we have to change the {self.side} position to {side}')
                if side != 'HOLD':
                    self.close_position()
        else:
            if side != 'HOLD':
                try:
                    pass_check = self.check_price(side,price)
                except:
                    pass_check = True
                    self.logger.exception("The bot is taking position without checking the price, due to an error in the check_price function")
                
                if pass_check:
                    print(f"INFO - I'm opening a new position of {side} at price {price}.")
                    self.place_order(price,side,quantity)
                    self.order_status = self.get_order_status(max_timeout=60)
                    if self.order_status == 'FILLED':
                        self.logger.info("Starting the Strategy!")
                        self.open_price = price
                        self.quantity = quantity
                        self.side = side
                        self.update_trailling_stop()
                        self.is_running = True
                        self.property = ''
                        self.clOrdId = ''
                    elif self.order_status == 'REJECTED':
                        self.property = ''
                        self.clOrdId = ''
                    elif self.order_status == 'CANCELLED':
                        self.property = ''
                        self.clOrdId = ''
                else:
                    self.logger.info("The price adopted did not pasas the check with the price {}.".format(price))

    def run(self):
        #Initialize the strategy
        self.logger.debug(f"Inicializando estrategia {self.__class__.__name__}")
        while not self.stopping.is_set():
            try:
                if self.WS.ws.sock.connected:
                    #Get strategy values
                    self.update_current_prices()

                    #Take strategy quantity, side and price.
                    quantity, side, price = self.signal_maker()
                    
                    #Agrego, mantengo o cierro posicion?
                    self.position_manager(price,side,quantity)
                    
                    #Duermo por 1 segundo, solo para testing
                    sleep(1)
            except KeyboardInterrupt:
                self.logger.debug("The Strategy was stopped by the user.")
                self.stopping.set()
            except:
                self.logger.exception("Exception running the strategy! Sleeping for 5 seconds, if this error continue, please close the BOT..")
                sleep(5)
            

        self.logger.debug("Estrategia was stopped by user. I'll be close all my opened positions.")
        self.stop_strategy()
        