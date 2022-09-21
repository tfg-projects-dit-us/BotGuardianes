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
import random

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
path_sqlite3:   str                         =None

def autenticar(func):
    """
    Método para autenticar usuario al usar las funciones. Verifica si el usuario está inscrito en el servicio REST

    Se utiliza como un decorador

    Args:
        func (function): Función a la que envuelve este método

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
        func (function): Función a la que envuelve este método

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
        func (function): Función a la que envuelve este método

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
        func (function): Función a la que envuelve este método

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

def start(token_bot:str, cal_prim:str,cal_prop:str,canal_id:str,canal_id_admin:str,path_sqlite:str):
    """
    Función de inicialización del bot de Telegram

    Args:
        token_bot: Token de Telegram para autenticar el bot en el sistema de Telegram
        cal_prim: Calendario principal que se utiliza en el servicio de guardias
        cal_prop: Calendario de propuestas de cambio en el servicio de guardias
        canal_id: Id para el canal de publicación de guardias.

    """
    global tokenbot,bot,cal_principal,cal_propuestas,canalid,canalid_admin, path_sqlite3
    cal_principal=cal_prim
    cal_propuestas=cal_prop
    canalid=canal_id
    canalid_admin=canal_id_admin
    tokenbot = token_bot
    path_sqlite3=path_sqlite
    bot = telegram.Bot(token=token_bot)



def registro_paso1(update:telegram.Update, context:telegram.ext.CallbackContext)-> int:
    """
    Primer paso para registrar ID del usuario en Telegram en el servicio REST de Guardianes.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    Returns:
        Devuelve estado actual del registro_paso1. Paso 1 completo
    """
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Introduce tu correo electronico para identificarte en la plataforma",
                             reply_markup=telegram.ForceReply())
    return 1

def registro_paso2(update:telegram.Update, context:telegram.ext.CallbackContext)->int:
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
                                     text="Ha sido identificado en la plataforma, {}".format(servicio_rest.GetNombrePorID(idusuario)))  # Imprimimos su nombre
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
def botones(update:telegram.Update, context:telegram.ext.CallbackContext):
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
                    telegram.KeyboardButton('Actividades propias')
                ],
                [
                    telegram.KeyboardButton('Actividades pendientes de ser aprobadas o denegadas'),
                ],
            ]
        else:
            kb = [
                [
                    telegram.KeyboardButton('Actividades propias')
                ],
                [
                    telegram.KeyboardButton('Actividades pendientes de ser aprobadas o denegadas')
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
        accion: Acción que se incluye en el botón que está debajo de la publicación del mensaje, que luego interacciona con los retornos
    """
    reply_markup = []
    mensaje = None
    if accion == "cancelar_cesion":
        texto = "Cancelar propuesta de cambio"
    if accion == "tomar":
        texto = "Pedir esta actividad cedida"
    if accion == "ceder":
        texto = "Ofrecer esta actividad"
    if accion=="aprobar_denegar":
        texto= "Aprobar este cambio de actividad"
    if accion=="permutar":
        texto="Pedir esta actividad para intercambio"
    if accion=="rechazar":
        texto="Rechazar intercambio"
    if accion=="escoger":
        texto="Escoger esta actividad para intercambio"
    boton_callback = [[telegram.InlineKeyboardButton
                (
                    text="{}".format(texto),
                    callback_data="{};{}".format(accion,evento.get_uid())
                )
                ]]

    cadena = "<b>{}</b>\nFecha: {}\nSitios libres: {}".format(evento.get_summary(), evento.get_fecha_str(),
                                                              evento.get_sitios_libres())
    if accion != "nada":
        reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
        mensaje = bot.editMessageText(chat_id=id_chat,message_id=id_mensaje,text=cadena,reply_markup=reply_markup, parse_mode="HTML")



def mostrar_datos_evento(modo:str, evento:gestor_calendario.Evento, id_chat:str,accion:str="nada",demandante:str="",ofertante:str="")->str:
    """
    Función para presentar datos de un evento en un chat de telegram.

    Envía una mensaje al chat indicado por id_chat con los datos del evento y los botones contextuales si procede.

    Args:
        modo: Modo en el que se presenta el evento:

            ···resumen: Solo muestra nombre, puestos libres y fecha del evento

            ···completo: Muestra nombre, fecha e integrantes del evento

        evento: Objeto gestor_calendario.Evento que contiene los datos del evento a representar.

        id_chat: Identificador del chat donde se van a mostrar los datos del evento
        accion: Accion que se pone en el mensaje de retorno cuando se pulsa un botón de un mensaje con un evento.
                Si la acción es nada, no se pone un botón
    Returns:
        Devuelve la id del mensaje enviado
    """
    reply_markup=[]
    mensaje:telegram.Message=None
    texto = ""
    if accion == "cancelar_cesion":
        texto = "Cancelar propuesta de cambio"
    if accion == "cancelar_intercambio":
        texto = "Cancelar propuesta de intercambio"
    if accion == "tomar":
        texto = "Demandar esta actividad cedida"
    if accion == "ceder":
        texto = "Ofrecer esta actividad"
    if accion=="aprobar_denegar":
        texto= "Aprobar este cambio de actividad"
    if accion=="permutar":
        texto="Demandar esta actividad para intercambio"
    if accion=="intercambiar":
        texto="Ofrecer esta actividad para intercambio"

    if modo=="resumen":
        boton_callback = [[telegram.InlineKeyboardButton
                (
                    text="{}".format(texto),
                    callback_data="{};{}".format(accion,evento.get_uid())
                )
                ]]

        cadena = "<b>{}</b>\nFecha: {}\n".format(evento.get_summary(), evento.get_fecha_str())
        if accion!="nada":
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, reply_markup=reply_markup,parse_mode="HTML")
        else:
            cadena = "Actividad en la que se ha inscrito a la espera de aprobación\n\n" + cadena
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, parse_mode="HTML")

    if modo=="completo":

        cadena = "<b>{}</b>\n".format(evento.get_summary())

        if evento.get_cuenta_asistentes()>0:
            cadena += "<i>Asignado a</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_rol_asistente(asistente)== "REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        if ofertante=="":
            if evento.get_cuenta_ofertantes()>0:
                cadena += "\n<i>Ofertantes de la actividad</i>:\n"
                for asistente in evento.get_asistentes():
                    if evento.get_rol_asistente(asistente)== "OPT-PARTICIPANT":
                        nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                        cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre,asistente)
        else:
            cadena+="\n<i>Ofertante de la actividad</i>:\n"
            nombre=servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante))
            cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, ofertante)
        if demandante=="":
            if evento.get_cuenta_demandantes() > 0:
                cadena += "\n<i>Demandantes de la actividad</i>:\n"
                for asistente in evento.get_asistentes():
                    if evento.get_rol_asistente(asistente) == "NON-PARTICIPANT":
                        nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                        cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)
        else:
            cadena+="\n<i>Demandante de la actividad</i>:\n"
            nombre=servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante))
            cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, demandante)

        cadena += "\nen fecha: <b>{}</b>".format(evento.get_fecha_str())
        boton_callback = [[telegram.InlineKeyboardButton(
            text=texto, callback_data="{};{}".format(accion,evento.get_uid()))]]
        if accion != "nada" and accion!= "aprobar_denegar_cesion" and accion!="ceder_intercambiar":
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)

            mensaje=bot.send_message(chat_id=id_chat, text=cadena,
                                 reply_markup=reply_markup,parse_mode="HTML")
        elif accion=="aprobar_denegar_cesion":
            boton_callback = [
                [
                    telegram.InlineKeyboardButton(
                        text="Aprobar este cambio de actividad", callback_data="{};{}".format("aprobar_cesion", evento.get_uid())
                    ),

                    telegram.InlineKeyboardButton(
                        text="Denegar este cambio de actividad", callback_data="{};{}".format("denegar_cesion", evento.get_uid())
                    )
                ]]
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje = bot.send_message(chat_id=id_chat, text=cadena,
                                       reply_markup=reply_markup, parse_mode="HTML")
        elif accion == "ceder_intercambiar":
            boton_callback = [
                [
                    telegram.InlineKeyboardButton(
                        text="Ceder", callback_data="{};{}".format("ceder", evento.get_uid())
                    ),

                    telegram.InlineKeyboardButton(
                        text="Intercambiar", callback_data="{};{}".format("intercambiar", evento.get_uid())
                    )
                ]]
            reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
            mensaje = bot.send_message(chat_id=id_chat, text=cadena,
                                       reply_markup=reply_markup, parse_mode="HTML")
        if accion=="nada":
            mensaje=bot.send_message(chat_id=id_chat, text=cadena, parse_mode="HTML")
    return mensaje.message_id


