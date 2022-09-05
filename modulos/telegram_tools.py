"""
Módulo para agregar manejo del servicio de Telegram y aportar funcionalidad para el servicio de Guardianes

Contiene las variables de módulo:

- `bot`: Contiene un objeto tipo telegram.Bot
- `tokenbot`: Contiene una cadena con el token del bot de Telegram
- `cal_principal`: Contiene un objeto gestor_calendario.Calendario que define el calendario principal del servicio
- `cal_propuestas`: Contiene un objeto gestor_calendario.Calendario que define el calendario de propuestas del servicio
- `canalid`: Contiene una cadena con la id del canal de avisos de guardias del servicio
- `canalid_admin`: Contiene una cadena con la id del canal de avisos para administradores

Estas variables son con acceso de lectura desde cualquier función del módulo.
Para poder escribir en ellas, es necesario declararla como global dentro de la función

"""

import datetime
import sys
import logging
import sqlite3
from urllib.parse import urlparse
from functools import wraps
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram

from modulos import gestor_calendario
from modulos import servicio_rest
from operator import attrgetter


bot:            telegram.Bot                =None
tokenbot:       str                         =None
cal_principal:  gestor_calendario.Calendario=None
cal_propuestas: gestor_calendario.Calendario=None
canalid:        str                         =None
canalid_admin:  str                         =None

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
        id_rest=servicio_rest.GetidRESTPorIDTel(id_user)
        if id_rest.isdigit():
            func(*args, **kwargs)
        elif "Email not found" in id_rest:
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
        id_rest=servicio_rest.GetidRESTPorIDTel(id_user)
        if id_rest.isdigit():
            func(*args, **kwargs)
        elif "Email not found" in id_rest:
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
        if id_rest.isdigit():
            email=servicio_rest.GetEmailPorID(id_rest)
            roles=servicio_rest.GetRolesPorEmail(email)
            if "Administrador" in roles:
                    func(*args, **kwargs)
            else:
                args[1].bot.send_message(chat_id=id_user,
                                             text="No tiene el rol adecuado para esta función."
                                                  "Verifique sus permisos con el administrador del sistema")
        if "Email not found" in id_rest:
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
        if id_rest.isdigit():
            email=servicio_rest.GetEmailPorID(id_rest)
            roles=servicio_rest.GetRolesPorEmail(email)
            if "Administrador" in roles:
                    func(*args,**kwargs)
            else:
                args[1].bot.send_message(chat_id=id_user,
                                         text="No tiene el rol adecuado para esta función."
                                              "Verifique sus permisos con el administrador del sistema")
        if "Email not found" in id_rest:
            args[1].bot.send_message(chat_id=id_user,
                                        text="No se encuentra identificado y registrado en la plataforma."
                                             "Por favor, regístrese con la función /start")
    return wrapper

def start(token_bot=None, cal_prim=None,cal_prop=None,canal_id=None,canal_id_admin=None):
    """
    Función de inicialización del bot de Telegram

    Args:
        token_bot: Token de Telegram para autenticar el bot en el sistema de Telegram
        cal_prim: Calendario principal que se utiliza en el servicio de guardias
        cal_prop: Calendario de propuestas de cambio en el servicio de guardias
        canal_id: Id para el canal de publicación de guardias.

    """
    global tokenbot,bot,cal_principal,cal_propuestas,canalid,canalid_admin
    cal_principal=cal_prim
    cal_propuestas=cal_prop
    canalid=canal_id
    canalid_admin=canalid_admin
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
            elif respuesta=="Email not found":
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
                                     text="Ha sido registrado en la plataforma, {}".format(servicio_rest.GetNombrePorID(idusuario)))  # Imprimimos su nombre
                else:
                    context.bot.send_message(chat_id=update.message.chat_id,
                                             text="Ha habido un error en la plataforma\nContacte por favor con soporte")

                botones(update,context)
                return ConversationHandler.END
        except Exception as e:
            context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error en la plataforma\nContacte por favor con soporte")
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return ConversationHandler.END

    else:
        update.message.reply_text("La cadena no tiene un @. Intente de nuevo enviar su correo")
        return 1

