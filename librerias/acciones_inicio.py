import yaml
import locale
import os.path
import datetime
import logging
import ics
import requests
def cargar_configuracion(directorio,modo):
    locale.setlocale(locale.LC_ALL,'es_ES')
    with open(directorio,modo) as configuracion:
        config=yaml.safe_load(configuracion)

    return config

def crear_log(config):
    if not os.path.exists('log'):
        os.makedirs('log')
        logging.info("Directorio log creado")

    #Comprobamos si está el nivel
    if "level" in config['log']:
        nivel_log_num=getattr(logging,config['log']['level'].upper())
        if not isinstance(nivel_log_num, int):
            raise ValueError('Nivel de log inválido: %s' % config['log']['level'])
        logging.basicConfig(filename='log/botguardianes-'+ str(datetime.datetime.today().strftime('%d.%m.%Y')) + '.log', filemode='a', encoding='utf-8',format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=nivel_log_num)
    else:
        logging.basicConfig(filename='log/botguardianes-'+ str(datetime.datetime.today()) + '.log', filemode='a', enconding='utf-8',format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.WARNING)

    logger = logging.getLogger()
    #logger.setLevel(logging.INFO)
    return logger
def cargar_calendarios(config):
    if "url_definitivos" in config['calendarios']:
        calendario_principal= ics.Calendar(requests.get(config['calendarios']['url_definitivos']).text,auth=(config['calendarios']['usuario'].text,config['calendarios']['contraseña'].text))
    else:
        logging.error('No está definida la url del calendario principal en config.yaml')
    if "url_propuestas" in config['calendarios']:
        calendario_propuestas= ics.Calendar(requests.get(config['calendarios']['url_propuestas']).text, auth=(config['calendarios']['usuario'].text,config['calendarios']['contraseña'].text))
    else:  
        logging.error('No está definida la url del calendario de propuestas en config.yaml')