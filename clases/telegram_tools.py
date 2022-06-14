import datetime
import sys
import logging
from urllib.parse import urlparse

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram
import ics

from clases import servicio_rest
from operator import attrgetter


token_bot=None
bot=None
logger=None
tokenbot=None
cal_principal=None
cal_propuestas=None
canalid=None

def start(token_bot=None, logger=None, bottelegram=None,cal_prim=None,cal_prop=None,canal_id=None):
    global tokenbot,bot,cal_principal,cal_propuestas,canalid
    cal_principal=cal_prim
    cal_propuestas=cal_prop
    canalid=canal_id
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
    logging.debug(update.message.text)
    idusuario=False
    if ("@" in update.message.text):

        try:
            # Aqui pedimos a la API Rest la ID del usuario con su email
            respuesta = servicio_rest.GetIDPorEmail(email=update.message.text)
            logging.debug("Respuesta a GETIDPorEmail es:" + str(respuesta) + " tipo " + str(respuesta.isdigit()))
            if respuesta.isdigit():
                idusuario = respuesta
            elif "Could not fing a doctor" in respuesta:
                context.bot.send_message(chat_id=update.message.chat_id,
                                        text="Su correo no ha sido encontrado en la plataforma.\nPor favor, consulte al "
                                             "administrador de su sistema para comprobar que sus datos estan adecuadamente "
                                             "agregados")
                return ConversationHandler.END
            if idusuario!= False:
                logging.debug(idusuario)
                logging.debug(update.effective_chat.id)
                respuesta = servicio_rest.InsertaTelegramID(idusuario=str(idusuario), chatid=update.effective_chat.id)
                logging.debug("Valor de respuesta " + str(respuesta))
                # Aqui haríamos la consulta a REST para preguntar si existe ese correo electrónico. Si es el caso,
                # enviaríamos el id
                if respuesta=='ID de telegram actualizado':
                    context.bot.send_message(chat_id=update.message.chat_id,
                                     text="Ha sido registrado en la plataforma,{}".format(servicio_rest.GetNombrePorID(idusuario)))  # Imprimimos su nombre
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text="Ha habido un error en la plataforma\nContacte por favor con soporte")

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
    lista_botones = []
    cadena = ""
    lista_eventos=cal_principal.get_eventos()
    try:
        if lista_eventos==[]:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay guardias disponibles")
            logging.debug("No hay guardias disponibles")
        else:
            for e in lista_eventos:
                lista_botones = lista_botones+ [[telegram.InlineKeyboardButton(
                            text=e.get_summary() + " - " + e.get_fecha_str(), callback_data="tomar;{}".format(e.get_uid()))]]

                cadena = cadena + e.get_summary() + " en fecha: " + e.get_fecha_str()+"\n"

            reply_markup = telegram.InlineKeyboardMarkup(lista_botones)
            context.bot.send_message(chat_id=update.message.chat_id, text=cadena, reply_markup=reply_markup)
            logging.debug(cadena)

    except Exception as e:
        logging.error(str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")


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



        if lista_eventos==[]:
            context.bot.send_message(chat_id=update.message.chat_id,text="No hay eventos asignados a usted")
            #key=lambda fecha: e.vobject_instance.vevent.dstart
        for e in lista_eventos:
            logging.debug("Evento con el usuario incluido" + str(e))
            cadena = e.get_summary() + ". Asignada a:\n "
            for asistente in e.get_asistentes():
                nombre=servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                cadena+= " - " +nombre +" (" +asistente +") \n "
            cadena+= " en fecha: " + e.get_fecha_str()
            boton_callback=[[telegram.InlineKeyboardButton(
                text="Proponer cambio de guardia", callback_data="ceder;{}".format(e.get_uid()))]]
            context.bot.send_message(chat_id=update.message.chat_id,text=cadena,reply_markup=telegram.InlineKeyboardMarkup(boton_callback))



    except Exception as e:
        logging.warning("Excepción recogiendo guardia propia" + str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las guardias propias, por favor, póngase en contacto con el administrador"
                             )

def ceder_evento(uid,attendee):
    global cal_principal, cal_propuestas
    try:
        evento=cal_principal.get_evento(uid)
        evento_cedido=cal_propuestas.ceder_evento(asistente=attendee,evento=evento,uidevento=uid)

        if isinstance(evento_cedido,ics.icalendar.Event):
            return evento_cedido
    except Exception as e:
        logging.error("Error cediendo evento en Telegram_Tools: " + str(e))
        return False
def callback(update, context):
    global cal_principal, cal_propuestas

    try:
        if update.callback_query.answer():
            print("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')
            if accion=="ceder":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cedido=ceder_evento(uid_evento,correo)

                if isinstance(cedido,ics.icalendar.Event):
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Se ha cedido con éxito el evento")
                    for attendee in cedido.attendees:
                        pass


            print("UID del evento es:" + str(uid_evento) + " por el usuario " + str(update.callback_query.from_user.id))
            logging.debug("UID del evento es:" + str(uid_evento) + " por el usuario " + str(update.callback_query.from_user.id))
    except BaseException as e:
        logging.error("Error recogiendo nombre del evento con UID {}. Valor de callback {}. Función ejecutada {}".format(uid_evento,
                                                                                                   update.callback_query, sys._getframe(1).f_code.co_name))
