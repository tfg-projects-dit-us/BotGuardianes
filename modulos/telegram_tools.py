"""
Módulo para agregar manejo del servicio de Telegram y aportar funcionalidad para el servicio de Guardianes

Contiene las variables de módulo:

- `bot`: Contiene un objeto tipo telegram.Bot
- `tokenbot`: Contiene una cadena con el token del bot de Telegram
- `cal_principal`: Contiene un objeto gestor_calendario.Calendario que define el calendario principal del servicio
- `cal_propuestas`: Contiene un objeto gestor_calendario.Calendario que define el calendario de propuestas del servicio
- `canalid`: Contiene una cadena con la id del canal de avisos de guardias del servicio

Contiene las funciones:

- TODO
"""

import datetime
import sys
import logging
import sqlite3
from urllib.parse import urlparse
from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram
import ics

from modulos import gestor_calendario
from modulos import servicio_rest
from operator import attrgetter


bot:            telegram.Bot                =None
tokenbot:       str                         =None
cal_principal:  gestor_calendario.Calendario=None
cal_propuestas: gestor_calendario.Calendario=None
canalid:        str                         =None

def autenticar(func):
    """
    Método para autenticar usuario al usar las funciones. Verifica si el usuario está inscrito en el servicio REST
    Se utiliza como un decorador

    Args:
        func: Función a la que envuelve este método

    """
    @wraps(func)
    def wrapper(*args,**kwargs):
        id_user=args[0].message.chat_id
        respuesta=servicio_rest.GetidRESTPorIDTel(id_user)
        if respuesta.isdigit():
            func(*args, **kwargs)
        elif "Could not fing a doctor" in respuesta:
            args[1].bot.send_message(chat_id=id_user,
                                        text="No se encuentra identificado y registrado en la plataforma."
                                             "Por favor, regístrese con la función /start")

    return wrapper


def autenticar_retorno(func):
    """
    Método para autenticar usuario al usar el retorno. Verifica si el usuario está inscrito en el servicio REST
    Se utiliza como un decorador

    Args:
        func: Función a la que envuelve este método

    """
    @wraps(func)
    def wrapper(*args,**kwargs):
        id_user=str(args[0].callback_query.from_user.id)
        respuesta=servicio_rest.GetidRESTPorIDTel(id_user)
        if respuesta.isdigit():
            func(*args, **kwargs)
        elif "Could not fing a doctor" in respuesta:
            args[1].bot.send_message(chat_id=id_user,
                                        text="No se encuentra identificado y registrado en la plataforma."
                                             "Por favor, regístrese con la función /start")

    return wrapper

def autenticar_retorno_admin(func):
    """
    Método para autenticar usuario al usar el retorno. Verifica si el usuario está inscrito en el servicio REST
    Se utiliza como un decorador

    Args:
        func: Función a la que envuelve este método

    """
    @wraps(func)
    def wrapper(*args,**kwargs):
        id_user=str(args[0].callback_query.from_user.id)
        id_rest=servicio_rest.GetidRESTPorIDTel(id_user)
        email=servicio_rest.GetEmailPorID(id_rest)
        roles=servicio_rest.GetRolesPorEmail(email)
        if "Administrador" in roles:
            if id_rest.isdigit():
                func(*args, **kwargs)
        elif "Could not fing a doctor" in respuesta:
            args[1].bot.send_message(chat_id=id_user,
                                        text="No se encuentra identificado y registrado en la plataforma."
                                             "Por favor, regístrese con la función /start")

    return wrapper


def autenticar_admin(func):
    """
    Método para autenticar usuario al usar las funciones del bot. Verifica si es un administrador.
    Se utiliza como un decorador

    Args:
        func: Función a la que envuelve este método

    """
    @wraps(func)
    def wrapper(*args,**kwargs):
        id_user=args[0].message.chat_id
        id_rest=servicio_rest.GetidRESTPorIDTel(id_user)
        email=servicio_rest.GetEmailPorID(id_rest)
        roles=servicio_rest.GetRolesPorEmail(email)
        if "Administrador" in roles:
            func(*args,**kwargs)
        else:
            args[1].bot.send_message(chat_id=id_user,
                                     text="No tiene el rol adecuado para esta función."
                                          "Verifique sus permisos con el administrador del sistema")
    return wrapper

