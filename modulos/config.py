import yaml
import locale
import os.path
import datetime
import logging
import requests
import sys


class config:
    """
    Clase para empaquetar la configuración del bot de telegram

    Attributes:
        configfile: Diccionario conteniendo la configuración en un fichero yaml
        directorio: Ruta donde se encuentra el fichero de configuración. Por defecto en ./config/config.yaml
    """


    def __init__(self, directorio=None):
        """
        Método inicializador
        Args:
            directorio:
        """
        self.configfile=None
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
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return self.configfile

    def crear_log(self, config=None):
        if (config != None):
            self.configfile = config

        if not os.path.exists('log'):
            os.makedirs('log')
            logging.getLogger( __name__ ).info("Directorio log creado")
        # Comprobamos si está el nivel
        if 'level' in self.configfile['log']:
            nivel_log_num = getattr(logging, self.configfile['log']['level'].upper())
            if not isinstance(nivel_log_num, int):
                raise ValueError('Nivel de log invalido: %s' % self.configfile['log']['level'])
            logging.basicConfig(
                filename='log/botguardianes-' + str(datetime.datetime.today().strftime('%Y.%m.%d')) + '.log',
                filemode='a', encoding='utf-8', format='[%(asctime)s] - ·%(name)s· - %(levelname)s - %(message)s',
                level=nivel_log_num)
        else:
            logging.basicConfig(
                filename='log/botguardianes-' + str(datetime.datetime.today().strftime('%Y.%m.%d')) + '.log',
                filemode='a', enconding='utf-8', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.WARNING)

        logging.getLogger( __name__ ).debug(str(self.configfile))