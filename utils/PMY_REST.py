#Python 2.7.6
#PrimaryAPI.py

import requests
import simplejson
from enum import Enum
import logging


import os
os.environ['no_proxy'] = '*' 
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
endpointSim = "http://pbcp-remarket.cloud.primary.com.ar/"
# Endpoint WS
wsEndpointProd = "wss://api.primary.com.ar/"
wsEndpointSim = "ws://pbcp-remarket.cloud.primary.com.ar/"

# User y Password para la API - Utilizamos un objeto Session para loguearnos para que se mantega la cookie de sesion en las proximas llamadas
initialized = False
islogin = False
user = ""
password = ""
activeEndpoint = ""
activeWSEndpoint = ""
account = ""
token = ""

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
    global user, password, account, activeEndpoint, initialized, activeWSEndpoint, verifyHTTPs
    user = userParam
    password = passwordParam
    account = accountParam
    verifyHTTPs = verifyHTTPsParam
    if entornoParam == 1:
        activeEndpoint = endpointSim
        activeWSEndpoint = wsEndpointSim
        verifyHTTPs = False
    elif entornoParam == 0:
        activeEndpoint = endpointProd
        activeWSEndpoint = wsEndpointProd
        verifyHTTPs = True
    else:
        print ("Entorno incorrecto")
    initialized = True

def requestAPI(url):
    if(not login):
        raise PMYAPIException("Usuario no Autenticado.")
        logger.error("Usuario no Autenticado")
    else:
        global token
        headers = {'X-Auth-Token': token}
        r = requests.get(url, headers=headers, verify=verifyHTTPs, proxies=proxies)
        return r

def md_historica(symbol, fechaini, fechafin):
    url = history_endpoint.format(s=symbol,fi=fechaini,ff=fechafin)
    r = requests.get(url, proxies=proxies)
    return simplejson.loads(r.content)
    
def md_historica_ohlc(symbol, fechaini, fechafin,horaini,horafin):
    url = historyOHLC_endpoint.format(s=symbol,fi=fechaini,ff=fechafin,hi=horaini,hf=horafin)
    print(url)
    r = requests.get(url, proxies=proxies)
    return simplejson.loads(r.content)
    
def segmentos():
    url = activeEndpoint + "rest/segment/all"
    r = requestAPI(url)
    return simplejson.loads(r.content)

def instrumentos():
    url = activeEndpoint + "rest/instruments/all"
    r = requestAPI(url)
    return simplejson.loads(r.content)

def MD(ticker, entries):
    url = activeEndpoint + "rest/marketdata/get?marketId={m}&symbol={s}&entries={e}".format(m=marketID,s=ticker,e=entries)
    r = requestAPI(url)
    return simplejson.loads(r.content)
    
def currencies():
    url = activeEndpoint + "rest/risk/currency/getAll"
    r = requestAPI(url)
    return simplejson.loads(r.content)
        
def order_status(clOrdId, propritary):
    url = activeEndpoint + "rest/order/id?clOrdId={c}&proprietary={p}".format(c=clOrdId, p=propritary)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def enviar_Orden(ticker, price, cantidad, tipoOrden, side, account):
    url = activeEndpoint + "rest/order/newSingleOrder?marketId={m}&symbol={s}&price={p}&orderQty={q}&ordType={t}&side={si}&timeInForce={tf}&account={a}".format(m=marketID,s=ticker,p=price,q=cantidad,t=tipoOrden,si=side,tf=timeInForce,a=account)
    r = requestAPI(url)
    return simplejson.loads(r.content)

def login():
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
                print("\nRequest Error.")
                logger.debug("Request Error.")
                logger.debug(loginResponse)
                success = False
            islogin=success   
        except:
            logger.exception("Error in the logging process")
            success = False
    else:
        print ("Ya estamos logueados")
        success = True
    return success        
        
if __name__ == "__main__":    
    # Inicializamos con usuario/password/cuenta
    init("user1","password","",Entorno.sim)
    login()
    print(instrumentos())