def start(token_bot=None, cal_prim=None,cal_prop=None,canal_id=None):
    """
    Función de inicialización del bot de Telegram

    Args:
        token_bot: Token de Telegram para autenticar el bot en el sistema de Telegram
        cal_prim: Calendario principal que se utiliza en el servicio de guardias
        cal_prop: Calendario de propuestas de cambio en el servicio de guardias
        canal_id: Id para el canal de publicación de guardias.

    """
    global tokenbot,bot,cal_principal,cal_propuestas,canalid
    cal_principal=cal_prim
    cal_propuestas=cal_prop
    canalid=canal_id
    tokenbot = token_bot
    bot = telegram.Bot(token=token_bot)



def registro_paso1(update, context):
    """
    Primer paso para registrar ID del usuario en Telegram en el servicio REST de Guardianes.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    Returns:
        Devuelve estado actual del registro_paso1. Paso 1 completo
    """
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Introduce tu correo electronico para registrarte en la plataforma",
                             reply_markup=telegram.ForceReply())
    return 1

def registro_paso2(update, context):
    """
    Segundo paso para registrar ID del usuario en Telegram en el servicio REST de Guardianes.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    Returns:
        Devuelve estado actual del registro_paso1. O bien vuelta a empezar este paso o fin de avance en estados
    """
    logging.getLogger( __name__ ).debug(update.message.text)
    idusuario=False
    if ("@" in update.message.text):

        try:
            # Aqui pedimos a la API Rest la ID del usuario con su email
            respuesta = servicio_rest.GetIDPorEmail(email=update.message.text)
            logging.getLogger( __name__ ).debug("Respuesta a GETIDPorEmail es:" + str(respuesta) + " tipo " + str(respuesta.isdigit()))
            if respuesta.isdigit():
                idusuario = respuesta
            elif "Could not fing a doctor" in respuesta:
                context.bot.send_message(chat_id=update.message.chat_id,
                                        text="Su correo no ha sido encontrado en la plataforma.\nPor favor, consulte al "
                                             "administrador de su sistema para comprobar que sus datos estan adecuadamente "
                                             "agregados")
                return ConversationHandler.END
            if idusuario!= False:
                logging.getLogger( __name__ ).debug(idusuario)
                logging.getLogger( __name__ ).debug(update.effective_chat.id)
                respuesta = servicio_rest.InsertaTelegramID(idusuario=str(idusuario), chatid=update.effective_chat.id)
                logging.getLogger( __name__ ).debug("Valor de respuesta " + str(respuesta))
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
            logging.getLogger( __name__ ).error("Error al hacer conexion con la API "+str(e))
            return ConversationHandler.END

    else:
        update.message.reply_text("La cadena no tiene un @. Intente de nuevo enviar su correo")
        return 1

def botones(update, context):
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

def editar_datos_evento( evento:gestor_calendario.Evento, id_chat:str, id_mensaje:str,accion:str="nada"):
    reply_markup = []
    mensaje = None
    boton_callback = [[telegram.InlineKeyboardButton
        (
        text="{} - {}".format(evento.get_summary(), evento.get_fecha_str()),
        callback_data="{};{}".format(accion, evento.get_uid())
    )
    ]]

    cadena = "<b>{}</b> en fecha: {}\nSitios libres: {}".format(evento.get_summary(), evento.get_fecha_str(),
                                                                evento.get_sitios_libres())
    if accion != "nada":
        reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
        mensaje = bot.editMessageText(chat_id=id_chat,message_id=id_mensaje,text=cadena,reply_markup=reply_markup, parse_mode="HTML")



