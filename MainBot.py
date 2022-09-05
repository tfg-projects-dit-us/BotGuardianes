from telegram.ext import (ExtBot,Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
import logging
import sys
import telegram
import datetime
import pytz
import calendar
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
    logging.getLogger( __name__ ).debug(str(configuracion.configfile))
    tokenbot = configuracion.configfile['telegram']['token_bot']
    servicio_rest.start(
        user=configuracion.configfile['REST']['usuario'],
        contrasena=configuracion.configfile['REST']['contrasena'],
        inserta_id_tel_por_id_rest=configuracion.configfile['REST']['url_insertartelegramID'],
        get_id_por_email=configuracion.configfile['REST']['url_getIDporemail'],
        get_nombre_por_id_rest=configuracion.configfile['REST']['url_getnombreporID'],
        get_id_rest_por_id_tel= configuracion.configfile['REST']['url_getIDrestporIDtel'],
        get_rol_por_email=configuracion.configfile['REST']['url_getrol'],
        get_id_tel_por_id_rest=configuracion.configfile['REST']['url_getTelegramID']
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
        cal_prop=cal_propuestas,
        canal_id=configuracion.configfile['telegram']['canal_id'],
        canal_id_admin=configuracion.configfile['telegram']['canal_id_admin']
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

    botones_handler = CommandHandler('botones', telegram_tools.botones)
    # Añadimos función de guardias disponibles
    gdisp_handler = MessageHandler(Filters.regex('Guardias disponibles'), telegram_tools.guardias_disponibles)
    dispatcher.add_handler(botones_handler)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = MessageHandler(Filters.regex('Guardias propias'), telegram_tools.guardias_propias)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = MessageHandler(Filters.regex('Guardias pendientes'), telegram_tools.guardias_pendientes)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = MessageHandler(Filters.regex('Aprobar o denegar guardias'), telegram_tools.guardias_aprobar_denegar)
    dispatcher.add_handler(gdisp_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_ceder,pattern="ceder")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_tomar,pattern="tomar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_aprobar,pattern="aprobar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_denegar,pattern="denegar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_cancelar,pattern="cancelar")
    dispatcher.add_handler(callback_handler)
    updater.start_polling()