@autenticar
def guardias_pendientes(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()
    actividad_encontrada=False
    try:
        idrest = servicio_rest.GetidRESTPorIDTel(update.message.chat_id)
        nombre_usuario = servicio_rest.GetNombrePorID(id=idrest)
        email_usuario = servicio_rest.GetEmailPorID(id=idrest)
        lista_eventos_ofertados = cal_propuestas.get_eventos(attendee=email_usuario,rol="OPT-PARTICIPANT")
        lista_eventos_demandados = cal_propuestas.get_eventos(attendee=email_usuario,rol="NON-PARTICIPANT")

        if lista_eventos_ofertados == [] and lista_eventos_demandados==[]:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay Actividades pendientes de ser aprobadas o denegadas")
            logging.getLogger(__name__).debug("No hay Actividades pendientes de ser aprobadas o denegadas")
        else:
            for e in lista_eventos_ofertados:
                cursor.execute(
                    f"""SELECT accion FROM oferta_demanda where uid_evento="{e.get_uid()}";""")
                accion = cursor.fetchall()[0][0]
                if accion=="ceder":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="cancelar_cesion")
                    actividad_encontrada=True
                elif accion=="intercambiar":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="cancelar_intercambio")
                    actividad_encontrada=True
                elif accion == "enviado":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id,
                                         accion="cancelar_intercambio")
                    actividad_encontrada = True


            for e in lista_eventos_demandados:
                cursor.execute(
                    f"""SELECT accion FROM oferta_demanda where uid_evento="{e.get_uid()}";""")
                accion = cursor.fetchall()[0][0]
                if accion == "ceder":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="cancelar_cesion")
                    actividad_encontrada=True
                elif accion == "intercambiar":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id,
                                         accion="cancelar_intercambio")
                    actividad_encontrada=True
                elif accion == "enviado":
                    mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id,
                                         accion="cancelar_intercambio")
                    actividad_encontrada = True

            if actividad_encontrada==False:
                context.bot.send_message(chat_id=update.message.chat_id,
                                       text="No hay Actividades pendientes de ser aprobadas o denegadas")
                logging.getLogger(__name__).debug("No hay Actividades pendientes de ser aprobadas o denegadas")

            logging.getLogger(__name__).debug(cadena)
        cursor.close()
        relacion.close()
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")
        cursor.close()
        relacion.close()