@autenticar
def botones(update, context):
    """
    Función para mostrar los botones en el chat que ejecutarán las funciones para el usuario

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    id_user = update.message.chat_id
    id_rest = servicio_rest.GetidRESTPorIDTel(id_user)
    if id_rest.isdigit():
        email = servicio_rest.GetEmailPorID(id_rest)
        roles = servicio_rest.GetRolesPorEmail(email)
        if "Administrador" in roles:
            kb = [
                [
                    telegram.KeyboardButton('Guardias disponibles para solicitar cambio'),
                    telegram.KeyboardButton('Guardias propias')
                ],
                [
                    telegram.KeyboardButton('Guardias pendientes de ser aprobadas o denegadas'),
                ],
                [
                    telegram.KeyboardButton('Aprobar o denegar guardias')
                ]
            ]
        else:
            kb = [
                [
                    telegram.KeyboardButton('Guardias disponibles para solicitar cambio'),
                    telegram.KeyboardButton('Guardias propias')
                ],
                [
                    telegram.KeyboardButton('Guardias pendientes de ser aprobadas o denegadas')
                ]
            ]


    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Seleccione una opcion",
                             reply_markup=kb_markup)

def editar_datos_evento( evento:gestor_calendario.Evento, id_chat:str, id_mensaje:str,accion:str="nada"):
    """
    Función para editar un mensaje de Telegram con los datos de un evento.
    Utilizada para actualizar los mensajes en el canal de publicación de guardias

    Args:
        evento: Evento que se va a actualizar
        id_chat: Identificador del chat donde se edita el mensaje
        id_mensaje: Identificador del mensaje que se va a editar
        accion: Acción que se incluye en el botón que está debajo de la publicación del mensaje,
        que luego interacciona con los retornos
    """
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
    texto = ""
    if accion == "cancelar":
        texto = "Cancelar propuesta de cambio"
    if accion == "tomar":
        texto = "Pedir este turno"
    if accion == "ceder":
        texto = "Ofrecer este turno"
    if accion=="aprobar_denegar":
        texto= "Aprobar este cambio de turno"
    if accion=="intercambiar":
        texto="Intercambiar este turno"

    if modo=="resumen":
        boton_callback = [[telegram.InlineKeyboardButton
                (
                    text="{}".format(texto),
                    callback_data="{};{}".format(accion,evento.get_uid())
                )
                ]]

        cadena = "<b>{}</b>\nFecha: {}\nSitios libres: {}".format(evento.get_summary(), evento.get_fecha_str(),evento.get_sitios_libres())
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
                if evento.get_rol_asistente(asistente)== "REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        if evento.get_cuenta_ofertantes()>0:
            cadena += "\n<i>Ofertantes del turno</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_rol_asistente(asistente)== "OPT-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        if evento.get_cuenta_demandantes() > 0:
            cadena += "\n<i>Demandantes del turno</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_rol_asistente(asistente) == "NON-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)
        cadena += "\nen fecha: <b>{}</b>".format(evento.get_fecha_str())
        boton_callback = [[telegram.InlineKeyboardButton(
            text=texto, callback_data="{};{}".format(accion,evento.get_uid()))]]
        if accion != "nada" and accion!= "aprobar_denegar" and accion!="ceder_intercambiar":
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)

            mensaje=bot.send_message(chat_id=id_chat, text=cadena,
                                 reply_markup=reply_markup,parse_mode="HTML")
        elif accion=="aprobar_denegar":
            boton_callback = [
                [
                    telegram.InlineKeyboardButton(
                        text="Aprobar este cambio de turno", callback_data="{};{}".format("aprobar", evento.get_uid())
                    ),

                    telegram.InlineKeyboardButton(
                        text="Denegar este cambio de turno", callback_data="{};{}".format("denegar", evento.get_uid())
                    )
                ]]
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje = bot.send_message(chat_id=id_chat, text=cadena,
                                       reply_markup=reply_markup, parse_mode="HTML")
        elif accion == "ceder_intercambiar":
            boton_callback = [
                [
                    telegram.InlineKeyboardButton(
                        text="Ceder este turno", callback_data="{};{}".format("ceder", evento.get_uid())
                    ),

                    telegram.InlineKeyboardButton(
                        text="Intercambiar este turno", callback_data="{};{}".format("intercambiar", evento.get_uid())
                    )
                ]]
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje = bot.send_message(chat_id=id_chat, text=cadena,
                                       reply_markup=reply_markup, parse_mode="HTML")
        if accion=="nada":
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, parse_mode="HTML")
    return mensaje.message_id


@autenticar
def guardias_pendientes(update, context):
    """
        Función para obtener las guardias en las que el usuario está demandando turno pero aún no se ha aprobado el cambio.

        Args:
            update: Objeto con parámetros del mensaje que envía el usuario al bot
            context: Objeto con funciones de contexto del bot de telegram

        """
    global cal_principal, cal_propuestas
    reply_markup = []
    lista_botones = []
    cadena = ""
    try:
        idrest = servicio_rest.GetidRESTPorIDTel(update.message.chat_id)
        nombre_usuario = servicio_rest.GetNombrePorID(id=idrest)
        email_usuario = servicio_rest.GetEmailPorID(id=idrest)
        lista_eventos_ofertados = cal_propuestas.get_eventos(attendee=email_usuario,rol="OPT-PARTICIPANT")
        lista_eventos_demandados = cal_propuestas.get_eventos(attendee=email_usuario,rol="NON-PARTICIPANT")

        if lista_eventos_ofertados == [] and lista_eventos_demandados==[]:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay guardias pendientes de ser aprobadas o denegadas")
            logging.getLogger(__name__).debug("No hay guardias pendientes de ser aprobadas o denegadas")
        else:
            for e in lista_eventos_ofertados:
                mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="cancelar")
            for e in lista_eventos_demandados:
                mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="cancelar")

            logging.getLogger(__name__).debug(cadena)

    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")

@autenticar
def guardias_disponibles(update, context):
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
    lista_eventos:list[gestor_calendario.Evento]=cal_propuestas.get_eventos()
    evento_ya_suscrito=0
    try:
        for e in lista_eventos:
            if e.get_comprobar_asistente(servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.message.chat_id)))!=True:
                mostrar_datos_evento("resumen",evento=e,id_chat=update.message.chat_id,accion="tomar")
            else:
                evento_ya_suscrito+=1
        if lista_eventos==[] or evento_ya_suscrito==len(lista_eventos):
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay guardias disponibles")
            logging.getLogger( __name__ ).debug("No hay guardias disponibles")




            logging.getLogger( __name__ ).debug(cadena)

    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")

@autenticar
def guardias_propias(update, context):
    """
    Función para obtener las guardias propias del usuario actualmente establecidas.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas
    # reply_markup=telegram.InlineKeyboardMarkup([])
    cadena = ""
    lista_eventos: list[gestor_calendario.Evento]=[]
    evento_ya_ofrecido=0
    try:
        idrest=servicio_rest.GetidRESTPorIDTel(update.message.chat_id)
        nombre_usuario=servicio_rest.GetNombrePorID(id=idrest)
        email_usuario=servicio_rest.GetEmailPorID(id=idrest)
        lista_eventos=cal_principal.get_eventos(email_usuario)
        # Aqui pediriamos el nombre del usuario a traves de REST, usando el id de Telegram como dato
        #hace falta una función de obtener la ID por la ID de Telegram
        logging.getLogger( __name__ ).debug("El usuario {} ha solicitado sus propias guardias. Fecha actual {}".format(nombre_usuario,datetime.date.today()))


        if lista_eventos == []:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay eventos asignados a usted")
        else:
            for e in lista_eventos:
                evento_aux=cal_propuestas.get_evento(uid_evento=e.get_uid())
                if isinstance(evento_aux,gestor_calendario.Evento):
                    if evento_aux.get_comprobar_asistente(asistente=email_usuario,rol="OPT-PARTICIPANT") == True:
                        logging.getLogger( __name__ ).debug("Evento con el usuario incluido: {}".format(e))
                        mostrar_datos_evento("completo",evento=e,id_chat=update.message.chat_id)
                else:
                    logging.getLogger(__name__).debug("Evento con el usuario incluido: {}".format(e))
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id,accion="ceder_intercambiar")



    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las guardias propias, por favor, póngase en contacto con el administrador"
                             )
