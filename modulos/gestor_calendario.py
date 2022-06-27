#BotGuardianes/modulos/gestor_calendario.py
"""
Módulo para agregar manejo de calendarios y eventos mediante un cliente calDAV

Contiene las clases:

- `Evento`: Clase para envolver un evento tipo caldav.Event
- `Calendario`: Clase para ofrecer métodos de manejo de un calendario

Contiene también los atributos de módulo:

- `cliente`: Variable a nivel de módulo con el objeto de manejo de cliente calDAV

Y los métodos de módulo:

- `start(servicio,usuario,contrasena)`: Inicio del cliente calDAV
"""


import datetime
import pytz
import sys
from urllib.parse import urlparse
import logging
import itertools

import arrow
import requests
import calendar
import ics
import caldav


cliente=None
def start(servicio=None,usuario=None,contrasena=None):
    """
    Función de módulo para iniciar cliente caldav con URL única de donde se almacenan calendarios

    Args:
        servicio: url donde se encuentra el servidor calDAV
        usuario: usuario para acceder al servidor calDAV
        contrasena: contraseña para acceder a servidor calDAV

    Returns:
        None
    """
    global cliente
    cliente=caldav.DAVClient(url=url_servicio,username=usuario,password=contrasena)
    logging.debug("Iniciado servicio CALDAV")

class Evento:
    """
    Clase que envuelve a un objeto de clase caldav.Event.
    Genera métodos que permitan operar con este objeto con más facilidad



    En el objeto caldav.Event Attendee es un diccionario de diccionarios.
    La clave es el correo del asistente, y da como resultado un diccionario que contiene
    rol y tipo de asistente. Los envuelve en listas, pero con esta clase vamos a convertirlo en un diccionario
    de diccionarios


    """

    def __init__(self, evento: caldav.Event):
        """
        Constructor de Evento.

        Crea atributos:
            - Event: caldav.Event
            - asistentes: diccionario de asistentes {correo1,correo2,...}

        Args:
             evento: Evento tipo caldav.Event

        """
        self.Event=evento
        self.asistentes={}
    def get_summary(self):
        """
        Obtiene nombre de evento o summary

        Returns:
             str: cadena con nombre del evento
        """
        return str(self.Event.vobject_instance.vevent.summary.value)
    def get_uid(self):
        return str(self.Event.vobject_instance.vevent.uid.value)

    def get_asistentes(self):
        """
        Obtiene un diccionario de diccionarios, con clave el correo del usuario

        Ejemplo
        {
        correo1: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENT}
        correo2: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENT}
        }

        Los roles del asistente son:
            - REQ-PARTICIPANT: Significa asistente obligatorio al calendario
            - OPT-PARTICIPANT: Empleado que pretende ceder este turno
            - NON-PARTICIPANT: Empleado que quiere tomar este turno
        Los tipos del asistente son (Aun sin uso):
            - INDIVIDUAL: El tipo por defecto
            - GROUP
            - RESOURCE
            - ROOM
        Returns:
             diccionario{diccionarios}
        """
        if self.asistentes =={}:
            if hasattr(self.Event.vobject_instance.vevent,'attendee'):
                for asistente in self.Event.vobject_instance.vevent.contents['attendee']:
                    if 'ROLE' in asistente.params.keys() and 'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":asistente.params['ROLE'][0],"tipo":asistente.params['CUTYPE'][0]}})
                    elif  'ROLE' in asistente.params.keys() and not 'CUTYPE' in asistente.params.keys():
                        if asistente.params['ROLE']==['null']:
                            self.asistentes.update(
                                {str(urlparse(asistente.value).path): {"rol": 'REQ-PARTICIPANT', "tipo": 'INDIVIDUAL'}})
                        else:
                            self.asistentes.update({str(urlparse(asistente.value).path):{"rol":asistente.params['ROLE'][0],"tipo":'INDIVIDUAL'}})
                    elif not 'ROLE' in asistente.params.keys() and  'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":'REQ-PARTICIPANT',"tipo":asistente.params['CUTYPE'][0]}})
                    else:
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":'REQ-PARTICIPANT',"tipo":'INDIVIDUAL'}})
        return self.asistentes

    def set_asistente(self, correo_asistente, asistente):
        try:
            self.asistentes.update({correo_asistente:asistente})
            if hasattr(self.Event.vobject_instance.vevent, 'attendee'):
                for i,attendee in enumerate(self.Event.vobject_instance.vevent.contents['attendee']):

                    if  str(urlparse(attendee.value).path)==correo_asistente:
                        self.Event.vobject_instance.vevent.contents['attendee'][i].params.update({'ROLE':[asistente['rol']]})
                        self.Event.vobject_instance.vevent.contents['attendee'][i].params.update({'CUTYPE': [asistente['tipo']]})
            else:
                self.Event.vobject_instance.vevent.contents['attendee'][0].behavior=None
                self.Event.vobject_instance.vevent.contents['attendee'][0].encoded=True
                self.Event.vobject_instance.vevent.contents['attendee'][0].group=None
                self.Event.vobject_instance.vevent.contents['attendee'][0].isNative=False
                self.Event.vobject_instance.vevent.contents['attendee'][0].name="ATTENDEE"
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update({'PARTSTAT':['NEEDS-ACTION']})
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update({'ROLE':[asistente['rol']]})
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update({'CUTYPE': [asistente['tipo']]})
                self.Event.vobject_instance.vevent.contents['attendee'][0].value="mailto:" + correo_asistente
        except Exception as e:
            logging.error("Error en set-asistentes. {}".format(e))


    def get_fecha_str(self):
        return str(self.Event.vobject_instance.vevent.dtstart.value.strftime('%d-%m-%Y %H:%M'))
    def get_fecha_datetime(self):
        return self.Event.vobject_instance.vevent.dtstart.value



