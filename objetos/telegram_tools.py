import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import librerias.acciones_inicio
import logging
import telegram
import pytz
import calendar
import arrow
import requests
import objetos.servicio_rest


class telegram_tools:
    def __init__(self, token_bot=None, logger=None, bot=None, REST=None):
        self.logger = logger
        self.token_bot = token_bot
        self.REST = REST
        if (bot is None and token_bot is not None):
            self.bot = telegram.Bot(token=self.token_bot)
        else:
            self.bot = bot

    # Creamos una funcion de eco, que repite el mensaje que recibe
    def echo(self, context):
        print(self.logger)
        context.bot.send_message(chat_id=self.effective_chat.id, text=self.message.text)

    # Esta funcion recibe un mensaje y cambia sus caracteres por mayusculas
    def caps(self, context):
        text_caps = ' '.join(context.args).upper()
        context.bot.send_message(chat_id=self.effective_chat.id, text=text_caps)

        # Esta funcion es la que inicia el bot cuando entra en contacto con un usuario

    def registro(self, context):
        context.bot.send_message(chat_id=self.message.chat_id,
                                 text="Introduce tu correo electronico para registrarte en la plataforma",
                                 reply_markup=telegram.ForceReply())
        return 1

    def registro_paso2(self, context):
        if (self.message.reply_to_message.text.contains('@')):

            try:
                # Aqui pedimos a la API Rest la ID del usuario con su email
                respuesta = self.REST.GetIDPorEmail(self.Message.ReplyToMessage.Text)
                idusuario = respuesta.text()
                logging.info(idusuario)
                logging.info(self.effective_chat.id)
                respuesta = self.REST.InsertaTelegramID(idusuario, self.effective_chat.id)

                # Aqui haríamos la consulta a REST para preguntar si existe ese correo electrónico. Si es el caso,
                # enviaríamos el id
                bot.send_message(chat_id=self.message.chat_id,
                                 text="Ha sido registrado en la plataforma, ")  # Imprimimos su nombre

                bot.send_message(chat_id=self.message.chat_id,
                                 text="Su correo no ha sido encontrado en la plataforma.Por favor, consulte al "
                                      "administrador de su sistema para comprobar que sus datos estan adecuadamente "
                                      "agregados")

                kb = [
                    [
                        telegram.KeyboardButton('/guardiasdisponibles'),
                        telegram.KeyboardButton('/guardiaspropias')
                    ],
                    [
                        telegram.KeyboardButton('Boton 3'),
                        telegram.KeyboardButton('Boton 4')
                    ]
                ]

                kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

                bot.send_message(chat_id=self.message.chat_id,
                                 text="Seleccione una opcion",
                                 reply_markup=kb_markup)
                return ConversationHandler.END
            except:
                bot.send_message(chat_id=self.message.chat_id,
                                 text="Ha habido un error en la plataforma")
                logger.error("Error al hacer conexion con la API")
                return ConversationHandler.END

        else:
            self.message.reply_text("La cadena no tiene un @. Intente de nuevo enviar su correo")
            return 1

    # Esta funcion representa las guardias disponibles
    def guardiasdisponibles(self, context):
        reply_markup = []
        lista_botones = [[]]
        cadena = ""
        events = cal_principal.events
        for e in events['items']:
            if timestampmesfinal() > pytz.timezone('Europe/Madrid').localize(
                    datetime.datetime.strptime(e['start']['date'], '%Y-%m-%d')) > timestampmesinicio():
                if list(e['attendees']) == []:
                    lista_botones = lista_botones + [[telegram.InlineKeyboardButton(
                        text=e.name + " - " + str(e['start']['date'].format('DD-MM-YY HH:mm')), callback_data=patata)]]

                    cadena = cadena + "\n" + e['name'] + " en fecha: " + str(e['begin'].format('DD-MM-YY HH:mm'))

        reply_markup = telegram.InlineKeyboardMarkup(lista_botones)
        if cadena == "":
            context.bot.send_message(chat_id=self.message.chat_id, text="No hay guardias disponibles")

        else:
            context.bot.send_message(chat_id=self.message.chat_id, text=cadena, reply_markup=reply_markup)

    def guardiaspropias(self, update, context):
        # reply_markup=telegram.InlineKeyboardMarkup([])
        cadena = ""
        for e in calendario.events:
            if timestampmesfinal() > e.begin.datetime > timestampmesinicio():
                # Aqui pediriamos el nombre del usuario a traves de REST, usando el id de Telegram como dato
                nombre_usuario = "NOMBRE"
                if list(e.attendees)[0].common_name == nombre_usuario:
                    # str(e.begin.format('DD-MM-YY HH:mm'))
                    # reply_markup
                    cadena = cadena + "\n" + e.name + "Asignada a " + list(e.attendees)[
                        0].common_name + " en fecha: " + str(e.begin.format('DD-MM-YY HH:mm'))

        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=cadena
                                 )