@autenticar
def guardias_disponibles(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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
                if e.get_asistentes(tipo='INDIVIDUAL'):
                    mostrar_datos_evento("resumen",evento=e,id_chat=update.message.chat_id,accion="tomar")
                if e.get_asistentes(tipo='GROUP'):
                    mostrar_datos_evento("resumen",evento=e,id_chat=update.message.chat_id,accion="intercambiar")
            else:
                evento_ya_suscrito+=1
        if lista_eventos==[] or evento_ya_suscrito==len(lista_eventos):
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay Actividades disponibles")
            logging.getLogger( __name__ ).debug("No hay Actividades disponibles")




            logging.getLogger( __name__ ).debug(cadena)

    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Ha habido un error en la plataforma\nContacte por favor con soporte")

@autenticar
def guardias_propias(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para obtener las Actividades propias del usuario actualmente establecidas.

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
        logging.getLogger( __name__ ).debug("El usuario {} ha solicitado sus propias actividades. Fecha actual {}".format(nombre_usuario,datetime.date.today()))


        if lista_eventos == []:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay actividades asignados a usted")
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



    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las Actividades propias, por favor, póngase en contacto con el administrador"
                             )
@autenticar_admin
def guardias_aprobar_denegar(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para obtener las guardias que están pendientes de aprobar o denegar y dar la posibilidad de aceptar o denegar el cambio

    Se imprimirán las guardias y se colocarán botones para aprobar o denegar el cambio, bajo el mensaje con los datos del evento.


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
            "El usuario {} ha solicitado las actividades para aprobar o denegar. Fecha actual {}".format(nombre_usuario,
                                                                                                      datetime.date.today()))

        if lista_eventos == []:
            context.bot.send_message(chat_id=update.message.chat_id, text="No hay actividades pendientes de aceptar o denegar")
            # key=lambda fecha: e.vobject_instance.vevent.dstart
        for e in lista_eventos:
            logging.getLogger(__name__).debug("Evento para denegar o aprobar: {}".format(e))
            mostrar_datos_evento("completo", evento=e, id_chat=update.message.chat_id, accion="aprobar_denegar_cesion")



    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        context.bot.send_message(chat_id=update.message.chat_id,
                             text="Ha habido un error recogiendo las Actividades, por favor, póngase en contacto con el administrador"
                             )

def ceder_evento(uid:str,attendee:str)->gestor_calendario.Evento|None:
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
        evento_cedido=cal_propuestas.ofertar_evento(correo_usuario=attendee, evento=evento, uid_evento=uid)

        if isinstance(evento_cedido,gestor_calendario.Evento):
            return evento_cedido
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None


def intercambiar_evento(uid:str,attendee:str)->gestor_calendario.Evento|None:
    """
    Función para que un usuario pueda ofertar un intercambio de su participación en una actividad y guardar dicha propuesta en el calendario de propuestas

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a ceder su puesto en una guardia

    Returns:
        Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento=cal_principal.get_evento(uid)
        evento_intercambiado=cal_propuestas.ofertar_evento(correo_usuario=attendee, evento=evento, tipo='GROUP', uid_evento=uid)

        if isinstance(evento_intercambiado,gestor_calendario.Evento):
            return evento_intercambiado
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None


def notificar_aprobar_cesion(borrados: list[str], asentados:list[str], evento:gestor_calendario.Evento)->bool:
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
                                 text="El cambio ha sido aprobado. Ha sido usted excluido de la actividad {} en fecha {}"
                                 .format(evento.get_summary(),evento.get_fecha_str()))
        for asentado in asentados:
            id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(asentado))
            if id_chat != "Email not found" and id_chat != '0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido aprobado. Ha sido usted incluido en la actividad {} en fecha {}"
                                 .format(
                                     evento.get_summary(), evento.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False

def notificar_denegar_cesion(borrados: list[str], mantenidos:list[str], evento:gestor_calendario.Evento)->bool:
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
                                 text="El cambio ha sido denegado. Ha sido usted excluido de la actividad {} en fecha {}"
                                 .format(evento.get_summary(),evento.get_fecha_str()))
        for mantenido in mantenidos:
            id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(mantenido))
            if id_chat != "Email not found" and id_chat != '0':
                bot.send_message(chat_id=id_chat,
                                 text="El cambio ha sido denegado. Se mantiene usted en la actividad {} en fecha {}"
                                 .format(
                                     evento.get_summary(), evento.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False


def notificar_aprobar_propuesta_intercambio(ofertante: str, demandante:str, evento_ofertado:gestor_calendario.Evento, evento_propuesto:gestor_calendario.Evento)->bool:
    """
    Función para notificar a los usuarios afectados de un cambio de guardia.

    Args:
        ofertante: Usuarios que ofrecio el evento ofertado y acepto el propuesto
        demandante: Usuarios que demando el evento ofertado y ofrecio el propuesto
        evento_ofertado: Evento ofertado para intercambio. Necesario para obtener las fechas y el resumen
        evento_propuesto: Evento propuesto para intercambio. Necesario para obtener las fechas y el resumen

    Returns:
        Devuelve verdadero si completa la acción, falso si hay un error

    """
    global bot

    try:


        id_chat=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante))
        if id_chat != "Email not found" and id_chat!='0':
            bot.send_message(chat_id=id_chat,
                             text="El intercambio ha sido aprobado.\n\nHa sido usted excluido de la actividad {} - {}\nHa sido incluido en la actividad {} - {}"
                             .format(evento_ofertado.get_summary(), evento_ofertado.get_fecha_str(),evento_propuesto.get_summary(),evento_propuesto.get_fecha_str()))

        id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante))
        if id_chat != "Email not found" and id_chat != '0':
            bot.send_message(chat_id=id_chat,
                             text="El intercambio ha sido aprobado.\n\nHa sido usted incluido en la actividad {} -{}\nHa sido excluido de la actividad {} - {}"
                             .format(
                                 evento_ofertado.get_summary(), evento_ofertado.get_fecha_str(),evento_propuesto.get_summary(),evento_propuesto.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False

def notificar_denegar_propuesta_intercambio(ofertante: str, demandante:str, evento_ofertado:gestor_calendario.Evento, evento_propuesto:gestor_calendario.Evento)->bool:
    """
    Función para notificar a los usuarios afectados de una denegación de cambio de guardia.

    Args:
        ofertante: Usuarios que ofrecio el evento ofertado y acepto el propuesto
        demandante: Usuarios que demando el evento ofertado y ofrecio el propuesto
        evento_ofertado: Evento ofertado para intercambio. Necesario para obtener las fechas y el resumen
        evento_propuesto: Evento propuesto para intercambio. Necesario para obtener las fechas y el resumen

    Returns:
        Devuelve verdadero si completa la acción, falso si hay un error

    """
    global bot

    try:

        id_chat=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante))
        if id_chat != "Email not found" and id_chat!='0':
            bot.send_message(chat_id=id_chat,
                             text="El cambio ha sido denegado. Mantiene usted su actividad {} - {}".
                             format(evento_ofertado.get_summary(), evento_ofertado.get_fecha_str()))

        id_chat = servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante))
        if id_chat != "Email not found" and id_chat != '0':
            bot.send_message(chat_id=id_chat,
                             text="El cambio ha sido denegado. Mantiene usted su actividad {} - {}"
                             .format(
                                 evento_propuesto.get_summary(), evento_propuesto.get_fecha_str()))
        return True
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        return False



def cancelar_propuesta_evento(uid:str|int,attendee:str)->gestor_calendario.Evento|None:
    """
    Función para que un usuario pueda cancelar su oferta o su demanda

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
def marcar_cambio(uid:str|int,demandante:str,ofertante:str):
    """
    Función para marcar la cesión de ofertante a un demandante

    Args:
        uid: UID del evento a marcar
        demandante: Correo del demandante
        ofertante: Correo del ofertante
    Returns:
        (bool): True si lo marcó con éxito, False si no
    """
    evento = cal_propuestas.get_evento(uid)
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()
    if isinstance(evento, gestor_calendario.Evento):
        ofertantes=evento.get_asistentes(rol='OPT-PARTICIPANT')
        lista=list(ofertantes.keys())

        ofertante_marcado=random.choice(lista)

        cursor.execute(f"""UPDATE  oferta_demanda  SET demandante="{demandante}" WHERE ofertante="{ofertante_marcado}" and uid_evento="{uid}";""")
        relacion.commit()

    cursor.close()
    relacion.close()
def mostrar_propuesta_cesion(evento:gestor_calendario.Evento, demandante:str, ofertante:str= ""):
    """
    Esta función se utiliza para mostrar la propuesta a los administradores para que puedan aprobarla o denegarla.

    Args:
        evento: Evento que se va a mostrar
        demandante:

    Returns:
        (bool): Verdadero si lo hace con éxito, falso si no
    """
    try:
        relacion=sqlite3.connect(path_sqlite3)
        cursor=relacion.cursor()
        cadena = "<b>{}</b> - <i>{}</i>\n".format(evento.get_summary(),evento.get_fecha_str())

        if evento.get_cuenta_asistentes() > 0:
            cadena += "<i>Asignado a</i>:\n"
            for asistente in evento.get_asistentes():
                if evento.get_rol_asistente(asistente) == "REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)
        if ofertante=="":
            cursor.execute(f"""SELECT ofertante FROM oferta_demanda where uid_evento="{evento.get_uid()}" and demandante="{demandante}";""")
            lectura = cursor.fetchall()
            if lectura != []:
                ofertante= lectura[0][0]



        nombre_ofertante = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante))
        nombre_demandante=servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante))
        cadena += "\n<b>{}</b> (<i>{}</i>) cede a\n<b>{}</b> (<i>{}</i>)".format(nombre_ofertante,ofertante,nombre_demandante,demandante)

        boton_callback = [
            [
                telegram.InlineKeyboardButton(
                    text="Aprobar este cambio de actividad", callback_data="{};{}".format("aprobar_cesion", evento.get_uid())
                ),

                telegram.InlineKeyboardButton(
                    text="Denegar este cambio de actividad", callback_data="{};{}".format("denegar_cesion", evento.get_uid())
                )
            ]]
        reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
        mensaje = bot.send_message(chat_id=canalid_admin, text=cadena,
                                   reply_markup=reply_markup, parse_mode="HTML")
        cursor.execute(f"""UPDATE oferta_demanda SET id_mensaje_canal_admins="{mensaje.message_id}" where uid_evento="{evento.get_uid()}" and demandante="{demandante}" and ofertante="{ofertante}";""")
        relacion.commit()

        cursor.close()
        relacion.close()
        return True
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()
        return False


