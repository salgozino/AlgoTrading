import websocket
import logging
import simplejson
from threading import Event,Thread
from time import sleep
from datetime import datetime
from queue import Queue
import numpy as np
import utils.PMY_REST as pmy
import utils.DBtools
from collections import OrderedDict


class WebSocketClass():
    def __init__(self, user="user1", password="password", entorno=1, account='',
                 stopping=Event(), q_md = Queue(), q_or=Queue(), db='../remarkets.db', export_to_db = False):
        """
        Initialize the websocket connection, until a stopping event is activated.
        """
        self.q_md = q_md
        self.q_or = q_or
        self.logger = logging.getLogger(__name__)
        self.stopping = stopping
        self.user = user
        self.password = password
        self.entorno = entorno
        self.account = account
        self.db = db
        self.ws = None
        self.t_ws = None    #thread for the run_forever
        self.t_process = None #Thread for process the messages
        self.is_logged = False
        
        self.export_to_db = export_to_db
        #Initialize the Websocket thread and the process thread.
        self.start()

    def start(self):
        try:
            self.t_ws = Thread(target=self.createWS, name='WebSocket')
            self.t_ws.daemon = True
            self.t_ws.start()
        except:
            self.logger.error("Error initializing the thread with the websocket connection")
        
        while self.ws == None:
            if self.stopping.is_set():
                break
            else:
                print("Sleeping 1 sec...")
                sleep(1)
        if not self.stopping.is_set():
            conn_timeout = 5
            while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
                sleep(1)
                conn_timeout -= 1
            if not conn_timeout:
                self.logger.info("Could not connect to WS! Exiting.")
            
            if self.export_to_db:
                self.t_process = Thread(target=self.process, name='Process Messages')
                self.t_process.daemon = True
                self.logger.debug("Initializing the thread to process the Messages")
                self.t_process.start()
        
    def login(self):
        if not pmy.islogin:
            self.logger.debug("Logging to get the AUTH-TOKEN again")
            pmy.init(self.user,self.password,self.account,self.entorno)
            pmy.login()
            if pmy.islogin:
                self.logger.debug("Logged to primary")
            else:
                self.logger.error("You are not logged in. Check!")
        else:
            self.logger.debug("You are ALREADY logged in!")

    def __on_message(self, message):
        try:
            # self.logger.debug("A message was received!")
            msg = simplejson.loads(message)
            #self.logger.debug(msg)
            msgType = msg['type'].upper()
            if msgType == 'MD':
                try:
                    self.q_md.put(msg)
                except:
                    self.logger.exception("Exception trying to put MD msg in the queue")
                # # print("Msg sended to the MD queue")
            elif msgType == 'OR':
                #fmt = '%Y%m%d-%H:%M:%S.%f-0300'
                #transactTime = datetime.strptime(msg['orderReport']['transactTime'],fmt)
                #if  transactTime > (datetime.now()-timedelta(minutes=1)):
                try:
                    self.q_or.put(msg)
                except:
                    self.logger.exception("Exception trying to put OR msg in the queue")
                #else:
                #    self.logger.debug("OR not sended to the queue because is an older orderReport.")
                if msg['orderReport']['status']=='REJECTED':
                    self.logger.info("The order was rejected: {}".format(msg['orderReport']['text']))
            else:
                self.logger.debug("Error message received: {}".format(msg))
        except:
            msg = simplejson.loads(message)
            if 'status' in msg:
                self.logger.debug("An error message was received: {}".format(msg))
            else:
                self.logger.exception("Exception ocurred in the on_message websocket method. The msg was: {msg}".format(msg))

    def __on_error(self, error):
        self.logger.error(error)
        self.ws.close()

    def __on_close(self):
