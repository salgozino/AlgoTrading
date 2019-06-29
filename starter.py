import botMiron
import botFollowTheLeader
from utils.createLogger import createLogger


if __name__ == '__main__':

    logger = createLogger()
    botMiron.run()
    botFollowTheLeader.run()

    while True:
        try:
            pass
        except KeyboardInterrupt:
                logger.debug("Hasta la vista, baby!")