def mostrar_propuesta_intercambio(evento_ofertado: gestor_calendario.Evento,evento_propuesto: gestor_calendario.Evento, demandante: str, ofertante: str ):
    """
    Esta función se utiliza para mostrar la propuesta de intercambio a los administradores para que puedan aprobarla o denegarla.

    Args:
        evento_ofertado: Evento ofertado por el ofertante
        evento_propuesto: Evento propuesto por el demandante
        ofertante: Correo del ofertante
        demandante: Correo del demandante

    """

    try:
        relacion = sqlite3.connect(path_sqlite3)
        cursor = relacion.cursor()
        cadena = "Evento ofertado:\n<b>{}</b> - {}\n".format(evento_ofertado.get_summary(),evento_ofertado.get_fecha_str())

        if evento_ofertado.get_cuenta_asistentes() > 0:
            cadena += "<i>Asignado a</i>:\n"
            for asistente in evento_ofertado.get_asistentes():
                if evento_ofertado.get_rol_asistente(asistente) == "REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)

        nombre_ofertante = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante))
        nombre_demandante = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante))
        cadena += "\n<b>{}</b> (<i>{}</i>) intercambia a\n<b>{}</b> (<i>{}</i>) su participación a cambio de\n".format(nombre_ofertante, ofertante,
                                                                                  nombre_demandante, demandante)

        cadena += "\nEvento propuesto:\n<b>{}</b> - {}\n".format(evento_propuesto.get_summary(),evento_propuesto.get_fecha_str())

        if evento_propuesto.get_cuenta_asistentes() > 0:
            cadena += "<i>Asignado a</i>:\n"
            for asistente in evento_propuesto.get_asistentes():
                if evento_propuesto.get_rol_asistente(asistente) == "REQ-PARTICIPANT":
                    nombre = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(asistente))
                    cadena += " - <b>{}</b> (<i>{}</i>)\n".format(nombre, asistente)




        boton_callback = [
            [
                telegram.InlineKeyboardButton(
                    text="Aprobar este intercambio de actividades",
                    callback_data="{};{}".format("aprobar_intercambio", evento_ofertado.get_uid())
                ),

                telegram.InlineKeyboardButton(
                    text="Denegar este intercambio de actividades",
                    callback_data="{};{}".format("denegar_intercambio", evento_ofertado.get_uid())
                )
            ]]
        reply_markup = telegram.InlineKeyboardMarkup(boton_callback)
        mensaje = bot.send_message(chat_id=canalid_admin, text=cadena,
                                   reply_markup=reply_markup, parse_mode="HTML")
        cursor.execute(
            f"""UPDATE oferta_demanda set uid_evento_propuesta_intercambio="{evento_propuesto.get_uid()}",id_mensaje_canal_admins="{str(mensaje.message_id)}",accion="enviado" WHERE demandante="{demandante}" and ofertante="{ofertante}" and accion="propuestas" and uid_evento="{evento_ofertado.get_uid()}" and id_mensaje_canal_publicaciones is null and uid_evento_propuesta_intercambio is null;""")
        relacion.commit()

        cursor.close()
        relacion.close()
        return True
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()
        return False

def tomar_evento(uid:str,attendee:str):
    """
    Función para que un usuario pueda demandar un puesto en una guardia ofrecida y guardar dicha propuesta en el calendario de propuestas

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a demandar un puesto en una guardia

    Returns:
        (gestor_calendario.Evento|None):Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento=cal_propuestas.get_evento(uid)
        if isinstance(evento,gestor_calendario.Evento):
            evento_tomado=cal_propuestas.tomar_evento(correo_usuario=attendee,uid_evento=uid)

            if  isinstance(evento_tomado,gestor_calendario.Evento):
                return evento_tomado
            else:
                return None
        else:
            return None
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None

def permutar_evento(uid:str,attendee:str):
    """
    Función para que un usuario pueda demandar un puesto en una guardia ofrecida y guardar dicha propuesta en el calendario de propuestas

    Args:
        uid: Identificador único de un evento, que se utilizará para buscar el evento en el calendario
        attendee: Correo del usuario que va a demandar un puesto en una guardia

    Returns:
        (gestor_calendario.Evento|None):Devuelve un Evento si es de clase Evento. En caso de haber excepción devuelve None
    """
    try:
        evento=cal_propuestas.get_evento(uid)
        if isinstance(evento,gestor_calendario.Evento):
            evento_permutado=cal_propuestas.tomar_evento(correo_usuario=attendee,uid_evento=uid,tipo='GROUP')

            if  isinstance(evento_permutado,gestor_calendario.Evento):
                return evento_permutado
            else:
                return None
        else:
            return None
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
        return None


def borrar_mensaje(id_chat:str|int,id_mensaje:str|int)->bool:
    """
    Función para borrar un mensaje cuando se ha cursado la petición de tomar un evento

    Args:
        id_chat: Id del chat de donde se hace la acción de tomar evento
        id_mensaje: ID del mensaje a borrar

    Returns:
        Verdadero si pudo completarlo, falso si no
    """
    terminado:bool=False
    try:
        terminado=bot.deleteMessage(chat_id=id_chat,message_id=id_mensaje)
        return terminado
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
    finally:
        return terminado


def lista_propuestas_seleccionadas(demandante:str, eventos_ya_propuestos:list[str]=[],ofertante:str=""):
    """
    Función para listar las propuestas que el demandante envía a un ofertante de un intercambio

    Args:
        demandante:  Correo del demandante
        eventos_ya_propuestos: Lista de id de eventos ya agregados en la propuesta. Se utiliza para evitar que el demandante pueda incluir un evento varias veces
        ofertante: Correo del ofertante para que no se puedan proponer eventos que el ofertante ya esté participando.

    Returns:
        (telegram.InlineKeyboardMarkup,str) : Devuelve el reply_markup y la cadena de texto del mensaje.
    """
    global cal_principal
    reply_markup:telegram.InlineKeyboardMarkup=[]
    texto:str=""
    try:
        if eventos_ya_propuestos!=[]:
            texto="Propuestas las actividades siguientes\n"
            for id in eventos_ya_propuestos:
                evento=cal_principal.get_evento(uid_evento=id)
                texto+="\n{} en fecha {}".format(evento.get_summary(),evento.get_fecha_str())
        else:
            texto="Escoja una o más actividades y pulse Enviar"
        lista_eventos=cal_principal.get_eventos(demandante)
        fila_botones=[]
        columna_botones=[]
        for evento in lista_eventos:
            if evento.get_uid() not in eventos_ya_propuestos:

                boton=telegram.InlineKeyboardButton(
                        text="{} - {}".format(evento.get_summary(),
                                            evento.get_fecha_str()
                                              ),
                        callback_data="{};{}".format("hacer_propuesta", evento.get_uid())
                        )

                columna_botones.append(list([boton]))


        columna_botones.append([telegram.InlineKeyboardButton(
                text="Deshacer las selecciones", callback_data="{}".format("deshacer_propuesta")
             ), telegram.InlineKeyboardButton(
                text="Enviar las propuestas", callback_data="{}".format("enviar_propuesta")
            )
        ])

        reply_markup = telegram.InlineKeyboardMarkup(columna_botones)

        return reply_markup,texto
    except BaseException as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
                                            format(sys._getframe(1).f_code.co_name,uid_evento,update.callback_query,e ))
@autenticar_retorno
def retorno_ceder(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es ceder, cambia el rol del usuario a OPT-PARTICIPANT para designar un hueco libre en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect(path_sqlite3)
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
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Se ha ofrecido para cesión con éxito el evento {} en fecha {}".format(
                                                cedido.get_summary(),cedido.get_fecha_str()))

                    idmensaje=mostrar_datos_evento("resumen",cedido,canalid,"tomar")
                    cursor.execute(f"""INSERT INTO oferta_demanda  (ofertante,uid_evento,id_mensaje_canal_publicaciones,accion)
                                                               VALUES ( "{correo}","{cedido.get_uid()}",'{idmensaje}',"ceder");""")
                    relacion.commit()



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
def retorno_intercambiar(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.

    Toma una acción a realizar con un evento y su uid.
    La acción es intercambiar, cambia el rol del usuario a OPT-PARTICIPANT para designar un hueco libre en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="intercambiar":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                intercambiado=intercambiar_evento(uid_evento,correo)

                if isinstance(intercambiado,gestor_calendario.Evento):
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,id_mensaje=update.callback_query.message.message_id)
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Se ha ofrecido para intercambio con éxito el evento {} en fecha {}".format(
                                                 intercambiado.get_summary(), intercambiado.get_fecha_str()))

                    idmensaje = mostrar_datos_evento("resumen", intercambiado, canalid, "permutar")

                    cursor.execute(f"""INSERT INTO oferta_demanda  (ofertante,uid_evento,id_mensaje_canal_publicaciones,accion)
                                                                                   VALUES ( "{correo}","{intercambiado.get_uid()}",'{idmensaje}',"intercambiar");""")
                    relacion.commit()



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
def retorno_permutar(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.

    Toma una acción a realizar con un evento y su uid.
    La acción es permutar, el demandante recibe una encuesta con todas sus guardias futuras para proponer algunas de ellas como intercambio.

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas, bot, canalid
    botones=[]
    relacion = sqlite3.connect(path_sqlite3)
    cursor = relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento = update.callback_query.data.split(';')

            if accion == "permutar":
                correo = servicio_rest.GetEmailPorID(
                    servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                permutado = permutar_evento(uid_evento, correo)
                cursor.execute(
                    f"""SELECT ofertante FROM oferta_demanda  where accion="intercambiar" and uid_evento="{uid_evento}" and id_mensaje_canal_publicaciones="{update.callback_query.message.message_id}" and demandante is null;""")
                datos=cursor.fetchall()
                ofertante=datos[0][0]
                if isinstance(permutado, gestor_calendario.Evento):
                    cursor.execute(f"""UPDATE oferta_demanda  set demandante="{correo}",id_mensaje_canal_publicaciones=null,accion="permutar" where uid_evento="{uid_evento}" and id_mensaje_canal_publicaciones="{update.callback_query.message.message_id}" and accion="intercambiar";""")
                    relacion.commit()
                    borrar_mensaje(id_chat=canalid,id_mensaje=update.callback_query.message.message_id)
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Se ha demandado para intercambio el evento {} en fecha {}".format(
                                                 permutado.get_summary(), permutado.get_fecha_str()))

                    reply_markup,texto=lista_propuestas_seleccionadas(correo)
                    mensaje=context.bot.send_message(
                        chat_id=update.callback_query.from_user.id,
                        text=texto,
                        reply_markup=reply_markup
                    )

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

@autenticar_retorno
def retorno_propuesta(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global cal_principal, cal_propuestas, bot, canalid
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento_propuesto = update.callback_query.data.split(';')
            demandante=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(f"""SELECT ofertante,uid_evento from oferta_demanda where accion="permutar" and demandante="{demandante}" and id_mensaje_canal_admins IS NULL and id_mensaje_canal_publicaciones IS NULL;""")
            datos=cursor.fetchall()
            ofertante=datos[0][0]
            uid_evento_ofertado=datos[0][1]
            cursor.execute(
                f"""INSERT INTO propuestas (ofertante,demandante,id_mensaje_chat,uid_evento_ofertado,uid_evento_propuesto ) 
                VALUES("{ofertante}","{demandante}","{update.callback_query.message.message_id}","{uid_evento_ofertado}","{uid_evento_propuesto}") ;""")
            relacion.commit()
            cursor.execute(f"""SELECT uid_evento_propuesto from propuestas 
            where demandante="{demandante}" and ofertante="{ofertante}" and uid_evento_ofertado="{uid_evento_ofertado}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            id_eventos_aux=cursor.fetchall()
            id_eventos=[]
            for id_evento in id_eventos_aux:
                id_eventos.append(id_evento[0])


            reply_markup,texto=lista_propuestas_seleccionadas(demandante, id_eventos)
            context.bot.edit_message_text(chat_id=update.callback_query.from_user.id,message_id=update.callback_query.message.message_id,text=texto,reply_markup=reply_markup)


        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()