def mostrar_datos_evento(modo:str, evento:gestor_calendario.Evento, id_chat:str,accion:str="nada"):
    """
    Función para presentar datos de un evento en un chat de telegram

    Args:
        modo: Modo en el que se presenta el evento:

            ···resumen: Solo muestra nombre, puestos libres y fecha del evento

            ···completo: Muestra nombre, fecha e integrantes del evento

        evento: Objeto gestor_calendario.Evento que contiene los datos del evento a representar.

        id_chat: Identificador del chat donde se van a mostrar los datos del evento
        accion: Accion que se pone en el mensaje de retorno cuando se pulsa un botón de un mensaje con un evento.
                Si la acción es nada, no se pone un botón
    """
    reply_markup=[]
    mensaje=None
    if modo=="resumen":
        boton_callback = [[telegram.InlineKeyboardButton
                (
                    text="{} - {}".format(evento.get_summary(),evento.get_fecha_str()),
                    callback_data="{};{}".format(accion,evento.get_uid())
                )
                ]]

        cadena = "<b>{}</b> en fecha: {}\nSitios libres: {}".format(evento.get_summary(), evento.get_fecha_str(),evento.get_sitios_libres())
        if accion!="nada":
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, reply_markup=reply_markup,parse_mode="HTML")
        else:
            cadena = "Evento en el que se ha inscrito a la espera de aprobación\n\n" + cadena
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, parse_mode="HTML")

    if modo=="completo":

        cadena = "<b>{}</b>\n".format(evento.get_summary())

        if evento.get_cuenta_asistentes()>0:
            cadena += "<i>Asignado a</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_asistente_rol(asistente)=="REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        if evento.get_cuenta_ofertantes()>0:
            cadena += "\n<i>Ofertantes del turno</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_asistente_rol(asistente)=="OPT-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        if evento.get_cuenta_demandantes() > 0:
            cadena += "\n<i>Demandantes del turno</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_asistente_rol(asistente) == "NON-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)
        cadena += "\nen fecha: <b>{}</b>".format(evento.get_fecha_str())
        boton_callback = [[telegram.InlineKeyboardButton(
            text="Proponer cambio de guardia", callback_data="{};{}".format(accion,evento.get_uid()))]]
        if accion != "nada":
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)

            mensaje=bot.send_message(chat_id=id_chat, text=cadena,
                                 reply_markup=reply_markup,parse_mode="HTML")
        else:
            cadena = "Evento en el que se ha inscrito a la espera de aprobación\n\n" + cadena
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, parse_mode="HTML")
    return mensaje.message_id
@autenticar
def guardiasdisponibles(update, context):
    """
    Función para obtener las guardias en las que hay al menos un puesto con propuesta de cambio.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal,cal_propuestas
    reply_markup = []
    lista_botones = []
    cadena = ""
    lista_eventos=cal_propuestas.get_eventos()
    try:
        if lista_eventos==[]:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay guardias disponibles")
            logging.getLogger( __name__ ).debug("No hay guardias disponibles")
        else:
            for e in lista_eventos:
                mostrar_datos_evento("resumen",evento=e,id_chat=update.message.chat_id,accion="tomar")


            logging.getLogger( __name__ ).debug(cadena)

    except Exception as e:
        logging.getLogger( __name__ ).error(str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")

@autenticar
def guardiaspropias(update, context):
    """
    Función para obtener las guardias propias del usuario actualmente establecidas.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
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
        logging.getLogger( __name__ ).debug("El usuario {} ha solicitado sus propias guardias. Fecha actual {}".format(nombre_usuario,datetime.date.today()))



        if lista_eventos==[]:
            context.bot.send_message(chat_id=update.message.chat_id,text="No hay eventos asignados a usted")
            #key=lambda fecha: e.vobject_instance.vevent.dstart
        for e in lista_eventos:
            logging.getLogger( __name__ ).debug("Evento con el usuario incluido: {}".format(e))
            mostrar_datos_evento("completo",evento=e,id_chat=update.message.chat_id,accion="ceder")



    except Exception as e:
        logging.getLogger( __name__ ).warning("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las guardias propias, por favor, póngase en contacto con el administrador"
                             )
