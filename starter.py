from botMiron import botMiron
from utils.createLogger import createLogger


if __name__ == '__main__':
    user = 'salgozino898'
    password = 'oeofsZ2*'
    account = 'REM898'
    db = 'remarkets.db'
    entorno = 1
    logger = createLogger()
    bot = botMiron(user=user, password=password, account=account, entorno=entorno,
                 db=db)
    

    while not bot.stopping.is_set():
        try:
            pass
        except KeyboardInterrupt:
            logger.debug("Closed by user")
            break
    logger.debug("Hasta la vista, baby!")