import botMiron
from utils.createLogger import createLogger


if __name__ == '__main__':
    user = ''
    password = ''
    account = ''
    db = 'remarkets.db'
    entorno = 1
    logger = createLogger()
    botMiron.run(user=user, password=password, account=account, entorno=entorno,     db=db)
    

    while not botMiron.stopping.is_set():
        try:
            pass
        except KeyboardInterrupt:
            logger.debug("Closed by user")
            break
    logger.debug("Hasta la vista, baby!")