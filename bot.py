from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, telegram
import ics
import datetime
import pytz
import calendar
import arrow
import locale
import yaml
locale.setlocale(locale.LC_ALL,'es_ES')

#Iniciamos el logging en la ventana de consola para mostrar información
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Este es el token del bot que se ha generado con BotFather.
tokenbot= None
with open("token.txt") as f:
    tokenbot = f.read().strip()
bot=telegram.Bot(token=tokenbot)

#Cargamos el calendario
ficherocalendario= open('calendario.ics','r')
calendario=ics.icalendar.Calendar(ficherocalendario.read())
ficherocalendario.close()

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
                     text="your message",
                     reply_markup=kb_markup)
#Esta funcion representa las guardias disponibles
def guardiasdisponibles(update, context):
    cadena=""
    #reply_markup=telegram.InlineKeyboardMarkup([])
    for e in calendario.events:
        if timestampmesfinal() >e.begin.datetime > timestampmesinicio():
            if list(e.attendees)[0].common_name == "Luis NG":
                cadena=cadena + "\n" +e.name + "Asistentes: " + list(e.attendees)[0].common_name + " : " + str(e.begin.format('DD-MM-YY HH:mm')) 
                #reply_markup
                print(update.effective_chat.id)
                bot.send_message(chat_id=update.message.chat_id,
                         text=cadena
                         )

    
    print('')

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
updater.start_polling()

#Anadimos la función de mayusculas al comando /caps del bot
caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)


#Añadimos función de guardias disponibles
gdisp_handler=CommandHandler('guardiasdisponibles',guardiasdisponibles)
dispatcher.add_handler(gdisp_handler)
