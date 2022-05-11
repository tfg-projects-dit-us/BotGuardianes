import requests
import logging
from requests.auth import HTTPBasicAuth


url_inserta=None
url_getID=None
url_getnombre=None
usuario=None
password=None
logger=None
def start(user=None,contrasena=None,inserta=None,getID=None,getnombre=None):
    #La palabra clave global sirve para poder modificar la variable que está fuera del ámbito de esta variable dentro del
    #módulo, no accesible fuera del módulo sin llamar al módulo en sí
    global url_inserta, url_getID,usuario,password,url_getnombre
    url_inserta=inserta
    url_getID= getID
    url_getnombre=getnombre
    usuario=user
    password=contrasena
    logging.debug("Inicializado el objeto REST con valores: " +
                  " URL_INSERTA: " + url_inserta+
                  " URL_OBTENER: " + url_getID+
                  " URL_GET_NOMBRE " + url_getnombre+
                  " USUARIO: " + usuario+
                  " PASSWORD: " + password
                  )

def InsertaTelegramID(idusuario,chatid):
    respuesta=None
    try:
        respuesta=requests.put(url_inserta+ '/' + idusuario,
                           auth=HTTPBasicAuth(usuario,
                                              password),
                           headers={'Content-Type': 'text/plain'},
                           data =str(chatid))

    except Exception as e:
        logging.error("Error insertando el ID de Telegram: " + str(e))

    return respuesta.text
def GetIDPorEmail(email):
    try:
        respuesta=requests.get(url_getID,
                                       auth=HTTPBasicAuth(
                                                   usuario,
                                                   password),
                                       params=(('email', email),))
        logging.debug(respuesta.text)
    except Exception as e:
        logging.error("Error obteniendo el ID mediante email: " + str(e))
    return respuesta.text

def GetNombrePorID(id):
    respuesta=None
    nombre=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               ).json()
        logging.debug("Respuesta de NombrePorID: " +str(respuesta))
        nombre=str(respuesta.get('firstName')) + " " + str(respuesta.get('lastNames'))
    except Exception as e:
        logging.error("Error obteniendo nombre del doctor " + str(e))

    return nombre

def GetEmailPorID(id):
    respuesta=None
    email=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               ).json()
        logging.debug("Respuesta de NombrePorID: " +str(respuesta))
        email=str(respuesta.get('email'))
    except Exception as e:
        logging.error("Error obteniendo nombre del doctor " + str(e))

    return email