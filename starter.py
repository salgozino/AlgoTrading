#!/usr/bin/python3
from datetime import datetime
from botMiron import botMiron
from utils.createLogger import createLogger
from threading import Thread

if __name__ == '__main__':
    user = 'salgozino898'
    password = 'oeofsZ2*'
    account = 'REM898'
    db = 'remarkets.db'
    entorno = 1
    logger = createLogger()
    bot = botMiron(user=user, password=password, account=account, entorno=entorno,
                 db=db)
    t = Thread(target=bot.run, name='bot')
    t.daemon = True
    t.start()

    while not bot.stopping.is_set():
        try:
            if datetime.now() > datetime.today().replace(hour=17,minute=5):
                #Despues de las 17 hs apago el bot miron
                logger.info("Market Closed!")
                bot.stopping.set()
                t.join()
                
        except KeyboardInterrupt:
            logger.debug("Closed by user")
            break
    logger.debug("Hasta la vista, baby!")
