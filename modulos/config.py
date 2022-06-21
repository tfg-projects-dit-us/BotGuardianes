import yaml
import locale
import os.path
import datetime
import logging
import ics
import requests
import sys


class config:
    configfile = None
    directorio = None

    def __init__(self, directorio=None):
        self.directorio = directorio
        self.cargar_configuracion_lectura()
        self.crear_log()

    def cargar_configuracion_lectura(self, directorio=None):
        locale.setlocale(locale.LC_ALL, 'es_ES')
        try:
            if (directorio == None and self.directorio != None):
                with open(self.directorio, 'r') as configuracion:
                    self.configfile = yaml.safe_load(configuracion)
            elif (directorio != None):
                with open(directorio, 'r') as configuracion:
                    self.configfile = yaml.safe_load(configuracion)

        except Exception as e:
            logging.error("Error durante la carga de configuracion: " + str(e))
        return self.configfile

    def crear_log(self, config=None):
        if (config != None):
            self.configfile = config

        if not os.path.exists('log'):
            os.makedirs('log')
            logging.info("Directorio log creado")
        # Comprobamos si está el nivel
        if 'level' in self.configfile['log']:
            nivel_log_num = getattr(logging, self.configfile['log']['level'].upper())
            if not isinstance(nivel_log_num, int):
                raise ValueError('Nivel de log invalido: %s' % self.configfile['log']['level'])
            logging.basicConfig(
                filename='log/botguardianes-' + str(datetime.datetime.today().strftime('%d.%m.%Y')) + '.log',
                filemode='a', encoding='utf-8', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=nivel_log_num)
        else:
            logging.basicConfig(
                filename='log/botguardianes-' + str(datetime.datetime.today().strftime('%d.%m.%Y')) + '.log',
                filemode='a', enconding='utf-8', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.WARNING)

        logging.debug(str(self.configfile))