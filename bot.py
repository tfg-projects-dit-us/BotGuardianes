from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from librerias.acciones_inicio import *
from librerias.funciones_calendario import *
from librerias.funciones_telegram import *
import logging
import telegram
import ics
import datetime
import pytz
import calendar
import arrow
import locale
import yaml
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

#Cargamos fichero de configuracion

config=cargar_configuracion('config/config.yaml','r')

logger=crear_log(config)
logging.debug('Cargado fichero de configuracion config.yaml')


#Este es el token del bot que se ha generado con BotFather.
tokenbot= config['telegram']['token_bot']
librerias.funciones_telegram.bot=telegram.Bot(token=tokenbot)
logging.debug('Cargado token de Telegram. TokenID= ' + tokenbot)

librerias.acciones_inicio.service = conectar_google()
logging.debug('Cargado token de Google')
cal_principal = librerias.acciones_inicio.service.calendars().get(calendarId='primary').execute()
logging.debug('Calendario principal cargado')

cal_propuestas = librerias.acciones_inicio.service.calendars().get(calendarId=config['calendarios']['id_propuestas']).execute()
logging.debug('Calendario de propuestas cargado')
#Función para calcular el timestamp del primer dia del mes

    


#print(cal_principal.events)
print(datetime.datetime.now())
print(timestampmesinicio())
print(timestampmesfinal())
updater = Updater(token=tokenbot, use_context=True)
dispatcher = updater.dispatcher

#La función start se le asigna a la funcion start del bot. Esta se llama cuando un usuario utiliza el bot por primera vez
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


#Añadimos función de guardias disponibles
gdisp_handler=CommandHandler('guardiasdisponibles',guardiasdisponibles)
dispatcher.add_handler(gdisp_handler)


updater.start_polling()