#        self.ws.close()
        self.logger.debug("WS cerrado.")
        pmy.islogin = False

    def __on_open(self):
        self.logger.debug("WS is open!")

    def createWS(self):
        """
        Create the websocket with the information (token, WSEndPoint) initialized in the Primary Module.
        """
        self.login()
        if pmy.token != '':
            websocket.enableTrace(True)
            headers = {'X-Auth-Token:{token}'.format(token=pmy.token)}
            self.ws = websocket.WebSocketApp(pmy.activeWSEndpoint,
                                       on_message=self.__on_message,
                                       on_close=self.__on_close,
                                       on_open=self.__on_open,
                                       on_error=self.__on_error,
                                       header=headers)
            self.ws.run_forever(ping_interval=295)
        else:
            self.logger.error("Empty token. Are you sure that the logging was correct?")
            self.stopping.set()

    def extract_features(self, msg):
        """
        take the message received from the API, and transform to a dict.
        """
        data = {}
        entries =[]
        col = 'orderReport' if msg['type'].upper() == "OR" else 'marketData'
        for entrie, value in msg[col].items():
            entries.append(entrie)
            if isinstance(value, list):
                if len(value)>0:
                    value = value[0]
                else:
                    value = np.nan
            try:
                for key,value in value.items():
                    if key == 'date':
                        value = datetime.fromtimestamp(value/1000)
                    
                    if value != None or np.isnan(value):
                        try:
                            isnan = np.isnan(value)
                        except:
                            isnan = False
                        if not isnan:
                            data['{}_{}'.format(entrie, key)]=value
            except:
                if value != None:
                    try:
                        isnan = np.isnan(value)
                    except:
                        isnan = False
                    if not isnan:
                        data[entrie]=value
        data['date'] = datetime.fromtimestamp(msg['timestamp']/1000)
        return data

    def process(self):
        """
        Function to process the messages from the queue, and add to the database.
        """
        try:
            while not self.stopping.is_set():
                r = None
                #primero me fijo sobre el q_or para procesar primero ordenes antes que market data
                if not self.q_or.empty():
                    r = self.q_or.get()
                elif not self.q_md.empty():
                    r = self.q_md.get()
                # start = time()
                if r != None:
                    table= "orderReport" if r['type'] == 'or' else utils.DBtools.rename_table(r['instrumentId']['symbol'])
                    data = self.extract_features(r)
                    try:
                        utils.DBtools.sql_append(data, table,db=self.db)
                    except:
                        self.logger.exception("Exception appending data to DataBase.")
                    self.q_or.task_done() if r['type'] == 'or' else self.q_md.task_done()
            self.logger.debug("Process thread finished")
        except KeyboardInterrupt:
            self.logger.info("Process Thread end by user")
        except Exception:
            self.logger.exception("Exception in the process function")

    def subscribeOR(self):
        try:
            #Genero un orderDict pq en python 3.5 me cambia el orden continuamente sino y por ende recibo un msg error.
            msg = simplejson.dumps(OrderedDict([("type", "os"), ("account", self.account),("snapshotOnlyActive","true")]))
            #MSG_OSSuscription = simplejson.dumps({"type":"os","account":self.account,"snapshotOnlyActive":'true'})
            self.ws.send(msg)
            self.logger.info("Mensaje de subscripcion al OR enviado.")
        except:
            self.logger.exception("Error trying to subscribe to the Order Report")

    def make_MD_msg(self, ticker,entries):
        #Cretae the message to ask the Market Data of the entries for some ticker.
        msg = simplejson.dumps(OrderedDict([("type", "smd"), ("level", 1),("entries",entries),("products",[{"symbol":ticker,"marketId":"ROFX"}])]))
        return msg

    def subscribeMD(self, tickers, entries):
        for i,ticker in enumerate(tickers):
            msg = self.make_MD_msg(ticker,entries)
            self.ws.send(msg)
            self.logger.info("Mensaje de subscripcion a {} enviado".format(ticker))

    def make_order_msg(self,ticker,price,quantity,side):
        msg = OrderedDict([("type", "no"), 
                           ("product", OrderedDict([("symbol",ticker),
                                                   ("marketId","ROFX")])),
                           ("price",str(price)),
                           ("quantity",str(quantity)),
                           ("side",side),
                           ("account",self.account)])
        return simplejson.dumps(msg)
    
    def placeOrder(self,ticker,price,quantity,side):
        msg = self.make_order_msg(ticker,price,quantity,side)
        self.ws.send(msg)
        
    def delete(self):
        #Delete the WS
        self.logger.debug("Deleting the WS and threads")
        self.stopping.set()
        try:
            self.ws.close()
            if self.t_ws.isAlive():
                self.t_ws.join()
            if self.export_to_db:
                if self.t_process.isAlive():
                    self.t_process.join()
            self.logger.debug("All threads and websocket closed")
        except:
            self.logger.exception("Error trying to close the WS and close the thread.")

        
if __name__ == '__main__':
    from utils.createLogger import createLogger
    logger = createLogger()
    WS = websocket(user="salgozino898", password="oeofsZ2*", entorno=1, account='REM898')
    
  
