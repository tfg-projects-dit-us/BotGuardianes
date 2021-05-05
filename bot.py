from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, telegram
tokenbot= None
with open("token.txt") as f:
    tokenbot = f.read().strip()
bot=telegram.Bot(token=tokenbot)

#Creamos una funcion de eco, que repite el mensaje que recibe
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

#Esta funcion recibe un mensaje y cambia sus caracteres por mayusculas
def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)    

#Esta funcion es la que inicia el bot cuando entra en contacto con un usuario
def start(update, context):
    #Aqui creamos el teclado por botones que se le mostraraa al usuario en esta funcion
    kb = [[telegram.KeyboardButton('Boton 1'),telegram.KeyboardButton('Boton 2')],
          [telegram.KeyboardButton('Boton 3'),telegram.KeyboardButton('Boton 4')],
          [telegram.KeyboardButton('Boton 5'),telegram.KeyboardButton('Boton 6')]]

    kb_markup = telegram.ReplyKeyboardMarkup(kb,resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="your message",
                     reply_markup=kb_markup)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
updater = Updater(token=tokenbot, use_context=True)
dispatcher = updater.dispatcher

#La función start se le asigna a la funcion start del bot
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


#Aplico la funcion echo a los mensajes escritos que se reciben
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)
updater.start_polling()

#Anadimos la función de mayusculas al comando /caps del bot
caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

