#Python 2.7.6
#PrimaryAPI.py

import requests
import simplejson
from enum import Enum
import logging


logger = logging.getLogger(__name__)
proxies = {
  "http": None,
  "https": None,
}


class Entorno(Enum):
    sim = 1
    prod = 0

class Side(Enum):
    buy = "sell"
    sell = "buy"

class OrderType(Enum):
    limit = "limit"
    market = "market_to_limit"

# Endpoint
endpointProd = "https://api.primary.com.ar/"
endpointSim = "http://api.remarkets.primary.com.ar/"
# Endpoint WS
wsEndpointProd = "wss://api.primary.com.ar/"
wsEndpointSim = "ws://api.remarkets.primary.com.ar/"


# User y Password para la API - Utilizamos un objeto Session para loguearnos para que se mantega la cookie de sesion en las proximas llamadas
initialized = False
islogin = False
user = ""
password = ""
activeEndpoint = ""
activeWSEndpoint = ""
account = ""
token = ""
verifyHTTPs = None

s = requests.Session()
# Fix API Parameter
marketID='ROFX'
timeInForce='Day'

class PMYAPIException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def init(userParam, passwordParam, accountParam, entornoParam, verifyHTTPsParam=False):
    """
    REST submodule
    Initialization of variables
    """
    global user, password, account, activeEndpoint, initialized, activeWSEndpoint, verifyHTTPs
    user = userParam
    password = passwordParam
    account = accountParam
    verifyHTTPs = verifyHTTPsParam
    if entornoParam == 1:
        activeEndpoint = endpointSim
        activeWSEndpoint = wsEndpointSim
        verifyHTTPs = False
        initialized = True
    elif entornoParam == 0:
        activeEndpoint = endpointProd
        activeWSEndpoint = wsEndpointProd
        verifyHTTPs = True
        initialized = True
    else:
        print ("Entorno incorrecto")
        initialized = False

    
def login():
    """
    REST submodule
    Login to the api
    """
    #Validamos que se inicializaron los parametros 
    global initialized, activeEndpoint, islogin, token
    if not initialized: raise PMYAPIException("Parametros no inicializados.")
    if not islogin:
        url = activeEndpoint+"auth/getToken"
        headers = {'X-Username': user, 'X-Password': password}
        try:
            loginResponse = s.post(url, headers=headers, verify=False) 
            # Checkeamos si la respuesta del request fue correcta, un ok va a ser un response code 200 (OK)
            if(loginResponse.ok):
                token = loginResponse.headers['X-Auth-Token'];
                success = True
                logger.debug("Logging success. X-Auth-Token obtained correctly")
            else:   
                #print("\nRequest Error.",loginResponse)
                logger.debug("Request Error."+str(loginResponse))
                success = False
            islogin=success   
        except:
            logger.exception("Error in the logging process")
            success = False
    else:
        print ("Ya estamos logueados")
        success = True
    return success  

def requestAPI(url):
    """
    REST submodule
    function the perform a request
    """
    if(not login):
        raise PMYAPIException("Usuario no Autenticado.")
        logger.error("Usuario no Autenticado")
    else:
        global token
        headers = {'X-Auth-Token': token}
        r = requests.get(url, headers=headers, verify=verifyHTTPs, proxies=proxies)
        return r

def MD(ticker, entries,marketID="ROFX"):
    """
    REST submodule
    Get the real time information of an asset
    """
    url = activeEndpoint + "rest/marketdata/get?marketId={m}&symbol={s}&entries={e}".format(m=marketID,s=ticker,e=entries)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def md_historica(symbol, dateFrom, dateTo, marketId='ROFX',external=False):
    """
    REST submodule
    Get the historic information of an asset. ROFEX or External
    """
    if external:
        url = activeEndpoint + "rest/data/getTrades?marketId={mId}&symbol={s}&dateFrom={df}&dateTo={dt}&external=True"
    else:
        url = activeEndpoint + "rest/data/getTrades?marketId={mId}&symbol={s}&dateFrom={df}&dateTo={dt}"
    url = url.format(mId=marketId, s=symbol,df=dateFrom,dt=dateTo)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def segmentos():
    """
    REST submodule
    Get the list of segments
    """
    url = activeEndpoint + "rest/segment/all"
    r = requestAPI(url)
    return simplejson.loads(r.content)