@autenticar_admin
def guardias_aprobar_denegar(update, context):
    """
    Función para obtener las guardias que están pendientes de aprobar o denegar y dar la posibilidad de aceptar o denegar el cambio
    Se imprimirán las guardias y se colocarán botones para aprobar o denegar el cambio.


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

        lista_eventos = cal_propuestas.get_eventos(completos=True)
        # Aqui pediriamos el nombre del usuario a traves de REST, usando el id de Telegram como dato
        # hace falta una función de obtener la ID por la ID de Telegram
        logging.getLogger(__name__).debug(
            "El usuario {} ha solicitado las guardias para aprobar o denegar. Fecha actual {}".format(nombre_usuario,
                                                                                                      datetime.date.today()))

        if lista_eventos == []:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay eventos pendientes de aceptar o denegar")
            # key=lambda fecha: e.vobject_instance.vevent.dstart
        for e in lista_eventos:
            logging.getLogger(__name__).debug("Evento para denegar o aprobar: {}".format(e))
            mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="aprobar_denegar")



    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las guardias propias, por favor, póngase en contacto con el administrador"
                             )

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

def notificar_aprobar_propuesta(borrados: list[str], asentados:list[str], evento:gestor_calendario.Evento):
    """
    Función para notificar a los usuarios afectados de un cambio de guardia.

    Args:
        borrados: Usuarios que se borran del evento
        asentados: Usuarios que se agregan al evento
        evento: Evento del que se hace el cambio. Necesario para obtener las fechas y el resumen

    Returns:
        Devuelve verdadero si completa la acción, falso si hay un error

    """
    global bot

    try:

        for borrado in borrados:
            id_chat=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(borrado))
            if id_chat != "Email not found" and id_chat!='0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido aprobado. Ha sido usted excluido de la guardia {} en fecha {}"
                                 .format(evento.get_summary(),evento.get_fecha_str()))
        for asentado in asentados:
            id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(asentado))
            if id_chat != "Email not found" and id_chat != '0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido aprobado. Ha sido usted incluido en la guardia {} en fecha {}"
                                 .format(
                                     evento.get_summary(), evento.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False

def notificar_denegar_propuesta(borrados: list[str], mantenidos:list[str], evento:gestor_calendario.Evento):
    """
    Función para notificar a los usuarios afectados de una denegación de cambio de guardia.

    Args:
        borrados: Usuarios que se borran del evento
        mantenidos: Usuarios que se agregan al evento
        evento: Evento del que se hace el cambio. Necesario para obtener las fechas y el resumen

    Returns:
        Devuelve verdadero si completa la acción, falso si hay un error

    """
    global bot

    try:

        for borrado in borrados:
            id_chat=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(borrado))
            if id_chat != "Email not found" and id_chat!='0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido denegado. Ha sido usted excluido de la guardia {} en fecha {}"
                                 .format(evento.get_summary(),evento.get_fecha_str()))
        for mantenido in mantenidos:
            id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(mantenido))
            if id_chat != "Email not found" and id_chat != '0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido denegado. Se mantiene usted en la guardia {} en fecha {}"
                                 .format(
                                     evento.get_summary(), evento.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False



def cancelar_propuesta_evento(uid,attendee):
    """
    Función para que un usuario pueda cancelar su propuesta de cambio

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a cancelar su propuesta

    Returns:
        Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento_cancelado=cal_propuestas.cancelar_evento(correo_usuario=attendee,uid_evento=uid)

        if isinstance(evento_cancelado,gestor_calendario.Evento):
            return evento_cancelado
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

    La acción es ceder, cambia el rol del usuario a OPT-PARTICIPANT para designar un hueco libre en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect('./relacionesids.sqlite')
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="ceder":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cedido=ceder_evento(uid_evento,correo)

                if isinstance(cedido,gestor_calendario.Evento):
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=update.callback_query.message.message_id)
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Se ha cedido con éxito el evento {} en fecha {}".format(cedido.get_summary(),cedido.get_fecha_str()))
                    cursor.execute(f"""SELECT Idmessage FROM relaciones_id where Idevento="{cedido.get_uid()}";""")
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
def retorno_intercambiar(update, context):
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es intercambiar, cambia el rol del usuario a OPT-PARTICIPANT para designar un hueco libre en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect('./relacionesids.sqlite')
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="intercambiar":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cedido=ceder_evento(uid_evento,correo)

                if isinstance(cedido,gestor_calendario.Evento):
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Se ha ofrecido con éxito el evento {} con fecha {}".format(cedido.get_summary(),cedido.get_fecha_str()))
                    cursor.execute(f"""SELECT Idmessage FROM relaciones_id where Idevento="{cedido.get_uid()}";""")
                    idmensaje = cursor.fetchall()
                    if idmensaje==[]:
                        idmensaje=mostrar_datos_evento("resumen",cedido,canalid,"aceptar_intercambio")
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
def retorno_cancelar(update, context):
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es cancelar, si es un usuario que estaba en NON-PARTICIPANT, lo borra del evento, y si es un usuario OPT-PARTICIPANT, lo vuelve a poner REQ-PARTICIPANT
    En el segundo caso,se evaluará si quedan sitios libres, si no queda ninguno en OPT-PARTICIPANT y se está demandando el turno, se borrará el evento,
    avisando previamente a los usuarios afectados

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect('./relacionesids.sqlite')
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="cancelar":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cancelado=cancelar_propuesta_evento(uid_evento,correo)

                if isinstance(cancelado,gestor_calendario.Evento):
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                   id_mensaje=update.callback_query.message.message_id)
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Se ha cancelado con éxito la propuesta de {} en fecha {}".format(
                                                 cancelado.get_summary(),cancelado.get_fecha_str()
                                                )
                                             )
                    cursor.execute(f"""SELECT Idmessage FROM relaciones_id where Idevento="{cancelado.get_uid()}";""" )
                    idmensaje = cursor.fetchall()
                    if idmensaje==[]:
                        if cancelado.get_sitios_libres()>0:
                            idmensaje=mostrar_datos_evento("resumen",cancelado,canalid,"tomar")
                            cursor.execute(f"""INSERT OR REPLACE INTO  relaciones_id  (Idevento,Idmessage)
                                       VALUES ( COALESCE((SELECT Idevento FROM relaciones_id WHERE Idevento="{cancelado.get_uid()}"),"{cancelado.get_uid()}"),"{idmensaje}");""")
                            relacion.commit()
                        else:
                            """El evento no tiene sitios libres¿se avisa o se borra del calendario?"""
                            pass
                    else:
                        idmensaje=idmensaje[0][0]
                        editar_datos_evento(cancelado,canalid,idmensaje,"tomar")



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
    global cal_principal, cal_propuestas,bot,canalid,canalid_admin
    relacion=sqlite3.connect('./relacionesids.sqlite')
    cursor=relacion.cursor()
    idmensaje=None
    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="tomar":
                correo = servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                tomado=tomar_evento(uid_evento,correo)
                evento=cal_propuestas.get_evento(uid_evento)
                if evento.get_comprobar_asistente(correo):
                    if isinstance(tomado,gestor_calendario.Evento):
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Evento en el que se ha inscrito")
                        mostrar_datos_evento("completo", tomado, update.callback_query.from_user.id, "nada")
                        if tomado.get_sitios_libres()==0:
                            if update.callback_query.message.chat_id!=canalid:
                                borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=update.callback_query.message.message_id)
                                cursor.execute(f"""SELECT Idmessage FROM relaciones_id where Idevento="{tomado.get_uid()}";""")
                                idmensaje=cursor.fetchall()
                                borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=idmensaje)
                                cursor.execute(f"""DELETE FROM relaciones_id where Idevento="{tomado.get_uid()}";""")
                                relacion.commit()

                                context.bot.send_message(chat_id=canalid_admin,text="Se ha hecho una propuesta de cambio para aprobar o denegar.")
                                mostrar_datos_evento("completo",tomado,canalid_admin,accion="aprobar_denegar")
                            else:
                                borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                               id_mensaje=update.callback_query.message.message_id)
                                cursor.execute(f"""DELETE  FROM relaciones_id where Idevento="{tomado.get_uid()}";""")
                                relacion.commit()
                                context.bot.send_message(chat_id=canalid_admin,text="Se ha hecho una propuesta de cambio para aprobar o denegar.")
                                mostrar_datos_evento("completo",tomado,canalid_admin,accion="aprobar_denegar")
                        else:
                            cursor.execute(f"""SELECT Idmessage FROM relaciones_id where Idevento="{tomado.get_uid()}";""")
                            idmensaje = cursor.fetchall()
                            idmensaje = idmensaje[0][0]
                            editar_datos_evento(tomado, canalid, idmensaje, "tomar")
                    else:
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Ha habido un problema a la hora de inscribirse en el evento."
                                                                                                    "Póngase en contacto con un administrador")
                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="No se puede usted inscribir en el evento porque ya está inscrito")

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
def retorno_aprobar(update, context):
    """
    Función para recibir datos del administrador cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es aprobar, toma el evento en el calendario de propuestas, lo coloca en el lugar del calendario principal
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

            if accion == "aprobar":
                correo = servicio_rest.GetEmailPorID(
                    servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                (borrados, asentados, evento) =cal_propuestas.asentar_cambios(uid_evento)

                if isinstance(evento, gestor_calendario.Evento):
                    if cal_principal.set_evento(evento):
                        cal_propuestas.borrar_evento(uid_evento)
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)
                        cadena_borrados=""
                        cadena_asentados=""
                        for borrado in borrados:
                            cadena_borrados="\n- " + servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(borrado)) + cadena_borrados
                        for asentado in asentados:
                            cadena_asentados="\n- " + servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asentado)) + cadena_asentados
                        texto_final="La propuesta de cambio del turno {} con fecha {} ha sido aprobada.\nSe han excluido a los usuarios:\n {} \n\nSe han incluido a los usuarios:\n {}"\
                            .format(evento.get_summary(),evento.get_fecha_str(),cadena_borrados,cadena_asentados)
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                                 text=texto_final)
                        notificar_aprobar_propuesta(borrados,asentados,evento)

                else:
                    logging.getLogger(__name__).debug("El evento {} se ha borrado del calendario de propuestas".format(uid_evento))

            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))



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
                evento=cal_propuestas.get_evento(uid_evento)
                evento_original=cal_principal.get_evento(uid_evento)
                denegado=cal_propuestas.borrar_evento(uid_evento)

                if denegado==True:
                    texto_final="Se ha denegado con éxito el turno. El turno actual queda de la forma siguiente"
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text=texto_final)
                    mostrar_datos_evento("completo", evento_original, update.callback_query.from_user.id, "nada")
                    cal_propuestas.borrar_evento(uid_evento)
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                   id_mensaje=update.callback_query.message.message_id)
                    notificar_denegar_propuesta(borrados=evento.get_asistentes(rol="NON-PARTICIPANT"),mantenidos=evento.get_asistentes(rol="OPT-PARTICIPANT"))


                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Ha habido un problema a la hora de inscribirse en el evento."
                                                  "Póngase en contacto con un administrador")

            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()


