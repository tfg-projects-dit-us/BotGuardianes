import yaml
import locale
import os.path
import datetime
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
global service
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
def conectar_google():
    #Cargamos la cuenta de servicio de Google
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    #Comentar
    if os.path.exists('config/token.json'):
        creds = Credentials.from_authorized_user_file('config/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('config/token.json', 'w') as token:
            token.write(creds.to_json())

    #Cargamos el calendario de Google
    service = build('calendar', 'v3', credentials=creds)
    return service
   