@autenticar_retorno
def retorno_propuesta_deshacer(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global cal_principal, cal_propuestas, bot, canalid
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion= update.callback_query.data.split(';')
            demandante=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(f"""SELECT ofertante,uid_evento from oferta_demanda where accion="permutar" and demandante="{demandante}" 
            and id_mensaje_canal_admins IS NULL and id_mensaje_canal_publicaciones IS NULL;""")
            datos=cursor.fetchall()
            ofertante=datos[0][0]
            uid_evento_ofertado=datos[0][1]
            cursor.execute(
                f"""DELETE FROM propuestas where ofertante="{ofertante}" and demandante="{demandante}" and uid_evento_ofertado="{uid_evento_ofertado}" 
                and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            relacion.commit()

            reply_markup, texto = lista_propuestas_seleccionadas(demandante)

            context.bot.edit_message_text(chat_id=str(update.callback_query.from_user.id),
                                          message_id=str(update.callback_query.message.message_id),
                                          text=texto,
                                          reply_markup=reply_markup)


        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))
        cursor.close()
        relacion.close()


@autenticar_retorno
def retorno_propuesta_enviar(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global cal_principal, cal_propuestas, bot, canalid
    relacion = sqlite3.connect(path_sqlite3)
    cursor = relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion= update.callback_query.data.split(';')
            demandante = servicio_rest.GetEmailPorID(
                servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(
                f"""SELECT ofertante,uid_evento from oferta_demanda where accion="permutar" and demandante="{demandante}" 
            and id_mensaje_canal_admins IS NULL and id_mensaje_canal_publicaciones IS NULL;""")
            datos = cursor.fetchall()
            ofertante = datos[0][0]
            uid_evento_ofertado = datos[0][1]
            cursor.execute(f"""SELECT uid_evento_propuesto from propuestas 
                       where demandante="{demandante}" and ofertante="{ofertante}" and uid_evento_ofertado="{uid_evento_ofertado}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            id_eventos_aux = cursor.fetchall()
            id_eventos = []
            for id_evento in id_eventos_aux:
                id_eventos.append(id_evento[0])
            cursor.execute(
                f"""UPDATE oferta_demanda  set accion="propuestas" where uid_evento="{uid_evento_ofertado}" and ofertante="{ofertante}" and demandante="{demandante}" and id_mensaje_canal_admins IS NULL and id_mensaje_canal_publicaciones IS NULL and accion="permutar";""")
            relacion.commit()
            evento_ofertado=cal_principal.get_evento(uid_evento=uid_evento_ofertado)
            texto = "Propuestas las actividades siguientes por el usuario {}\n a cambio de la actividad {} en fecha {}\nEscoja una o rechace las propuestas:\n".format(
                servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante)),
                evento_ofertado.get_summary(),
                evento_ofertado.get_fecha_str()
            )
            fila_botones = []
            columna_botones = []
            for id in id_eventos:
                evento = cal_principal.get_evento(uid_evento=id)
                texto += "\n{} - {}".format(evento.get_summary(), evento.get_fecha_str())
                if len(fila_botones) < 1:
                    fila_botones.append(
                        telegram.InlineKeyboardButton(
                            text="{} - {}".format(evento.get_summary(), evento.get_fecha_str()),
                            callback_data="{};{}".format("aceptar_propuesta", evento.get_uid())
                        )
                    )
                    if id == id_eventos[-1]:
                        columna_botones.append(list(fila_botones))
                else:
                    columna_botones.append(list(fila_botones))
                    fila_botones.clear()
                    fila_botones.append(
                        telegram.InlineKeyboardButton(
                            text="{} - {}".format(evento.get_summary(),
                                                                    evento.get_fecha_str()),
                            callback_data="{};{}".format("aceptar_propuesta", evento.get_uid())
                        )
                    )
                    if id == id_eventos[-1]:
                        columna_botones.append(list(fila_botones))


            columna_botones.append([ telegram.InlineKeyboardButton(
                text="Rechazar las propuestas", callback_data="{};{}".format("rechazar_propuesta", uid_evento_ofertado)
            )])

            reply_markup = telegram.InlineKeyboardMarkup(columna_botones)

            borrar_mensaje(id_chat=update.callback_query.from_user.id,id_mensaje=update.callback_query.message.message_id)
            mensaje = context.bot.send_message(
                chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante)),
                text=texto,
                reply_markup=reply_markup
            )
            cursor.execute(
                f"""UPDATE propuestas set id_mensaje_chat="{mensaje.message_id}" where uid_evento_ofertado="{uid_evento_ofertado}" and ofertante="{ofertante}" and demandante="{demandante}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            relacion.commit()

        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))
        cursor.close()
        relacion.close()

@autenticar_retorno
def retorno_aceptar_propuesta(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global cal_principal, cal_propuestas, bot, canalid
    relacion = sqlite3.connect(path_sqlite3)
    cursor = relacion.cursor()
    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion,uid_evento_aceptado= update.callback_query.data.split(';')
            ofertante=servicio_rest.GetEmailPorID(
                servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(f"""SELECT uid_evento_ofertado,demandante from propuestas 
                       where ofertante="{ofertante}" and uid_evento_propuesto="{uid_evento_aceptado}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            datos= cursor.fetchall()
            uid_evento_ofertado=datos[0][0]
            demandante=datos[0][1]

            mostrar_propuesta_intercambio(cal_principal.get_evento(uid_evento=uid_evento_ofertado),cal_principal.get_evento(uid_evento=uid_evento_aceptado),demandante=demandante,ofertante=ofertante)
            borrar_mensaje(id_chat=update.callback_query.from_user.id,id_mensaje=update.callback_query.message.message_id)
            cursor.execute(f"""DELETE FROM propuestas 
                                  where demandante="{demandante}" and ofertante="{ofertante}" and uid_evento_ofertado="{uid_evento_ofertado}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            relacion.commit()





        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))
        cursor.close()
        relacion.close()


@autenticar_retorno
def retorno_rechazar_propuesta(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global cal_principal, cal_propuestas, bot, canalid
    relacion = sqlite3.connect(path_sqlite3)
    cursor = relacion.cursor()
    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion,uid_evento_ofertado= update.callback_query.data.split(';')
            ofertante = servicio_rest.GetEmailPorID(
                servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(f"""SELECT demandante from oferta_demanda 
                                   where ofertante="{ofertante}" and uid_evento="{uid_evento_ofertado}" and accion="propuestas" and id_mensaje_canal_admins is null and id_mensaje_canal_publicaciones is null;""")
            datos = cursor.fetchall()
            demandante = datos[0][0]
            evento_demandante_rechazado=cancelar_propuesta_evento(uid_evento_ofertado,demandante)
            borrar_mensaje(id_chat=update.callback_query.from_user.id,
                           id_mensaje=update.callback_query.message.message_id)
            texto="Sus propuestas para la oferta de intercambio <b>{}</b> - <i>{}</i> han sido rechazadas.".format(evento_demandante_rechazado.get_summary(),evento_demandante_rechazado.get_fecha_str())
            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante)),
                                     text=texto,
                                     parse_mode="HTML")

            idmensaje = mostrar_datos_evento("resumen", evento_demandante_rechazado, canalid, "permutar")

            cursor.execute(f"""UPDATE oferta_demanda set demandante=null,id_mensaje_canal_publicaciones="{idmensaje}",accion="intercambiar" where uid_evento="{uid_evento_ofertado}" and ofertante="{ofertante}" and demandante="{demandante}" and id_mensaje_canal_publicaciones is null and accion="propuestas";""")
            relacion.commit()

            cursor.execute(f"""DELETE FROM propuestas 
                                              where demandante="{demandante}" and ofertante="{ofertante}" and uid_evento_ofertado="{uid_evento_ofertado}" and id_mensaje_chat="{update.callback_query.message.message_id}";""")
            relacion.commit()

        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))
        cursor.close()
        relacion.close()


@autenticar_retorno
def retorno_cancelar_cesion(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.

    Toma una acción a realizar con un evento y su uid.

    La acción es cancelar, si es un usuario que estaba en NON-PARTICIPANT, lo borra del evento, y si es un usuario OPT-PARTICIPANT, lo vuelve a poner REQ-PARTICIPANT
    En el segundo caso,se evaluará si quedan sitios libres, si no queda ninguno en OPT-PARTICIPANT y se está demandando el turno, se borrará el evento,
    avisando previamente a los usuarios afectados

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="cancelar_cesion":
                correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                cursor.execute(
                    f"""SELECT ofertante,demandante,id_mensaje_canal_publicaciones,id_mensaje_canal_admins,accion FROM oferta_demanda where uid_evento="{uid_evento}";""")
                resultado=cursor.fetchall()
                if resultado!=[]:
                    ofertante=resultado[0][0]
                    demandante=resultado[0][1]
                    id_mensaje_canal_publicaciones=resultado[0][2]
                    id_mensaje_canal_admins=resultado[0][3]
                    accion=resultado[0][4]

                if demandante is not None:
                    if demandante == correo:
                        cancelado=cancelar_propuesta_evento(uid_evento,demandante)

                    elif ofertante == correo:
                        cancelado=cancelar_propuesta_evento(uid_evento,demandante)
                        cancelado=cancelar_propuesta_evento(uid_evento,ofertante)

                elif ofertante==correo:
                    cancelado=cancelar_propuesta_evento(uid_evento,ofertante)

                if isinstance(cancelado,gestor_calendario.Evento):
                    if id_mensaje_canal_admins is not None:
                        borrar_mensaje(id_chat=canalid_admin,id_mensaje=id_mensaje_canal_admins)

                    if id_mensaje_canal_publicaciones is not None:
                        borrar_mensaje(id_chat=canalid,id_mensaje=id_mensaje_canal_publicaciones)


                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)

                    if demandante is not None:
                        if demandante == correo:
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante)),
                                                     text="Se ha cancelado la propuesta de cesión. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            idmensaje = mostrar_datos_evento("resumen", cancelado, canalid, "tomar")
                            cursor.execute(
                                f"""UPDATE oferta_demanda set id_mensaje_canal_admins=null,demandante=null,id_mensaje_canal_publicaciones="{idmensaje}" where uid_evento="{uid_evento}" and ofertante="{ofertante}" and accion="ceder" and demandante="{correo}";""")
                            relacion.commit()
                        elif ofertante == correo:
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante)),
                                                     text="Se ha cancelado la propuesta de cesión. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante)),
                                                     text="Se ha cancelado la propuesta de cesión. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            cursor.execute(
                                f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and demandante="{demandante}"and accion="ceder";""")
                            relacion.commit()
                    elif ofertante == correo:
                        context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante)),
                                                 text="Se ha cancelado la propuesta de cesión. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                     cancelado.get_summary(), cancelado.get_fecha_str())
                                                 )
                        cursor.execute(
                            f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and accion="ceder";""")
                        relacion.commit()


                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="No se pudo cancelar con éxito la propuesta de {} en fecha {}, dado que la oferta ya no existe".format(
                                                 cancelado.get_summary(),cancelado.get_fecha_str()
                                                )
                                             )


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
def retorno_tomar_cesion(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.
    Toma una acción a realizar con un evento y su uid

    La acción es tomar, añade al usuario con el rol NON-PARTICIPANT al evento en el calendario de propuestas

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid,canalid_admin
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()
    idmensaje=None
    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')

            if accion=="tomar":
                correo = servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))

                evento=cal_principal.get_evento(uid_evento)
                if evento.get_comprobar_asistente(correo) != True:
                    tomado = tomar_evento(uid_evento, correo)
                    if isinstance(tomado,gestor_calendario.Evento):
                        cursor.execute(
                            f"""SELECT ofertante FROM oferta_demanda where uid_evento="{tomado.get_uid()}"and demandante IS NULL and accion="ceder" and id_mensaje_canal_publicaciones="{update.callback_query.message.message_id}";""")
                        datos = cursor.fetchall()
                        ofertante=datos[0][0]
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,text="Evento en el que se ha inscrito")
                        mostrar_datos_evento("completo", tomado, update.callback_query.from_user.id, "nada",demandante=correo,ofertante=ofertante)

                        borrar_mensaje(id_chat=canalid,id_mensaje=update.callback_query.message.message_id)
                        cursor.execute(
                            f"""UPDATE oferta_demanda set id_mensaje_canal_publicaciones=null,demandante="{correo}" where uid_evento="{tomado.get_uid()}"and demandante IS NULL and accion="ceder" and ofertante="{ofertante}";""")
                        relacion.commit()
                        mostrar_propuesta_cesion(tomado, demandante=correo, ofertante=ofertante)



                    else:
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,text="No puede demandar este evento porque ya está inscrito en él o no hay puestos libres")
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
def retorno_aprobar_cesion(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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
            accion, uid_evento= update.callback_query.data.split(';')

            if accion == "aprobar_cesion":
                correo = servicio_rest.GetEmailPorID(
                    servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
                evento=cal_propuestas.get_evento(uid_evento)
                relacion = sqlite3.connect(path_sqlite3)
                cursor = relacion.cursor()
                cursor.execute(
                    f"""SELECT ofertante,demandante FROM oferta_demanda where uid_evento="{evento.get_uid()}" and id_mensaje_canal_admins="{update.callback_query.message.message_id}" and accion="ceder";""")
                lectura = cursor.fetchall()

                ofertante = lectura[0][0]
                demandante=lectura[0][1]




                evento.asienta_asistentes(ofertante=ofertante,demandante=demandante)

                if isinstance(evento, gestor_calendario.Evento):
                    evento_modificado=cal_principal.get_evento(uid_evento)
                    evento_modificado.set_asistente(demandante,'REQ-PARTICIPANT')
                    evento_modificado.borrar_asistente(ofertante)
                    if cal_principal.set_evento(evento_modificado):
                        if evento.get_cuenta_ofertantes()==0:
                            cal_propuestas.borrar_evento(uid_evento)
                        borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)

                        texto_final="La propuesta de cambio de la actividad <b>{}</b> con fecha <i>{}</i> ha sido aprobada.\nSe ha excluido a {} \n\nSe ha incluido a {}"\
                            .format(evento.get_summary(),evento.get_fecha_str(),
                                    servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante)),servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante)))
                        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                                 text=texto_final, parse_mode="HTML")
                        notificar_aprobar_cesion([ofertante], [demandante], evento_modificado)
                        servicio_rest.SetEvento(evento_modificado.get_data())

                else:
                    logging.getLogger(__name__).debug("El evento {} se ha borrado del calendario de propuestas".format(uid_evento))

                cursor.execute(f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{ofertante}" and demandante="{demandante}";""")
                relacion.commit()
                cursor.close()
                relacion.close()
            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))