@autenticar
def guardias_pendientes_aprobacion(update, context):
    pass
def ceder_evento(uid,attendee):
    """
    Función para que un usuario pueda ceder su puesto en una guardia y guardar dicha propuesta en el calendario de propuestas

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a ceder su puesto en una guardia

    Returns:
        Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento=cal_principal.get_evento(uid)
        evento_cedido=cal_propuestas.ceder_evento(correo_usuario=attendee,evento=evento,uid_evento=uid)

        if isinstance(evento_cedido,gestor_calendario.Evento):
            return evento_cedido
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None

def tomar_evento(uid,attendee):
    """
    Función para que un usuario pueda ceder su puesto en una guardia y guardar dicha propuesta en el calendario de propuestas

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a ceder su puesto en una guardia

    Returns:
        Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento=cal_propuestas.get_evento(uid)
        if isinstance(evento,gestor_calendario.Evento):
            evento_tomado=cal_propuestas.tomar_evento(correo_usuario=attendee,uid_evento=uid)

            if evento_tomado:
                return evento_tomado
            else:
                return None
        else:
            return None
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None

def borrar_mensaje(id_chat,id_mensaje):
    """
    Función para borrar un mensaje cuando se ha cursado la petición de tomar un evento

    Args:
        id_chat: Id del chat de donde se hace la acción de tomar evento
        id_mensaje: ID del mensaje a borrar

    Returns:
        Verdadero si pudo completarlo, falso si no
    """
    terminado=False
    try:
        terminado=bot.deleteMessage(chat_id=id_chat,message_id=id_mensaje)
        return terminado
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return terminado

@autenticar_retorno
def retorno_ceder(update, context):
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    Si la acción es ceder, cambia el rol del usuario a OPT-PARTICIPANT para designar un hueco libre en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect('./relacionesids')
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="ceder":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cedido=ceder_evento(uid_evento,correo)

                if isinstance(cedido,gestor_calendario.Evento):
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Se ha cedido con éxito el evento")
                    cursor.execute("SELECT Idmessage FROM relaciones_id where Idevento=?;", (cedido.get_uid(),) )
                    idmensaje = cursor.fetchall()
                    if idmensaje==[]:
                        idmensaje=mostrar_datos_evento("resumen",cedido,canalid,"tomar")
                        cursor.execute(f"""INSERT OR REPLACE INTO  relaciones_id  (Idevento,Idmessage)
                                       VALUES ( COALESCE((SELECT Idevento FROM relaciones_id WHERE Idevento="{cedido.get_uid()}"),"{cedido.get_uid()}"),"{idmensaje}");""")
                        relacion.commit()
                    else:
                        idmensaje=idmensaje[0][0]
                        editar_datos_evento(cedido,canalid,idmensaje,"tomar")



            logging.getLogger( __name__ ).debug("UID del evento es:{} por el usuario {}".
                                                format(uid_evento,update.callback_query.from_user.id))
        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
                                            format(sys._getframe(1).f_code.co_name,uid_evento,update.callback_query,e ))
        cursor.close()
        relacion.close()


