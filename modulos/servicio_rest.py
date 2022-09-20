"""
Módulo para agregar manejo del servicio REST para obtener datos del servicio Guardianes

Contiene las variables de módulo:

- `url_inserta`: Contiene la URL para insertar la ID de telegram utilizando la ID de usuario en la BBDD del servicio REST
- `url_getID`: Contiene la URL para obtener la ID del doctor en la BBDD del servicio REST a partir del email
- `url_getnombre`: Contiene la URL para obtener el nombre y apellido del doctor a partir de la ID del doctor en la BBDD del servicio REST
- `url_getIDrestporIDtel`: Contiene la URL para obtener la ID del doctor en la BBDD del servicio REST a partir de la ID de usuario de Telegram
- `url_getroles`: Contiene la URL para obtener los roles de un doctor a partir del correo del doctor
- `url_getIDtelporIDrest`: Contiene la URL para obtener la ID de usuario de Telegram del doctor a partir de la ID en la BBDD del servicio REST
- `usuario`: Usuario para el servicio REST
- `password`: Password para el servicio REST

Estas variables son con acceso de lectura desde cualquier función del módulo.
Para poder escribir en ellas, es necesario declararla como `global` dentro de la función

"""

import requests
import logging
import sys
import ast
from requests.auth import HTTPBasicAuth


url_inserta             :str =None
url_getID               :str =None
url_getnombre           :str =None
url_getIDrestporIDtel   :str =None
url_getroles            :str =None
url_getIDtelporIDrest   :str =None
url_eventos             :str =None
usuario                 :str =None
password                :str =None
def start(user:str, contrasena:str, inserta_id_tel_por_id_rest:str, get_id_por_email:str,
          get_nombre_por_id_rest:str,get_id_rest_por_id_tel:str,
          get_rol_por_email:str,get_id_tel_por_id_rest:str,put_evento:str)->None:
    """
    Función para inicializar  el módulo. Rellena las urls de acceso a la API REST y las credenciales.

    Args:
        user: Usuario para acceder a la API REST
        contrasena: Password para acceder a la API REST
        inserta_id_tel_por_id_rest: URL para insertar la ID de telegram en la BBDD
        get_id_por_email: URL para obtener la ID del servicio REST a partir del email
        get_nombre_por_id_rest: URL para obtener el nombre del doctor a partir de la ID del servicio REST
        get_id_rest_por_id_tel: URL para obtener la ID del servicio REST a partir de la ID de Telegram
        get_rol_por_email: URL para obtener los roles de un doctor a partir de su email
        get_id_tel_por_id_rest: URL para obtener la ID de Telegram a partir de la ID del servicio REST
        put_evento: URL para enviar el evento a la API REST.
    """

    global url_inserta, url_getID,usuario,password,url_getnombre,url_getIDrestporIDtel, url_getroles,url_getIDtelporIDrest,url_eventos
    url_inserta=inserta_id_tel_por_id_rest
    url_getID= get_id_por_email
    url_getnombre=get_nombre_por_id_rest
    url_getIDrestporIDtel=get_id_rest_por_id_tel
    url_getroles=get_rol_por_email
    url_getIDtelporIDrest=get_id_tel_por_id_rest
    url_eventos=put_evento
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

def InsertaTelegramID(idusuario:str|int,chatid:str|int)->str|None:
    """
    Inserta la ID de telegram del usuario, utilizando la ID REST del mismo

    Args:
        idusuario: ID del usuario en el servicio REST
        chatid: ID del usuario en Telegram

    Returns:
        Devuelve el mensaje de ID de Telegram actualizado si se completa, o None si hay un fallo.
    """
    respuesta=None
    try:
        respuesta=requests.put(url_inserta+ '/' + idusuario,
                           auth=HTTPBasicAuth(usuario,
                                              password),
                           headers={'Content-Type': 'text/plain'},
                           data =str(chatid))

    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    if respuesta.status_code ==200:
        return respuesta.text
def GetIDPorEmail(email:str)->str:
    """
    Obteiene la ID del usuario en el servicio REST a partir de su correo electrónico

    Args:
        email: Correo electrónico del usuario

    Returns:
        Devuelve la cadena `Email not found` si no encuentra el correo, o la ID en el servicio REST si lo encontró
    """
    try:
        respuesta=requests.get(url_getID,
                                       auth=HTTPBasicAuth(
                                                   usuario,
                                                   password),
                                       params={'email': email})
        logging.getLogger( __name__ ).debug(respuesta.text)
        idrest=str(respuesta.text)
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    if respuesta.status_code ==200:
        return idrest
    if "Could not fing a doctor" in respuesta.text:
        return "Email not found"


