import requests
import logging


url_inserta=None
url_getID=None
usuario=None
password=None
logger=None
def __init__(usuario=None,password=None,logger=None,url_inserta=None,url_getID=None):
    url_inserta=url_inserta
    url_getID= url_getID
    usuario=usuario
    password=password
    logger=logger
    logging.debug("Inicializado el objeto REST con valores: " +
                  " URL_INSERTA: " + url_inserta+
                  " URL_OBTENER: " + url_getID+
                  " USUARIO: " + usuario+
                  " PASSWORD: " + password
                  )

def InsertaTelegramID(self,idusuario,chatid):
    try:
        respuesta=requests.PUT(url_inserta+ '/' + idusuario,
                           auth=HTTPBasicAuth(usuario,
                                              password),
                           data =chatid)

    except Exception as e:
        logging.error("Error insertando el ID de Telegram: " + str(e))

    return respuesta.text
def GetIDPorEmail(email):
    try:
        respuesta=requests.GET(url_getID,
                                       auth=HTTPBasicAuth(
                                                   usuario,
                                                   password),
                                       data={'email': email})
        logging.debug(respuesta.text)
    except Exception as e:
        logging.error("Error obteniendo el ID mediante email: " + str(e))
    return respuesta.text