@autenticar_retorno_admin
def retorno_denegar_cesion(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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

            if accion == "denegar_cesion":
                evento=cal_propuestas.get_evento(uid_evento)
                evento_original=cal_principal.get_evento(uid_evento)

                relacion = sqlite3.connect(path_sqlite3)
                cursor = relacion.cursor()
                cursor.execute(
                    f"""SELECT ofertante,demandante FROM oferta_demanda where uid_evento="{evento.get_uid()}" and id_mensaje_canal_admins="{update.callback_query.message.message_id}" and accion="ceder";""")
                lectura = cursor.fetchall()

                ofertante = lectura[0][0]
                demandante=lectura[0][1]



                if(evento.negar_cambio_asistentes(ofertante=ofertante,demandante=demandante)):
                    resultado = cal_propuestas.set_evento(evento)

                if resultado==True:
                    texto_final="Se ha denegado con éxito la cesión de <b>{}</b> con fecha <i>{}</i>".format(evento.get_summary(),evento.get_fecha_str())
                    if evento.get_cuenta_ofertantes()==0:
                        cal_propuestas.borrar_evento(evento.get_uid())

                    notificar_denegar_cesion(borrados=list([demandante]), mantenidos=list([ofertante]), evento=evento)
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,text=texto_final,parse_mode="HTML")
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                   id_mensaje=update.callback_query.message.message_id)



                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="Ha habido un problema a la hora de inscribirse en el evento."
                                                  "Póngase en contacto con un administrador")
                cursor.execute(f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{ofertante}" and demandante="{demandante}";""")
                relacion.commit()
                cursor.close()
                relacion.close()
            logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                              format(uid_evento, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento, update.callback_query, e))
        cursor.close()
        relacion.close()