def instrumentos():
    """
    REST submodule
    Get the list of all the insturments available in the market
    """
    url = activeEndpoint + "rest/instruments/all"
    r = requestAPI(url)
    return simplejson.loads(r.content)

def detilInstrument(symbol, marketId='ROFX'):
    """
    REST submodule
    Get the detailed information of an insturment
    """
    url = activeEndpoint + '/rest/instruments/detail?marketId='+ marketId + '&symbol=' + symbol
    r = requestAPI(url)
    return simplejson.loads(r.content)
    
def currencies():
    """
    REST submodule
    Get different currencies prices, mainly, usd dolars
    """
    url = activeEndpoint + "rest/risk/currency/getAll"
    r = requestAPI(url)
    return simplejson.loads(r.content)
        
def order_status(clOrdId, propritary):
    """
    REST submodule
    Check order status of an order sent
    """
    url = activeEndpoint + "rest/order/id?clOrdId={c}&proprietary={p}".format(c=clOrdId, p=propritary)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def enviar_Orden(ticker, price, cantidad, tipoOrden, side, account):
    """
    REST submodule
    Send an order sent to the market
    """
    if tipoOrden.upper() == 'MARKET':
        url = activeEndpoint + "rest/order/newSingleOrder?marketId={m}&symbol={s}&orderQty={q}&ordType={t}&side={si}&timeInForce={tf}&account={a}".format(m=marketID,s=ticker,q=cantidad,t=tipoOrden,si=side,tf=timeInForce,a=account)
    else:
        url = activeEndpoint + "rest/order/newSingleOrder?marketId={m}&symbol={s}&price={p}&orderQty={q}&ordType={t}&side={si}&timeInForce={tf}&account={a}".format(m=marketID,s=ticker,p=price,q=cantidad,t=tipoOrden,si=side,tf=timeInForce,a=account)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def cancelar_Orden(clOrderId, proprietary):
    """
    REST submodule
    Cancel an order sent to the market
    """
    url = activeEndpoint + "rest/order/cancelById?clOrdId={}&proprietary={}".format(clOrderId,proprietary)
    r = requestAPI(url)
    return simplejson.loads(r.content)
    
def cambiar_Orden(clOrderId,proprietary,new_qty,new_price):
    """
    REST submodule
    Change an order sent to the market
    """
    url = activeEndpoint + "rest/order/replaceById?clOrdId={}&proprietary={}&orderQty={}&price={}".format(clOrderId,proprietary,new_qty,new_price)
    r = requestAPI(url)
    return simplejson.loads(r.content) 

def getPositions():
    """
    RISK submodule
    Get positions for an account
    """
    url = activeEndpoint + "rest/risk/position/getPositions/{}".format(account)
    r = requestAPI(url)
    return simplejson.loads(r.content) 


def getDetailedPosition():
    """
    RISK submodule
    Get positions for an account
    """
    url = activeEndpoint + "rest/risk/detailedPosition/{}".format(account)
    r = requestAPI(url)
    return simplejson.loads(r.content) 
      
        
def getAccountReport():
    """
    RISK submodule
    Get positions for an account
    """
    url = activeEndpoint + "rest/risk/accountReport/{}".format(account)
    r = requestAPI(url)
    return simplejson.loads(r.content) 


if __name__ == "__main__":    
    # Inicializamos con usuario/password/cuenta
    init("salgozino898","oeofsZ2*","REM898",1)
    #init("50547","Algozin0!","50547",0)
    login()
    print("is logged?:", islogin)
    #print(instrumentos())
    print("Account report:",getAccountReport())
    print("Detailed Positions:",getDetailedPosition())

    print("Positions:",getPositions())