@autenticar_retorno
def retorno_tomar(update, context):
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es tomar, añade al usuario con el rol NON-PARTICIPANT al evento en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect('./relacionesids')
    cursor=relacion.cursor()
    idmensaje=None
    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="tomar":
                correo = servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                tomado=tomar_evento(uid_evento,correo)


                if isinstance(tomado,gestor_calendario.Evento):
                    mostrar_datos_evento("completo", tomado, update.callback_query.from_user.id, "nada")
                    if tomado.get_sitios_libres()==0:
                        if update.callback_query.message.chat_id!=canalid:
                            borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=update.callback_query.message.message_id)
                            cursor.execute("SELECT Idmessage FROM relaciones_id where Idevento=?;",(tomado.get_uid()),)
                            idmensaje=cursor.fetchall()
                            borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=idmensaje)
                            cursor.execute("DELETE FROM relaciones_id where Idevento=?;",(tomado.get_uid()),)
                            relacion.commit()
                        else:
                            borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                           id_mensaje=update.callback_query.message.message_id)
                            cursor.execute("DELETE FROM relaciones_id where Idevento=?;",(tomado.get_uid(),))
                            relacion.commit()
                    else:
                        cursor.execute("SELECT Idmessage FROM relaciones_id where Idevento=?;", (tomado.get_uid(),) )
                        idmensaje = cursor.fetchall()
                        idmensaje = idmensaje[0][0]
                        editar_datos_evento(tomado, canalid, idmensaje, "tomar")
                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Ha habido un problema a la hora de inscribirse en el evento."
                                                                                             "Póngase en contacto con un administrador")


            logging.getLogger( __name__ ).debug("UID del evento es:{} por el usuario {}".
                                                format(uid_evento,update.callback_query.from_user.id))
        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
                                            format(sys._getframe(1).f_code.co_name,uid_evento,update.callback_query,e ))
        cursor.close()
        relacion.close()


@autenticar_retorno_admin
def retorno_aceptar(update, context):
    """
    Función para recibir datos del administrador cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es aceptar, toma el evento en el calendario de propuestas, lo coloca en el lugar del calendario principal
    y lo borra del calendario de propuestas. Informa a los participantes

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas, bot, canalid


    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento = update.callback_query.data.split(';')

            if accion == "aceptar":
                correo = servicio_rest.GetEmailPorID(
                    servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                tomado = tomar_evento(uid_evento, correo)

                if isinstance(tomado, gestor_calendario.Evento):
                    mostrar_datos_evento("completo", tomado, update.callback_query.from_user.id, "nada")
                    if update.callback_query.message.chat_id != canalid:
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)
                        cursor.execute("SELECT Idmessage FROM relaciones_id where Idevento=?;", (tomado.get_uid()), )
                        idmensaje = cursor.fetchall()
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id, id_mensaje=idmensaje)
                        cursor.execute("DELETE FROM relaciones_id where Idevento=?;", (tomado.get_uid()), )
                        relacion.commit()
                    else:
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)
                        cursor.execute("DELETE FROM relaciones_id where Idevento=?;", (tomado.get_uid(),))
                        relacion.commit()

                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Ha habido un problema a la hora de inscribirse en el evento."
                                                  "Póngase en contacto con un administrador")

            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))
        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()


@autenticar_retorno_admin
def retorno_denegar(update, context):
    """
    Función para recibir datos del administrador cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es denegar, toma el evento en el calendario de propuestas, y lo elimina. Informa a los participantes del evento de este cambio.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas, bot, canalid


    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento = update.callback_query.data.split(';')

            if accion == "denegar":
                correo = servicio_rest.GetEmailPorID(
                    servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                tomado = tomar_evento(uid_evento, correo)

                if isinstance(tomado, gestor_calendario.Evento):
                    mostrar_datos_evento("completo", tomado, update.callback_query.from_user.id, "nada")
                    if update.callback_query.message.chat_id != canalid:
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)
                        cursor.execute("SELECT Idmessage FROM relaciones_id where Idevento=?;", (tomado.get_uid()), )
                        idmensaje = cursor.fetchall()
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id, id_mensaje=idmensaje)
                        cursor.execute("DELETE FROM relaciones_id where Idevento=?;", (tomado.get_uid()), )
                        relacion.commit()
                    else:
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)
                        cursor.execute("DELETE FROM relaciones_id where Idevento=?;", (tomado.get_uid(),))
                        relacion.commit()

                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Ha habido un problema a la hora de inscribirse en el evento."
                                                  "Póngase en contacto con un administrador")

            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))
        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()