@autenticar_retorno_admin
def retorno_aprobar_intercambio(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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
            accion, uid_evento_ofertado= update.callback_query.data.split(';')

            evento_ofertado=cal_propuestas.get_evento(uid_evento_ofertado)
            relacion = sqlite3.connect(path_sqlite3)
            cursor = relacion.cursor()
            cursor.execute(
                f"""SELECT ofertante,demandante,uid_evento_propuesta_intercambio FROM oferta_demanda where uid_evento="{evento_ofertado.get_uid()}" and id_mensaje_canal_admins="{update.callback_query.message.message_id}" and accion="enviado";""")
            lectura = cursor.fetchall()

            ofertante = lectura[0][0]
            demandante=lectura[0][1]
            uid_evento_propuesto=lectura[0][2]




            evento_ofertado.asienta_asistentes(ofertante=ofertante,demandante=demandante)
            evento_propuesto=cal_principal.get_evento(uid_evento=uid_evento_propuesto)

            if isinstance(evento_ofertado, gestor_calendario.Evento):
                evento_modificado=cal_principal.get_evento(uid_evento_ofertado)
                evento_modificado.set_asistente(demandante,'REQ-PARTICIPANT')
                evento_modificado.borrar_asistente(ofertante)
                evento_propuesto.set_asistente(ofertante,'REQ-PARTICIPANT')
                evento_propuesto.borrar_asistente(demandante)
                if cal_principal.set_evento(evento_modificado) and cal_principal.set_evento(evento_propuesto):
                    if evento_ofertado.get_cuenta_ofertantes()==0:
                        cal_propuestas.borrar_evento(uid_evento_ofertado)
                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                   id_mensaje=update.callback_query.message.message_id)

                    texto_final="La propuesta de intercambio ha sido aprobada.\nLa actividad <b>{}</b> - <i>{}</i> ofertada por <b>{}</b>\n" \
                                "Intercambiada por la actividad <b>{}</b> - <i>{}</i> propuesta por <b>{}</b>"\
                        .format(evento_ofertado.get_summary(),evento_ofertado.get_fecha_str(),
                                servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante)),
                                evento_propuesto.get_summary(),
                                evento_propuesto.get_fecha_str()
                                ,servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante)))
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text=texto_final, parse_mode="HTML")
                    notificar_aprobar_propuesta_intercambio(ofertante,demandante,evento_modificado,evento_propuesto)
                    servicio_rest.SetEvento(evento_modificado.get_data())
                    servicio_rest.SetEvento(evento_propuesto.get_data())

            else:
                logging.getLogger(__name__).debug("El evento {} se ha borrado del calendario de propuestas".format(uid_evento_ofertado))

            cursor.execute(f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento_ofertado}" and ofertante="{ofertante}" and demandante="{demandante}" and uid_evento_propuesta_intercambio="{uid_evento_propuesto}";""")
            relacion.commit()
            cursor.close()
            relacion.close()
        logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                          format(uid_evento_ofertado, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))



