import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import librerias.acciones_inicio
import logging
import telegram
import pytz
import calendar
import arrow
import requests
from objetos import servicio_rest
from operator import attrgetter


token_bot=None
bot=None
logger=None
tokenbot=None
cal_principal=None
cal_propuestas=None

def start(token_bot=None, logger=None, bottelegram=None,cal_prim=None,cal_prop=None):
    global tokenbot,bot,cal_principal,cal_propuestas
    cal_principal=cal_prim
    cal_propuestas=cal_prop

    tokenbot = token_bot
    if (bottelegram is None and token_bot is not None):
        bot = telegram.Bot(token=telegram.update.tokenbot)
    else:
        bot = bottelegram

# Creamos una funcion de eco, que repite el mensaje que recibe
def echo(update, context):
    print(update.logger)
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# Esta funcion recibe un mensaje y cambia sus caracteres por mayusculas
def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

    # Esta funcion es la que inicia el bot cuando entra en contacto con un usuario

def registro(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Introduce tu correo electronico para registrarte en la plataforma",
                             reply_markup=telegram.ForceReply())
    return 1

def registro_paso2(update, context):
    logging.info(update.message.text)
    idusuario=False
    if ("@" in update.message.text):

        try:
            # Aqui pedimos a la API Rest la ID del usuario con su email
            respuesta = servicio_rest.GetIDPorEmail(email=update.message.text)
            logging.debug("Respuesta a GETIDPorEmail es:" + str(respuesta) + " tipo " + str(respuesta.isdigit()))
            if respuesta.isdigit():
                idusuario = respuesta
            elif "Could not fing a doctor with email:" in respuesta:
                context.bot.send_message(chat_id=update.message.chat_id,
                                        text="Su correo no ha sido encontrado en la plataforma.Por favor, consulte al "
                                             "administrador de su sistema para comprobar que sus datos estan adecuadamente "
                                             "agregados")
            if idusuario!= False:
                logging.info(idusuario)
                logging.info(update.effective_chat.id)
                respuesta = servicio_rest.InsertaTelegramID(idusuario=str(idusuario), chatid=update.effective_chat.id)
                logging.debug("Valor de respuesta " + str(respuesta))
                # Aqui haríamos la consulta a REST para preguntar si existe ese correo electrónico. Si es el caso,
                # enviaríamos el id
                if respuesta.lower()=='true':
                    context.bot.send_message(chat_id=update.message.chat_id,
                                     text="Ha sido registrado en la plataforma, " + servicio_rest.GetNombrePorID(idusuario))  # Imprimimos su nombre


            kb = [
                [
                    telegram.KeyboardButton('/guardias_disponibles'),
                    telegram.KeyboardButton('/guardias_propias')
                ],
                [
                    telegram.KeyboardButton('Boton 3'),
                    telegram.KeyboardButton('Boton 4')
                ]
            ]

            kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

            context.bot.send_message(chat_id=update.message.chat_id,
                             text="Seleccione una opcion",
                             reply_markup=kb_markup)
            return ConversationHandler.END
        except Exception as e:
            context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error en la plataforma")
            logging.error("Error al hacer conexion con la API "+str(e))
            return ConversationHandler.END

    else:
        update.message.reply_text("La cadena no tiene un @. Intente de nuevo enviar su correo")
        return 1

# Esta funcion representa las guardias disponibles
def guardiasdisponibles(update, context):
    global cal_principal,cal_propuestas
    reply_markup = []
    lista_botones = [[]]
    calendario=cal_principal
    cadena = ""
    lista_eventos=cal_principal.get_eventos()
    try:
        if lista_eventos==[]:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay guardias disponibles")
            logging.debug("No hay guardias disponibles")
        else:
            for e in sorted(lista_eventos,key=attrgetter('begin')):
                lista_botones = [[telegram.InlineKeyboardButton(
                            text=e.name + " - " + str(e.begin.format('DD-MM-YY HH:mm')), callback_data=e.uid)]]

                cadena = e.name + " en fecha: " + str(e.begin.format('DD-MM-YY HH:mm'))

                reply_markup = telegram.InlineKeyboardMarkup(lista_botones)
                context.bot.send_message(chat_id=update.message.chat_id, text=cadena, reply_markup=reply_markup)
                logging.debug(cadena)

    except Exception as e:
        logging.error(str(e))



def guardiaspropias(update, context):
    global cal_principal, cal_propuestas
    # reply_markup=telegram.InlineKeyboardMarkup([])
    cadena = ""
    lista_eventos=[]
    try:
        idrest=servicio_rest.GetidRESTPorIDTel(update.message.chat_id)
        nombre_usuario=servicio_rest.GetNombrePorID(id=idrest)
        email_usuario=servicio_rest.GetEmailPorID(id=idrest)
        lista_eventos=cal_principal.get_eventos(email_usuario)
        # Aqui pediriamos el nombre del usuario a traves de REST, usando el id de Telegram como dato
        #hace falta una función de obtener la ID por la ID de Telegram
        logging.debug("El usuario " + nombre_usuario + " ha solicitado sus propias guardias. Fecha actual " + str(datetime.date.today()))
            # str(e.begin.format('DD-MM-YY HH:mm'))
            # reply_markup

        for e in sorted(lista_eventos,key=attrgetter('begin')):
            logging.debug("Evento con el usuario incluido" + str(e))
            cadena = e.name + ". Asignada a:\n "
            for asistente in e.attendees:
                cadena+= " - " + asistente.common_name +"\n "
            cadena+= " en fecha: " + str(e.begin.format('DD-MM-YY HH:mm'))
            context.bot.send_message(chat_id=update.message.chat_id,text=cadena)

    except Exception as e:
        logging.warning("Excepción recogiendo guardia propia" + str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las guardias propias, por favor, póngase en contacto con el administrador"
                             )

def callback(update, context):
    try:
        if update.callback_query.answer():
            uid_evento=update.callback_query.data
            print("UID del evento es:" + str(uid_evento) + " por el usuario " + str(update.callback_query.from_user.id))
            logging.debug("UID del evento es:" + str(uid_evento) + " por el usuario " + str(update.callback_query.from_user.id))
    except AttributeError as e:
        logging.error("Error recogiendo nombre del evento con UID {}. Valor de callback {}".format(uid_evento,update.callback_query))
