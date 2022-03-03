import requests
import logging

class servicio_rest(object):
    def __init__(self,usuario=None,password=None,logger=None,url_inserta=None,url_getID=None):
        self.url_inserta=url_inserta 
        self.url_getID= url_getID
        self.usuario=usuario
        self.password=password
        self.logger=logger
        logging.debug("Inicializado el objeto REST con valores: " +
                      "URL_INSERTA: " + self.url_inserta+
                      "URL_OBTENER: " + self.url_getID+
                      "USUARIO: " + self.usuario+
                      "PASSWORD: " + self.password
                      )

    def InsertaTelegramID(self,idusuario,chatid):
        try:
            respuesta=requests.PUT(self.url_inserta+ '/' + idusuario, 
                               auth=HTTPBasicAuth(self.usuario,
                                                  self.password),
                               data =chatid)
        except Exception as e:
            logging.error("Error insertando el ID de Telegram: " + str(e))

        return respuesta
    def GetIDPorEmail(self,email):
        try:
            respuesta=requests.GET(self.url_getID,
                                           auth=HTTPBasicAuth(
                                                       self.usuario,
                                                       self.password),
                                           data={'email': email})
        except Exception as e:
            logging.error("Error obteniendo el ID mediante email: " + str(e))
        return respuesta.text()