from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
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
import argparse
from objetos import telegram_tools
from objetos.config import config
from objetos import servicio_rest
from objetos.calendario import calendario

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bot de telegram para gestion de guardias hospitalarias')
    parser.add_argument('--config', help="Fichero de configuracion (Por defecto en config/config.yaml)", type=open)

    configuracion = config(directorio="config/config.yaml")
    logger = config.logger
    logging.debug('Cargado fichero de configuracion config.yaml')
    logging.debug(config.logger)

    # Este es el token del bot que se ha generado con BotFather.
    logging.debug(str(config.configfile))
    tokenbot = configuracion.configfile['telegram']['token_bot']
    servicio_rest.start(user=configuracion.configfile['REST']['usuario'],
                    contrasena=configuracion.configfile['REST']['contrasena'],
                    inserta=configuracion.configfile['REST']['url_insertartelegramID'],
                    getID=configuracion.configfile['REST']['url_getIDporemail'],
                    getnombre=configuracion.configfile['REST']['url_getnombreporid']
                    )



    logging.debug('Cargado token de API REST')
    cal_principal=calendario(url=configuracion.configfile['calendarios']['url_definitivos'], user= configuracion.configfile['calendarios']['usuario'], password=configuracion.configfile['calendarios']['contrasena'])
    cal_propuestas = calendario(url=str(configuracion.configfile['calendarios']['url_propuestas']), user= configuracion.configfile['calendarios']['usuario'], password=configuracion.configfile['calendarios']['contrasena'])
    logging.debug('Calendarios cargados')
    Bot = telegram.Bot(token=tokenbot)
    telegram_tools.start(token_bot=tokenbot, logger=logger, bottelegram=Bot,cal_prim=cal_principal,cal_prop=cal_propuestas)
    logging.debug('Cargado token de Telegram. TokenID= ' + tokenbot)
    print("Calendarios cargados. Iniciado correctamente")
    # Función para calcular el timestamp del primer dia del mes

    # print(cal_principal.events)
    # print(datetime.datetime.now())
    # print(timestampmesinicio())
    # print(timestampmesfinal())

    updater = Updater(token=tokenbot, use_context=True)
    dispatcher = updater.dispatcher

    # La función registro se le asigna a la funcion start del bot. Esta se llama cuando un usuario utiliza el bot por
    # primera vez
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', telegram_tools.registro)],
        fallbacks=[],
        states={
            1: [MessageHandler(Filters.text, telegram_tools.registro_paso2)],
        }
    )
    dispatcher.add_handler(conv_handler)

    botones_handler = CommandHandler('botones', telegram_tools.guardiasdisponibles)
    # Añadimos función de guardias disponibles
    gdisp_handler = CommandHandler('guardias_disponibles', telegram_tools.guardiasdisponibles)
    dispatcher.add_handler(botones_handler)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = CommandHandler('guardias_propias', telegram_tools.guardiaspropias)
    dispatcher.add_handler(gdisp_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.callback)
    dispatcher.add_handler(callback_handler)
    updater.start_polling()
