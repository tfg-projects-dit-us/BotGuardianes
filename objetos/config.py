import yaml
import locale
import os.path
import datetime
import logging
import ics
import requests
import sys
class config:
    def __init__(self,logger=None,directorio=None):
        self.directorio = directorio
        self.logger = logger
        self.configuracion=configuracion

    def cargar_configuracion_lectura(directorio):
        locale.setlocale(locale.LC_ALL,'es_ES')
        with open(directorio,'r') as configuracion:
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

        self.logger = logging.getLogger()
