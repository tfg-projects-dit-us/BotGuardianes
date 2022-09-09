import yaml
import locale
import os.path
import datetime
import logging
import requests
import sys
import sqlite3

class config:
    """
    Clase para empaquetar la configuración del bot de telegram

    Attributes:
        configfile(dict): Diccionario conteniendo la configuración en un fichero yaml
        directorio(str): Ruta donde se encuentra el fichero de configuración. Por defecto en ./data/config/config.yaml
    """


    def __init__(self, directorio:str):
        """
        Método inicializador
        Args:
            directorio: Directorio donde se encuentra el fichero de configuración en yaml
        """
        self.configfile:dict=None
        self.directorio = directorio
        self.cargar_configuracion_lectura()
        self.crear_log()
        self.crear_db()
    def cargar_configuracion_lectura(self, directorio:str=None)->dict:
        """
        Carga la configuración desde el archivo YAML de configuración

        Configura el locale en es_ES y carga el fichero YAML de manera que crea un diccionario guardado en configfile
        Args:
            directorio: Directorio donde se encuentra el fichero de configuración. Util para cargar otro fichero de configuración en tiempo de ejecución

        Returns:
            Devuelve diccionario con la configuración
        """
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        try:
            if (directorio == None and self.directorio != None):
                with open(self.directorio, 'r') as configuracion:
                    self.configfile:dict = yaml.safe_load(configuracion)
            elif (directorio != None):
                with open(directorio, 'r') as configuracion:
                    self.configfile:dict = yaml.safe_load(configuracion)

        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return self.configfile

    def crear_log(self, config:dict=None)->None:
        """
        Crea logs del servicio

        Este método crea una carpeta de logs en el directorio data si no existiera, y crea a su vez el fichero de log con la fecha actual como parte del nombre


        Args:
            config: Diccionario con la configuración, basado en la lectura del fichero yaml de configuración

        """
        if (config != None):
            self.configfile = config

        if not os.path.exists('./data/log'):
            os.makedirs('./data/log')
            logging.getLogger( __name__ ).info("Directorio log creado")
        # Comprobamos si está el nivel
        if 'level' in self.configfile['log']:
            nivel_log_num = getattr(logging, self.configfile['log']['level'].upper())
            if not isinstance(nivel_log_num, int):
                raise ValueError('Nivel de log invalido: %s' % self.configfile['log']['level'])
            logging.basicConfig(
                filename='data/log/botguardianes-' + str(datetime.datetime.today().strftime('%Y.%m.%d')) + '.log',
                filemode='a', encoding='utf-8', format='[%(asctime)s] - ·%(name)s· - %(levelname)s - %(message)s',
                level=nivel_log_num)
        #En caso de que no haya nivel definido, se pone por defecto warning
        else:
            logging.basicConfig(
                filename='data/log/botguardianes-' + str(datetime.datetime.today().strftime('%Y.%m.%d')) + '.log',
                filemode='a', enconding='utf-8', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.WARNING)

        logging.getLogger( __name__ ).debug(str(self.configfile))

    def crear_db(self):
        """
        Crea base de datos sqlite en el path definido en el fichero de configuración

        """

        connection=sqlite3.connect(self.configfile['sqlite']['path'])
        c=connection.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS relaciones_id (
                Idevento TEXT NOT NULL,
                Idmessage TEXT NOT NULL);
                ''')
        connection.commit()
        c.close()
        connection.close()