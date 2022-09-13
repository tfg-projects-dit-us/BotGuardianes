"""
Script principal para iniciar la aplicación de BotGuardianes

Desarrollado por Luis Marín Peña
"""
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
    #Se cargan parámetros de entrada. El parámetro de entrada es la localización del archivo de configuración.
    parser = argparse.ArgumentParser(description='Bot de telegram para gestion de guardias hospitalarias')
    parser.add_argument('--config', help="Fichero de configuracion (Por defecto en ./data/config/config.yaml)", type=str, default="./data/config/config.yaml")
    args=parser.parse_args()
    #Se carga el fichero de configuración guardado en yaml y se convierte a un diccionario llamado configuracion
    configuracion = config(directorio=args.config)
    logging.getLogger( __name__ ).debug('Cargado fichero de configuracion config.yaml')
    logging.getLogger( __name__ ).debug(str(configuracion.configfile))

    # Este es el token del bot que se ha generado con BotFather.
    tokenbot = configuracion.configfile['telegram']['token_bot']
    #Se inicializa el módulo de contacto con el servicio rest.
    servicio_rest.start(
        user=configuracion.configfile['REST']['usuario'],
        contrasena=configuracion.configfile['REST']['contrasena'],
        inserta_id_tel_por_id_rest=configuracion.configfile['REST']['url_insertartelegramID'],
        get_id_por_email=configuracion.configfile['REST']['url_getIDporemail'],
        get_nombre_por_id_rest=configuracion.configfile['REST']['url_getnombreporID'],
        get_id_rest_por_id_tel= configuracion.configfile['REST']['url_getIDrestporIDtel'],
        get_rol_por_email=configuracion.configfile['REST']['url_getrol'],
        get_id_tel_por_id_rest=configuracion.configfile['REST']['url_getTelegramID'],
        put_evento=configuracion.configfile['REST']['url_evento']

        )

    logging.getLogger( __name__ ).debug('Cargada API REST')

    #Inicializacion de módulo gestor_calendario
    gestor_calendario.start(
        url_servicio=configuracion.configfile['calendarios']['url_servidor'],
        usuario=configuracion.configfile['calendarios']['usuario'],
        contrasena=configuracion.configfile['calendarios']['contrasena']
    )
    #Se crea objeto calendario principal
    cal_principal=gestor_calendario.Calendario(
        url=configuracion.configfile['calendarios']['url_definitivos']
    )
    #Se crea objeto calendario propuestas

    cal_propuestas = gestor_calendario.Calendario(
        url=str(configuracion.configfile['calendarios']['url_propuestas'])
    )
    logging.getLogger( __name__ ).debug('Calendarios cargados')
    #Inicializacion de telegram_tools.
    telegram_tools.start(
        token_bot=tokenbot,
        cal_prim=cal_principal,
        cal_prop=cal_propuestas,
        canal_id=configuracion.configfile['telegram']['canal_id'],
        canal_id_admin=configuracion.configfile['telegram']['canal_id_admin'],
        path_sqlite=configuracion.configfile['sqlite']['path']
    )
    logging.getLogger( __name__ ).debug('Cargado token de Telegram. TokenID= ' + tokenbot)
    print("Calendarios cargados. Iniciados todos los módulos correctamente")

    #Aquí se carga la función que actualiza lo que recibe el bot por parte de Telegram y por parte del software.
    updater = Updater(
        token=tokenbot,
        use_context=True
    )
    #Este es el despachador del objeto updater.
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
    #Se agrega la función botones como /comando.
    botones_handler = CommandHandler('botones', telegram_tools.botones)
    # Añadimos función de Actividades disponibles
    dispatcher.add_handler(botones_handler)

    gdisp_handler = MessageHandler(Filters.regex('Actividades propias'), telegram_tools.guardias_propias)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = MessageHandler(Filters.regex('Actividades pendientes'), telegram_tools.guardias_pendientes)
    dispatcher.add_handler(gdisp_handler)
    gdisp_handler = MessageHandler(Filters.regex('Aprobar o denegar cambios'), telegram_tools.guardias_aprobar_denegar)
    dispatcher.add_handler(gdisp_handler)

    #Se agregan retornos de botones contextuales de Telegram
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_ceder,pattern="ceder")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_tomar_cesion, pattern="tomar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_aprobar_cesion, pattern="aprobar_cesion")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_denegar_cesion, pattern="denegar_cesion")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_intercambiar,pattern="intercambiar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_cancelar_cesion, pattern="cancelar_cesion")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_permutar,pattern="permutar")
    dispatcher.add_handler(callback_handler)
    callback_handler=CallbackQueryHandler(telegram_tools.retorno_propuesta,pattern="propuesta")
    dispatcher.add_handler(callback_handler)
    #Se comienza a recoger mensajes del bot.
    updater.start_polling()