class Calendario:
    """
    Clase para manejar un calendario con cliente calDAV

    Methods:
        get_fecha_inicio_mes(): Obtiene fecha de inicio del mes en curso
        get_fecha_fin_mes():    Obtiene fecha de fin del mes en curso
        cargar_calendario(url): Carga el calendario con el cliente calDAV en el atributo calendario
        get_eventos(attendee=None):
    """
    def __init__(self, url: str = None):
        """
        Constructor de Calendario
        Args:
            url (str): La url del calendario que cargaremos

        Attributes:
            url (str): La url del calendario
            calendario (caldav.Calendar): Calendario conectado con cliente calDAV
        """
        self.url = url
        self.cargar_calendario(self.url)

    def cargar_calendario(self, url):
        self.calendario = cliente.principal().calendar(cal_id=url)
    # Función para calcular el timestamp del primer día del mes
    @staticmethod
    def get_fecha_inicio_mes():
        return arrow.utcnow().to('Europe/Madrid').floor('month').datetime
    # Función para calcular el timestamp del último día del mes
    @staticmethod
    def get_fecha_fin_mes():
        self.fecha_final = arrow.utcnow().to('Europe/Madrid').ceil('month').datetime
        return self.fecha_final
    def get_eventos(self,attendee=None):
        lista_eventos=[]
        lista_eventos_aux=[]
        no_pedido=False
        sitios_libres=0
        sin_sitio=False
        try:
            eventosmes=self.calendario.date_search(start=self.fecha_inicial, end=self.fecha_final, expand=True)
            for x in eventosmes:
                lista_eventos_aux.append(Evento(x))

            for e in  lista_eventos_aux:
                fecha=e.get_fecha_datetime()
                if self.get_fecha_fin_mes() > datetime.datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0, 0, pytz.timezone('Europe/Madrid')) > self.get_fecha_inicio_mes():
                    logging.debug("Evento en el periodo actual " + str(e))
                    dic_asistentes = e.get_asistentes()
                    if (attendee == None):
                        logging.info("Se ha pedido lista de eventos libres")
                        if dic_asistentes!={}:
                            for asistente in dic_asistentes:
                                if dic_asistentes[asistente]['rol']=='OPT-PARTICIPANT':
                                    logging.debug("Hay un asistente 'Optativo' en un evento. Significa que ya alguien pidió ceder el evento")
                                    sitios_libres+=1
                                if dic_asistentes[asistente]['rol']=='NON-PARTICIPANT':
                                    logging.debug("Hay un asistente 'No Participante' en un evento. Significa que ya alguien pidió obtener el evento que alguien cedió")
                                    sitios_libres-=1
                            if sitios_libres>0:
                                lista_eventos.append(e)
                    elif (attendee != None):
                        logging.info("Se ha pedido lista de eventos de una persona")
                        if dic_asistentes != {}:
                            for asistente in dic_asistentes:
                                if (attendee in asistente):
                                    logging.debug("Evento con el usuario incluido Atendee " + str(asistente))
                                    lista_eventos.append(e)

            logging.debug("Lista de eventos en get_eventos:" + str(lista_eventos))
            lista_ordenada=self.ordenar_eventos(lista_eventos)
            return lista_ordenada
        except BaseException as e:
            logging.error("Error cargando eventos: " + str(e))
            print("Error cargando eventos: " + str(e))


    def ordenar_eventos(self,lista_eventos):
        lista_ordenada=lista_eventos
        try:
            lista_ordenada=sorted(lista_eventos,key=lambda x: x.get_fecha_str())
        except BaseException as exception:
            logging.error("Error ordenando lista: "+ str(exception))
        finally:
            return lista_ordenada

    def get_evento(self,uid_evento):
        try:
            return Evento(self.calendario.event_by_uid(uid=uid_evento))
        except Exception as e:
            logging.error("Error consiguiendo evento de calendario: " + str(e))
            return None

    def set_evento(self,evento):
        try:
            evento_encontrado=self.calendario.event_by_uid(uid=evento.get_uid())
            if isinstance(evento_encontrado, caldav.Event):
                evento_encontrado=evento.Event
                evento_encontrado.save()

            return True
        except caldav.lib.error.NotFoundError as e:
            logging.debug("Evento {} no existente en calendario. Función ejecutada {}".format(evento.get_uid(), sys._getframe(1).f_code.co_name))
            print(str(evento))
            logging.debug("Evento a introducir {} en calendario {} con data {}".format(str(evento),str(self.calendario.canonical_url),str(evento.Event.data)))
            self.calendario.save_event(evento.Event.data)
            return True
        except Exception as e:
            logging.error("Error en la insercion de evento: " + str(e))
            return False


    def ceder_evento(self,asistente,uidevento,evento=None):

        try:
            logging.debug("Tipo de evento: " + str(type(evento)))
            evento_buscado=self.get_evento(uid_evento=uidevento)
            if not isinstance(evento,Evento) and isinstance(evento_buscado,Evento):
                asistentes=evento_buscado.get_asistentes()
                for attendee in asistentes:
                    if attendee==asistente:
                        asistentes[attendee]['rol']='OPT-PARTICIPANT'
                        evento_buscado.set_asistente(attendee,asistentes[attendee])

                evento_cedido = self.set_evento(evento_buscado)
                if evento_cedido == True:
                    return evento_buscado

            if isinstance(evento,Evento):

                asistentes=evento.get_asistentes()

                for attendee in asistentes:
                    if attendee==asistente:
                        asistentes[attendee]['rol']='OPT-PARTICIPANT'
                        evento.set_asistente(attendee,asistentes[attendee])

                evento_cedido = self.set_evento(evento)

                if evento_cedido == True:
                    return evento

        except Exception as e:
            logging.error("Error cediendo evento: {}. Funcion {}".format(e,sys._getframe(1).f_code.co_name))
            return False
    def tomar_evento(self,attendee,uidevento):
        for e in self.calendario.events:
            if e.uid==uidevento:
                pass