def GetNombrePorID(id:str|int)->str:
    """
    Obtiene el nombre y apellido de un usuario en el servicio REST a partir de su ID

    Args:
        id: ID del usuario en el servicio REST

    Returns:
        El nombre y apellido en caso de encontrar al doctor o el mensaje "Email not found"
    """
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
        logging.getLogger( __name__ ).info("Error obteniendo nombre del doctor " + str(e))
        raise Exception
    if respuesta.status_code==200:
        return nombre
    if "Could not fing a doctor" in respuesta.text:
        return "Email not found"
def GetidRESTPorIDTel(id:str|int)->str:
    """
    Obtiene la ID del servicio REST de un usuario a partir de su ID en Telegram

    Args:
        id: ID de Telegram del usuario

    Returns:
        Obtiene la ID del usuario en el servicio REST o el mensaje "Email not found"
    """
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
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception
    if respuesta.status_code==200:
        return idRest
    if "Could not fing a doctor" in respuesta.text:
        return "Email not found"

def GetEmailPorID(id:str|int)->str|None:
    """
    Obtiene el correo de un usuario a partir de su ID del servicio REST

    Args:
        id: ID del servicio REST del usuario

    Returns:
        Correo del usuario o None en caso contrario
    """
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
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    return email


def GetRolesPorEmail(mail:str)->list[str]:
    """
    Obtiene los roles de un usuario

    Args:
        mail: Correo del usuario

    Returns:
        Lista de roles que tenga el usuario, o lista vacía si no los encuentra.
    """
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
        if "Could not fing a doctor" in respuesta.text:
            return "Email not found"
    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).info("Error obteniendo roles del doctor " + str(e))
        raise Exception

    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))

    finally:
        return roles

def GetidTelPoridREST(id:str|int)->str:
    """
    Obtiene la ID de telegram de un usuario a partir de su ID del servicio REST

    Args:
        id: ID de servicio REST de un usuario

    Returns:
        La ID de Telegram de un usuario, o "Email not found" en caso de no existir.
    """
    respuesta = None
    nombre = None
    idTel='0'
    try:
        respuesta = requests.get(url_getIDtelporIDrest,
                                 auth=HTTPBasicAuth(usuario, password),
                                 params={'id': str(id)}
                                 )
        idTel= str(respuesta.text)
        logging.getLogger(__name__).debug("Respuesta de idRESTPorIDTel: " + str(respuesta.text))
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception
    if respuesta.status_code == 200:
        return idTel
    if "Could not find the doctor" in respuesta.text:
        return "Email not found"


def GetAdmins()->list[str]:
    """
    Obtiene una lista de administradores en la BBDD del servicio REST

    Returns:
        Lista con los correos de los administradores, o lista vacía si no los encuentra.
    """
    respuesta = None
    admines=[]
    try:
        #Obtenemos la respuesta de solicitar los roles
        respuesta = requests.get(url_getroles,
                                 auth=HTTPBasicAuth(usuario, password),
                                    params = {'rol': "Administrador"}
                                 )
        if respuesta.status_code==200:
            admines=respuesta.text.strip('][').split(', ')


        return admines
    except requests.exceptions.HTTPError as e:
        logging.getLogger( __name__ ).info("Error obteniendo roles del doctor " + str(e))
        raise Exception

    except Exception as e:
        logging.getLogger(__name__).error(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
    finally:
        return admines

def SetEvento(evento_data:str):
    """
    Función para enviar el evento final a la API REST para que modifique el calendario de asignaciones

    Args:
        evento_data: Cadena con los datos del evento en formato ical

    Returns:
        (bool) : Verdadero si lo hizo bien, falso si no

    """
    respuesta = None
    try:
        # Obtenemos la respuesta de solicitar los roles
        respuesta = requests.post(url_eventos,
                                 auth=HTTPBasicAuth(usuario, password),
                                 headers={'Content-Type': 'text/plain'},
                                 data=str(evento_data)
                                 )
    except requests.exceptions.HTTPError as e:
        logging.getLogger(__name__).info(
            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
        raise Exception

    if respuesta.status_code == 200:
        return respuesta.text