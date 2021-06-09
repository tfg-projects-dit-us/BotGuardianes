from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, telegram
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
#Iniciamos el logging en la ventana de consola para mostrar información

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


locale.setlocale(locale.LC_ALL,'es_ES')
#Cargamos fichero de configuracion

with open('config.yaml','r') as configuracion:
    config=yaml.safe_load(configuracion)

logging.debug('Cargado fichero de configuracion config.yaml')


#Este es el token del bot que se ha generado con BotFather.
tokenbot= config['telegram']['token_bot']
bot=telegram.Bot(token=tokenbot)
logging.debug('Cargado token de Telegram. TokenID= ' + tokenbot)

#Cargamos la cuenta de servicio de Google
SCOPES = ['https://www.googleapis.com/auth/calendar']
#Cargamos el calendario de Google
creds = service_account.Credentials.from_service_account_file('service_secret.json', scopes=SCOPES)

service = build('calendar', 'v3', credentials=creds)

logging.debug('Cargado token de Google')
cal_principal = service.calendars().get(calendarId=config['calendarios']['id_principal']).execute()
logging.debug('Calendario principal cargado')

cal_propuestas = service.calendars().get(calendarId=config['calendarios']['id_propuestas']).execute()
logging.debug('Calendario de propuestas cargado')
#Función para calcular el timestamp del primer dia del mes

def timestampmesinicio():
    fecha=datetime.date.today()
    tstamp=datetime.datetime(fecha.year,fecha.month,1,0,0,0,tzinfo=pytz.timezone('Europe/Madrid'))
    return tstamp

#Función para calcular el timestamp del último día del mes
def timestampmesfinal():
    fecha=datetime.date.today()
    tstamp=datetime.datetime(fecha.year,fecha.month,calendar.monthlen(fecha.year,fecha.month),23,59,59,tzinfo=pytz.timezone('Europe/Madrid'))
    return tstamp

#Creamos una funcion de eco, que repite el mensaje que recibe
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

#Esta funcion recibe un mensaje y cambia sus caracteres por mayusculas
def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)    

#Esta funcion es la que inicia el bot cuando entra en contacto con un usuario
def start(update, context):
    #Aqui creamos el teclado por botones que se le mostraraa al usuario en esta funcion
    kb = [[telegram.KeyboardButton('/guardiasdisponibles'),telegram.KeyboardButton('/guardiaspropias')],
          [telegram.KeyboardButton('Boton 3'),telegram.KeyboardButton('Boton 4')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb,resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Seleccione una opción",
                     reply_markup=kb_markup)


def registro(update, context):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Introduce tu correo electrónico para registrarte en la plataforma",
                     )
    #Aqui haríamos la consulta a REST para preguntar si existe ese correo electrónico. Si es el caso, enviaríamos el id
    
    bot.send_message(chat_id=update.message.chat_id,
                     text="Ha sido registrado en la plataforma, ") #Imprimimos su nombre

    bot.send_message(chat_id=update.message.chat_id,
                     text="Su correo no ha sido encontrado en la plataforma. Por favor, consulte al administrador de su sistema para comprobar que sus datos están adecuadamente agregados")


#Esta funcion representa las guardias disponibles
def guardiasdisponibles(update, context):
    reply_markup=[]
    lista_botones=[[]]
    cadena=""
    for e in calendario.events:
        if timestampmesfinal() >e.begin.datetime > timestampmesinicio():
            if  list(e.attendees) == []:
                lista_botones=lista_botones + [[telegram.InlineKeyboardButton(text=e.name + " - " + str(e.begin.format('DD-MM-YY HH:mm') ),callback_data=patata) ]]

                cadena=cadena + "\n" +e.name +  " en fecha: " + str(e.begin.format('DD-MM-YY HH:mm')) 
                #reply_markup
                #print(update.effective_chat.id)

    reply_markup=telegram.InlineKeyboardMarkup(lista_botones)
    bot.send_message(chat_id=update.message.chat_id,
                         text=cadena,
                         reply_markup=reply_markup
                         )

def guardiaspropias(update, context):
    #reply_markup=telegram.InlineKeyboardMarkup([])
    cadena=""
    for e in calendario.events:
        if timestampmesfinal() >e.begin.datetime > timestampmesinicio():
            #Aqui pediriamos el nombre del usuario a través de REST, usando el id de Telegram como dato
            nombre_usuario="NOMBRE"
            if list(e.attendees)[0].common_name == nombre_usuario:
                #str(e.begin.format('DD-MM-YY HH:mm')) 
                #reply_markup
                cadena=cadena + "\n" + e.name + "Asignada a " + list(e.attendees)[0].common_name + " en fecha: " +str(e.begin.format('DD-MM-YY HH:mm'))

    bot.send_message(chat_id=update.message.chat_id,
                         text=cadena
                         )
    


print(calendario.events)
print(datetime.datetime.now())
print(timestampmesinicio())
print(timestampmesfinal())
updater = Updater(token=tokenbot, use_context=True)
dispatcher = updater.dispatcher

#La función start se le asigna a la funcion start del bot. Esta se llama cuando un usuario utiliza el bot por primera vez
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


#Aplico la funcion echo a los mensajes escritos que se reciben
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)


#Anadimos la función de mayusculas al comando /caps del bot
caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)


#Añadimos función de guardias disponibles
gdisp_handler=CommandHandler('guardiasdisponibles',guardiasdisponibles)
dispatcher.add_handler(gdisp_handler)


updater.start_polling()