@autenticar_retorno_admin
def retorno_denegar_intercambio(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
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
            accion, uid_evento_ofertado = update.callback_query.data.split(';')

            correo = servicio_rest.GetEmailPorID(
                servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            evento_ofertado = cal_propuestas.get_evento(uid_evento_ofertado)
            relacion = sqlite3.connect(path_sqlite3)
            cursor = relacion.cursor()
            cursor.execute(
                f"""SELECT ofertante,demandante,uid_evento_propuesta_intercambio FROM oferta_demanda where uid_evento="{evento_ofertado.get_uid()}" and id_mensaje_canal_admins="{update.callback_query.message.message_id}" and accion="enviado";""")
            lectura = cursor.fetchall()

            ofertante = lectura[0][0]
            demandante = lectura[0][1]
            uid_evento_propuesto = lectura[0][2]
            evento_propuesto=cal_principal.get_evento(uid_evento=uid_evento_propuesto)
            nombre_ofertante=servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(ofertante))
            nombre_demandante = servicio_rest.GetNombrePorID(servicio_rest.GetIDPorEmail(demandante))

            if(evento_ofertado.negar_cambio_asistentes(ofertante=ofertante,demandante=demandante)):
                resultado = cal_propuestas.set_evento(evento_ofertado)

            if resultado==True:
                texto_final="Se ha denegado con éxito el intercambio de\n{} - {} ofertado por {} y \n{} - {} propuesto por {} "\
                    .format(evento_ofertado.get_summary(),evento_ofertado.get_fecha_str(),nombre_ofertante,evento_propuesto.get_summary(),evento_propuesto.get_fecha_str(),nombre_demandante)
                if evento_ofertado.get_cuenta_ofertantes()==0:
                    cal_propuestas.borrar_evento(evento_ofertado.get_uid())

                notificar_denegar_propuesta_intercambio(demandante=demandante,ofertante=ofertante,evento_propuesto=evento_propuesto,evento_ofertado=evento_ofertado)
                context.bot.send_message(chat_id=update.callback_query.from_user.id,text=texto_final)
                borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                               id_mensaje=update.callback_query.message.message_id)

                cursor.execute(
                    f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento_ofertado}" and ofertante="{ofertante}" and demandante="{demandante}" and uid_evento_propuesta_intercambio="{uid_evento_propuesto}";""")
                relacion.commit()

            else:
                context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                         text="Ha habido un problema a la hora de inscribirse en el evento."
                                              "Póngase en contacto con un administrador")

            cursor.close()
            relacion.close()
        logging.getLogger(__name__).debug("UID del evento es:{} por el usuario {}".
                                          format(uid_evento_ofertado, update.callback_query.from_user.id))

    except BaseException as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
            format(sys._getframe(1).f_code.co_name, uid_evento_ofertado, update.callback_query, e))
        cursor.close()
        relacion.close()

@autenticar_retorno
def retorno_cancelar_intercambio(update:telegram.Update, context:telegram.ext.CallbackContext)->None:
    """
    Función para recibir datos del usuario cuando aprieta botones integrados en el propio chat y tratarlos adecuadamente.

    Toma una acción a realizar con un evento y su uid.

    La acción es cancelar, si es un usuario que estaba en NON-PARTICIPANT, lo borra del evento, y si es un usuario OPT-PARTICIPANT, lo vuelve a poner REQ-PARTICIPANT
    En el segundo caso,se evaluará si quedan sitios libres, si no queda ninguno en OPT-PARTICIPANT y se está demandando el turno, se borrará el evento,
    avisando previamente a los usuarios afectados

    Args:
        update: Objeto con parámetros del mensaje que envía el usuario al bot
        context: Objeto con funciones de contexto del bot de telegram

    """
    global cal_principal, cal_propuestas,bot,canalid
    relacion=sqlite3.connect(path_sqlite3)
    cursor=relacion.cursor()

    try:
        if update.callback_query.answer():
            logging.getLogger(__name__).debug("Callback: " + update.callback_query.data)
            accion, uid_evento=update.callback_query.data.split(';')


            correo=servicio_rest.GetEmailPorID(servicio_rest.GetidRESTPorIDTel(update.callback_query.from_user.id))
            cursor.execute(
                f"""SELECT ofertante,demandante,id_mensaje_canal_publicaciones,id_mensaje_canal_admins,accion FROM oferta_demanda where uid_evento="{uid_evento}";""")
            resultado=cursor.fetchall()
            if resultado!=[]:
                ofertante=resultado[0][0]
                demandante=resultado[0][1]
                id_mensaje_canal_publicaciones=resultado[0][2]
                id_mensaje_canal_admins=resultado[0][3]
                accion=resultado[0][4]
            if accion=="intercambiar" or accion=="enviado":
                if demandante is not None:
                    if demandante == correo:
                        cancelado=cancelar_propuesta_evento(uid_evento,demandante)
                    elif ofertante == correo:
                        cancelado=cancelar_propuesta_evento(uid_evento,demandante)
                        cancelado=cancelar_propuesta_evento(uid_evento,ofertante)

                elif ofertante==correo:
                    cancelado=cancelar_propuesta_evento(uid_evento,ofertante)

                if isinstance(cancelado,gestor_calendario.Evento):
                    if id_mensaje_canal_admins is not None:
                        borrar_mensaje(id_chat=canalid_admin,id_mensaje=id_mensaje_canal_admins)

                    if id_mensaje_canal_publicaciones is not None:
                        borrar_mensaje(id_chat=canalid,id_mensaje=id_mensaje_canal_publicaciones)


                    borrar_mensaje(id_chat=update.callback_query.message.chat_id,
                                       id_mensaje=update.callback_query.message.message_id)

                    if demandante is not None:
                        if demandante == correo:
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante)),
                                                     text="Se ha cancelado la propuesta de intercambio. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            idmensaje = mostrar_datos_evento("resumen", cancelado, canalid, "permutar")
                            cursor.execute(
                                f"""UPDATE oferta_demanda set id_mensaje_canal_admins=null,demandante=null,uid_evento_propuesta_intercambio=null,id_mensaje_canal_publicaciones="{idmensaje}",accion="intercambiar" where uid_evento="{uid_evento}" and ofertante="{ofertante}" and demandante="{correo}";""")
                            relacion.commit()
                        elif ofertante == correo:
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(demandante)),
                                                     text="Se ha cancelado la propuesta de intercambio. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante)),
                                                     text="Se ha cancelado la propuesta de intercambio. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                         cancelado.get_summary(), cancelado.get_fecha_str())
                                                     )
                            cursor.execute(
                                f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and demandante="{demandante}"and accion="intercambiar";""")
                            cursor.execute(
                                f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and demandante="{demandante}"and accion="enviado";""")
                            relacion.commit()
                    elif ofertante == correo:
                        context.bot.send_message(chat_id=servicio_rest.GetidTelPoridREST(servicio_rest.GetIDPorEmail(ofertante)),
                                                 text="Se ha cancelado la propuesta de intercambio. Ha sido usted excluido de la propuesta de {} en fecha {}".format(
                                                     cancelado.get_summary(), cancelado.get_fecha_str())
                                                 )
                        cursor.execute(
                            f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and accion="intercambiar";""")
                        cursor.execute(
                            f"""DELETE FROM oferta_demanda where uid_evento="{uid_evento}" and ofertante="{correo}" and accion="enviado";""")
                        relacion.commit()


                else:
                    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                             text="No se pudo cancelar con éxito la propuesta  {} en fecha {}, dado que la oferta ya no existe".format(
                                                 cancelado.get_summary(),cancelado.get_fecha_str()
                                                )
                                             )
            else:
                context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                         text="No se puede cancelar esta propuesta actualmente hasta que se decidan las propuestas.".format(
                                             cancelado.get_summary(), cancelado.get_fecha_str()
                                         )
                                         )


            logging.getLogger( __name__ ).debug("UID del evento es:{} por el usuario {}".
                                                format(uid_evento,update.callback_query.from_user.id))
        cursor.close()
        relacion.close()
    except BaseException as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. UID del evento:{}. Valor de Callback_query: {}. Motivo: {}".
                                            format(sys._getframe(1).f_code.co_name,uid_evento,update.callback_query,e ))
        cursor.close()
        relacion.close()


