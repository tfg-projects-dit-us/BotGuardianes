import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import librerias.acciones_inicio
import telegram
import pytz
import calendar
import arrow
global bot
def timestampmesinicio():
    fecha=datetime.date.today()
    tstamp=datetime.datetime(fecha.year,fecha.month,1,0,0,0,tzinfo=pytz.timezone('Europe/Madrid'))
    return tstamp

#Función para calcular el timestamp del último día del mes
def timestampmesfinal():
    fecha=datetime.date.today()
    tstamp=datetime.datetime(fecha.year,fecha.month,calendar.monthrange(fecha.year,fecha.month)[1],23,59,59,tzinfo=pytz.timezone('Europe/Madrid'))
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
    print(update.effective_chat.id)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Ha sido registrado en la plataforma, ") #Imprimimos su nombre

    bot.send_message(chat_id=update.message.chat_id,
                     text="Su correo no ha sido encontrado en la plataforma. Por favor, consulte al administrador de su sistema para comprobar que sus datos están adecuadamente agregados")


#Esta funcion representa las guardias disponibles
def guardiasdisponibles(update, context):
    reply_markup=[]
    lista_botones=[[]]
    cadena=""
    events=librerias.acciones_inicio.service.events().list(calendarId='primary').execute()
    for e in events['items']:
        if timestampmesfinal() > pytz.timezone('Europe/Madrid').localize(datetime.datetime.strptime(e['start']['date'],'%Y-%m-%d')) > timestampmesinicio():
            if  list(e['attendees']) == []:
                lista_botones=lista_botones + [[telegram.InlineKeyboardButton(text=e.name + " - " + str(e['start']['date'].format('DD-MM-YY HH:mm') ),callback_data=patata) ]]

                cadena=cadena + "\n" +e['name'] +  " en fecha: " + str(e['begin'].format('DD-MM-YY HH:mm')) 
                

    reply_markup=telegram.InlineKeyboardMarkup(lista_botones)
    if cadena =="":
        bot.send_message(chat_id=update.message.chat_id,text="No hay guardias disponibles")

    else:
        bot.send_message(chat_id=update.message.chat_id,text=cadena,reply_markup=reply_markup)

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