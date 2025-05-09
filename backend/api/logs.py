import logging, sys

# Configuration de la journalisation
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(module)s.py -> %(message)s')
)
logger.addHandler(handler)


def info(s):
    return logger.info(s)
