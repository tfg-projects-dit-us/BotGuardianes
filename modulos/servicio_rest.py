import requests
import logging
import sys
from requests.auth import HTTPBasicAuth


url_inserta=None
url_getID=None
url_getnombre=None
url_getIDrestporIDtel=None
url_getroles=None
usuario=None
password=None
def start(user=None,contrasena=None,inserta=None,getID=None,getnombre=None,getIDrest=None,getRol=None):
    #La palabra clave global sirve para poder modificar la variable que está fuera del ámbito de esta variable dentro del
    #módulo, no accesible fuera del módulo sin llamar al módulo en sí
    global url_inserta, url_getID,usuario,password,url_getnombre,url_getIDrestporIDtel, url_getroles
    url_inserta=inserta
    url_getID= getID
    url_getnombre=getnombre
    url_getIDrestporIDtel=getIDrest
    url_getroles=getRol
    usuario=user
    password=contrasena
    logging.getLogger( __name__ ).debug("Inicializado el objeto REST con valores: " +
                  " URL_INSERTA: " + url_inserta+
                  " URL_OBTENER: " + url_getID+
                  " URL_GET_NOMBRE " + url_getnombre+
                  " URL_GET_ID" + url_getIDrestporIDtel+
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

    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    if respuesta.status_code ==200:
        return respuesta.text
def GetIDPorEmail(email):
    try:
        respuesta=requests.get(url_getID,
                                       auth=HTTPBasicAuth(
                                                   usuario,
                                                   password),
                                       params={'email': email})
        logging.getLogger( __name__ ).debug(respuesta.text)
        idrest=str(respuesta.text)
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    if respuesta.status_code ==200:
        return idrest
    if "Could not fing a doctor" in respuesta.text:
        return "Email not found"


def GetNombrePorID(id):
    respuesta=None
    nombre=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               )
        respuestajson=respuesta.json()
        logging.getLogger( __name__ ).debug("Respuesta de NombrePorID: " +str(respuestajson))
        nombre=str(respuestajson.get('firstName')) + " " + str(respuestajson.get('lastNames'))
    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).error("Error obteniendo nombre del doctor " + str(e))
        raise Exception
    if respuesta.status_code==200:
        return nombre

def GetidRESTPorIDTel(id):
    respuesta=None
    nombre=None
    try:
        respuesta=requests.get(url_getIDrestporIDtel,
                               auth=HTTPBasicAuth(usuario,password),
                               params={'idTel':str(id)}
                               )
        idRest=str(respuesta.text)
        logging.getLogger( __name__ ).debug("Respuesta de idRESTPorIDTel: " +str(respuesta.text))
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception
    if respuesta.status_code==200:
        return idRest


def GetEmailPorID(id):
    respuesta=None
    email=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               )
        respuestajson=respuesta.json()
        logging.getLogger( __name__ ).debug("Respuesta de NombrePorID: " +str(respuestajson))
        email=str(respuestajson.get('email'))
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    return email

def GetRolesPorEmail(mail):
    respuesta = None
    roles = []
    try:
        respuesta = requests.get(url_getroles + '/' + str(mail),
                                 auth=HTTPBasicAuth(usuario, password)
                                 )
        if respuesta.status_code==200:
            if "Nombre rol=Doctor" in respuesta.text:
                roles.append("Doctor")
            if "Nombre rol=Administrador" in respuesta.text:
                roles.append("Administrador")
            if "Nombre rol=Administrativo" in respuesta.text:
                roles.append("Administrativo")
        logging.getLogger( __name__ ).debug("Respuesta de GetRolesPorEmail: " + str(roles))

    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).error("Error obteniendo roles del doctor " + str(e))
        raise Exception
    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))

    finally:
        return roles