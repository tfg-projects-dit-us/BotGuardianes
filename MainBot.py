from telegram.ext import (ExtBot,Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
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
from modulos import telegram_tools
from modulos.config import config
from modulos import servicio_rest
from modulos import gestor_calendario


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bot de telegram para gestion de guardias hospitalarias')
    parser.add_argument('--config', help="Fichero de configuracion (Por defecto en config/config.yaml)", type=str, default="config/config.yaml")
    args=parser.parse_args()

    configuracion = config(directorio=args.config)
    logging.getLogger( __name__ ).debug('Cargado fichero de configuracion config.yaml')

    # Este es el token del bot que se ha generado con BotFather.
    logging.getLogger( __name__ ).debug(str(config.configfile))
    tokenbot = configuracion.configfile['telegram']['token_bot']
    servicio_rest.start(
        user=configuracion.configfile['REST']['usuario'],
        contrasena=configuracion.configfile['REST']['contrasena'],
        inserta=configuracion.configfile['REST']['url_insertartelegramID'],
        getID=configuracion.configfile['REST']['url_getIDporemail'],
        getnombre=configuracion.configfile['REST']['url_getnombreporID'],
        getIDrest = configuracion.configfile['REST']['url_getIDtestporIDtel'],
        getRol=configuracion.configfile['REST']['url_getrol']
        )



    logging.getLogger( __name__ ).debug('Cargado token de API REST')
    gestor_calendario.start(
        url_servicio=configuracion.configfile['calendarios']['url_servidor'],
        usuario=configuracion.configfile['calendarios']['usuario'],
        contrasena=configuracion.configfile['calendarios']['contrasena']
    )
    cal_principal=gestor_calendario.Calendario(
        url=configuracion.configfile['calendarios']['url_definitivos']
    )
    cal_propuestas = gestor_calendario.Calendario(
        url=str(configuracion.configfile['calendarios']['url_propuestas'])
    )
    logging.getLogger( __name__ ).debug('Calendarios cargados')
    telegram_tools.start(
        token_bot=tokenbot,
        cal_prim=cal_principal,
        cal_prop=cal_propuestas
    )
    logging.getLogger( __name__ ).debug('Cargado token de Telegram. TokenID= ' + tokenbot)
    print("Calendarios cargados. Iniciado correctamente")
    # Función para calcular el timestamp del primer dia del mes

    # print(cal_principal.events)
    # print(datetime.datetime.now())
    # print(get_fecha_inicio_mes())
    # print(get_fecha_fin_mes())

    updater = Updater(
        token=tokenbot,
        use_context=True
    )
    dispatcher = updater.dispatcher

    # La función registro_paso1 se le asigna a la funcion start del bot. Esta se llama cuando un usuario utiliza el bot por
    # primera vez
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', telegram_tools.registro_paso1)],
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
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_boton)
    dispatcher.add_handler(callback_handler)
    updater.start_polling()
