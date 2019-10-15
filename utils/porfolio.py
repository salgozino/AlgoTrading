import pandas as pd
import logging
from datetime import datetime
import utils.DBtools
import utils.PMY_REST as pmy
"""
Issues:
    Automate determination of the portfolio cash at init!

"""
class Porfolio():
    """
    Clase para administrar el portfolio.
    Para inicializarla, se necesita conocer la cantidad de cash disponible, y definir una perdida maxima admisible.
    """
    def __init__(self, user, password, account, entorno=1, yearly_rate_free_risk=0.,logger=None, db='remarkets.db'):
        self.porfolio = {}
        self.yearly_rate_free_risk = 0.50;
        self.historic_value = pd.DataFrame(columns=['date','PV'])
        self.cum_ret = 0
        self.avg_daily_ret = None
        self.std_daily_ret = None
        self.sharpe_ratio = None
        self.max_loss = 0  #Max loss 
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
        self.user = user
        self.password = password
        self.account = account
        self.entorno = entorno
        self.currentCash = 0.
        self.accountReport = {}
        
        #update current porfolio
        pmy.init(self.user,self.password,self.account,self.entorno)
        pmy.login()
        self.getAccountReport()
        self.getPorfolio()

    def getPorfolio(self):
        if pmy.islogin:
            response = pmy.getPositions()
            self.porfolio = response['positions']
        else:
            self.logger.error("You have to be logged to ask for Porfolio")
            
    def getAccountReport(self):
        if pmy.islogin:
            response = pmy.getAccountReport()
            self.accountReport = response['accountData']
            self.currentCash = response['accountData']['currentCash']
        else:
            self.logger.error("You have to be logged to ask for Porfolio")
                
    
    def add_cash(self,money):
        self.cash += money

    def buy_stock(self,ticker,price,quantity):
        if self.cash > quantity*price:
            if ticker in self.porfolio:
                self.porfolio[ticker]['quantity'] += quantity
                self.porfolio[ticker]['current_price'] = price
            else:
                self.porfolio[ticker] = {'quantity':quantity,'current_price':price}
            self.cash -= quantity*price
            self.compute_current_PV()
        else:
            self.logger.warning("Ups, you've not enough money to buy this stock!")
        

    def sell_stock(self,ticker,price, quantity):
        if ticker in self.porfolio:
            if self.porfolio[ticker]['quantity'] <= 0:
                print("Selling in short")
                self.buy_stock(ticker,price,-quantity)
            else:
                self.porfolio[ticker]['quantity'] -= quantity
                self.cash += price*quantity
        else:
            print("Selling in short")
            self.buy_stock(ticker,price,-quantity)
        self.compute_current_PV()

        
    def compute_sharpe_ratio(self):
        try:
            self.sharpe_ratio = (self.historic_value.PV.mean() - 
                                 (self.historic_value.PV.loc[0]*(1+self.yearly_rate_free_risk)**(1/254)-1))/self.historic_value.PV.std()
        except:
            self.sharpe_ratio = 1


    def remove_stock_from_porfolio(self,ticker):
        try:
            del self.porfolio[ticker]
        except KeyError:
            print("Stock {} not found in porfolio".format(ticker))


    def compute_current_PV(self):
        PV = 0
        #Sum the value of the stocks
        for ticker in self.porfolio:
            PV += self.porfolio[ticker]['quantity']*self.porfolio[ticker]['current_price']
        #sum the fresh cash
        PV += self.cash
        #datetime to track the porfolio value
        data = {'date':datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 'PV':PV}
        #save it
        self.historic_value = self.historic_value.append(data,ignore_index=True)
        self.compute_sharpe_ratio()
        #just logging
        self.logger.info("Current PV is: {} with SR:".format(PV,self.sharpe_ratio))
        
        

    def update_stocks_prices(self):
        "Read the current prices from the DataBase"
        for ticker in self.porfolio:
            try:
                self.porfolio[ticker]['current_price'] = utils.DBtools.read_last_price(ticker, db=self.db)
            except:
                self.logger.exception('Error trying to update the price from the DB')    
        self.compute_current_PV()
        

if __name__ == '__main__':

    p = Porfolio("salgozino898","oeofsZ2*","REM898",1)
    p.buy_stock(ticker='RFX20JUN19',price=45000,quantity=1)
    p.buy_stock(ticker='RFX20SEP19',price=50000,quantity=1)
    print(p.historic_value)
    print(p.porfolio)
    p.update_stocks_prices()
    print(p.historic_value)
    print(p.porfolio)
    p.sell_stock('RFX20JUN19',55000,1)
    print(p.historic_value)
    print(p.porfolio)
    p.sell_stock('RFX20JUN19',55000,1)
    print(p.historic_value)
    print(p.porfolio)
    p.buy_stock('RFX20JUN19',50000,1)
    print(p.historic_value)
    print(p.porfolio)
