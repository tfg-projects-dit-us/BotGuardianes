import requests
import logging
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
        logging.getLogger( __name__ ).error("Error insertando el ID de Telegram: " + str(e))
        raise Exception

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
        logging.getLogger( __name__ ).error("Error obteniendo el ID mediante email: " + str(e))
        raise Exception
    return idrest

def GetNombrePorID(id):
    respuesta=None
    nombre=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               ).json()
        logging.getLogger( __name__ ).debug("Respuesta de NombrePorID: " +str(respuesta))
        nombre=str(respuesta.get('firstName')) + " " + str(respuesta.get('lastNames'))
    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).error("Error obteniendo nombre del doctor " + str(e))
        raise Exception

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
        logging.getLogger( __name__ ).error("Error obteniendo id del doctor. " + str(e))
        raise Exception
    return idRest


def GetEmailPorID(id):
    respuesta=None
    email=None
    try:
        respuesta=requests.get(url_getnombre+'/'+str(id),
                               auth=HTTPBasicAuth(usuario,password)
                               ).json()
        logging.getLogger( __name__ ).debug("Respuesta de NombrePorID: " +str(respuesta))
        email=str(respuesta.get('email'))
    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).error("Error obteniendo email del doctor " + str(e))
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
        logging.getLogger( __name__ ).error("Error obteniendo roles del doctor " + str(e))

    finally:
        return roles