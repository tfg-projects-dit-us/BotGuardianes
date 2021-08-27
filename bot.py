from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import librerias.acciones_inicio
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


#Cargamos fichero de configuracion
global config
global logger

config = librerias.acciones_inicio.cargar_configuracion('config/config.yaml','r')
logger = librerias.acciones_inicio.crear_log(config)
logging.debug('Cargado fichero de configuracion config.yaml')


#Este es el token del bot que se ha generado con BotFather.
tokenbot= config['telegram']['token_bot']
librerias.funciones_telegram.bot=telegram.Bot(token=tokenbot)
logging.debug('Cargado token de Telegram. TokenID= ' + tokenbot)


logging.debug('Cargado token de Google')
cal_principal,cal_propuestas= librerias.acciones_inicio.cargar_calendarios(config)
logging.debug('Calendarios cargados')
print("Calendarios cargados. Iniciado correctamente")
#Función para calcular el timestamp del primer dia del mes

    


#print(cal_principal.events)
#print(datetime.datetime.now())
#print(timestampmesinicio())
#print(timestampmesfinal())
updater = Updater(token=tokenbot, use_context=True)
dispatcher = updater.dispatcher

#La función registro se le asigna a la funcion start del bot. Esta se llama cuando un usuario utiliza el bot por primera vez
start_handler = CommandHandler('start', registro)
dispatcher.add_handler(start_handler)


#Añadimos función de guardias disponibles
gdisp_handler=CommandHandler('guardiasdisponibles',guardiasdisponibles)
dispatcher.add_handler(gdisp_handler)


updater.start_polling()