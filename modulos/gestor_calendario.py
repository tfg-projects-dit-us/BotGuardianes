"""
Módulo para agregar manejo de calendarios y eventos mediante un cliente calDAV

Contiene las clases:

- `Evento`: Clase para envolver un evento tipo caldav.Event
- `Calendario`: Clase para ofrecer métodos de manejo de un calendario

Contiene también los atributos de módulo:

- `cliente`: Variable a nivel de módulo con el objeto de manejo de cliente calDAV

Y los métodos de módulo:

- `start(url_servicio,usuario,contrasena)`: Inicio del cliente calDAV
"""

import datetime
import typing
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


class Cliente_calDAV:
    """

    Clase que maneja un cliente calDAV, carga calendarios y lista los calendarios abiertos

    Attributes:

        cliente: caldav.DAVClient
    """

    def __init__(self, url_servicio, usuario, contrasena):
        """
            Método constructor de objeto de cliente caldav con URL única de donde se almacenan calendarios
            El cliente se almacena en la variable de módulo cliente

            Args:
                url_servicio: url donde se encuentra el servidor calDAV
                usuario: usuario para acceder al servidor calDAV
                contrasena: contraseña para acceder a servidor calDAV
            """
        try:
            self.cliente = caldav.DAVClient(url=url_servicio, username=usuario, password=contrasena)
            logging.debug("Iniciado url_servicio CALDAV")
        except Exception as e:
            print("")

def start(url_servicio, usuario=None, contrasena=None):

    try:
        cliente = caldav.DAVClient(url=url_servicio, username=usuario, password=contrasena)
        logging.debug("Iniciado url_servicio CALDAV")
    except Exception as e:
        print("")
    finally:
        pass


class Evento:
    """
    Clase que envuelve a un objeto de clase caldav.Event.
    Genera métodos que permitan operar con este objeto con más facilidad



    En el objeto caldav.Event Attendee es un diccionario de diccionarios.
    La clave es el correo del asistente, y da como resultado un diccionario que contiene
    rol y tipo de asistente. Los envuelve en listas, pero con esta clase vamos a convertirlo en un diccionario
    de diccionarios.

    Los roles del asistente son:
        - REQ-PARTICIPANT: Significa asistente obligatorio al calendario
        - OPT-PARTICIPANT: Empleado que pretende ceder este turno
        - NON-PARTICIPANT: Empleado que quiere tomar este turno
    Los tipos del asistente son (Aun sin uso):
        - INDIVIDUAL: El tipo por defecto
        - GROUP
        - RESOURCE
        - ROOM

    Examples:

        {

        correo1: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENTE},

        correo2: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENTE}

        }



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
        self.Event = evento
        self.asistentes = {}

    def get_summary(self):
        """
        Obtiene nombre de evento o summary

        Returns:
             str: cadena con nombre del evento
        """
        return str(self.Event.vobject_instance.vevent.summary.value)

    def get_uid(self):
        """
        Obtiene uid del evento
        Returns:
            str: uid del evento
        """
        return str(self.Event.vobject_instance.vevent.uid.value)

    def get_asistentes(self):
        """
        Obtiene un diccionario de diccionarios, con clave el correo del usuario
        La primera vez que se ejecuta, crea el diccionario completo.

        Returns:
             diccionario{diccionarios}
        """
        if self.asistentes == {}:
            if hasattr(self.Event.vobject_instance.vevent, 'attendee'):
                for asistente in self.Event.vobject_instance.vevent.contents['attendee']:
                    if 'ROLE' in asistente.params.keys() and 'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path): {
                            "rol": asistente.params['ROLE'][0], "tipo": asistente.params['CUTYPE'][0]}})
                    elif 'ROLE' in asistente.params.keys() and 'CUTYPE' not in asistente.params.keys():
                        if asistente.params['ROLE'] == ['null']:
                            self.asistentes.update(
                                {str(urlparse(asistente.value).path): {"rol": 'REQ-PARTICIPANT', "tipo": 'INDIVIDUAL'}})
                        else:
                            self.asistentes.update({str(urlparse(asistente.value).path): {
                                "rol": asistente.params['ROLE'][0], "tipo": 'INDIVIDUAL'}})
                    elif 'ROLE' not in asistente.params.keys() and 'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path): {"rol": 'REQ-PARTICIPANT', "tipo":
                            asistente.params['CUTYPE'][0]}})
                    else:
                        self.asistentes.update(
                            {str(urlparse(asistente.value).path): {"rol": 'REQ-PARTICIPANT', "tipo": 'INDIVIDUAL'}})
        return self.asistentes

    def set_asistente(self, correo_asistente, asistente):
        """
        Actualiza lista de asistentes en el evento caldav.Event y el propio diccionario de gestor_calendario.Evento
        Args:
            correo_asistente: Correo del asistente que estamos queriendo actualizar
            asistente: Diccionario de rol y tipo del asistente
        Returns:
            int: 0 si es correcto, -1 si sucede una Excepción
        """
        try:
            self.asistentes.update({correo_asistente: asistente})
            if hasattr(self.Event.vobject_instance.vevent, 'attendee'):
                for i, attendee in enumerate(self.Event.vobject_instance.vevent.contents['attendee']):

                    if str(urlparse(attendee.value).path) == correo_asistente:
                        self.Event.vobject_instance.vevent.contents['attendee'][i].params.update(
                            {'ROLE': [asistente['rol']]})
                        self.Event.vobject_instance.vevent.contents['attendee'][i].params.update(
                            {'CUTYPE': [asistente['tipo']]})
            else:
                self.Event.vobject_instance.vevent.contents['attendee'][0].behavior = None
                self.Event.vobject_instance.vevent.contents['attendee'][0].encoded = True
                self.Event.vobject_instance.vevent.contents['attendee'][0].group = None
                self.Event.vobject_instance.vevent.contents['attendee'][0].isNative = False
                self.Event.vobject_instance.vevent.contents['attendee'][0].name = "ATTENDEE"
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update({'PARTSTAT': ['NEEDS-ACTION']})
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update({'ROLE': [asistente['rol']]})
                self.Event.vobject_instance.vevent.contents['attendee'][0].params.update(
                    {'CUTYPE': [asistente['tipo']]})
                self.Event.vobject_instance.vevent.contents['attendee'][0].value = "mailto:" + correo_asistente
            return 0
        except Exception as e:
            logging.error("Error en set-asistentes. {}".format(e))
            return -1

    def get_fecha_str(self):
        """
        Obtiene la fecha del evento en formato cadena

        Returns:
            str: Fecha en formato [dia-mes-año horas-minutos]
        """
        return str(self.Event.vobject_instance.vevent.dtstart.value.strftime('%d-%m-%Y %H:%M'))

    def get_fecha_datetime(self):
        """
        Obtiene la fecha del evento en formato datetime

        Returns:
            datetime.datetime
        """
        return self.Event.vobject_instance.vevent.dtstart.value


class Calendario:
    """
    Clase para manejar un calendario con cliente calDAV
    Atributes:
            url (str): Nombre del calendario
            calendario (caldav.Calendar): Calendario conectado con cliente calDAV
    Methods:
        get_fecha_inicio_mes(): Obtiene fecha de inicio del mes en curso
        get_fecha_fin_mes():    Obtiene fecha de fin del mes en curso
        cargar_calendario(nombre): Carga el calendario con el cliente calDAV en el atributo calendario
        get_eventos(attendee=None):
    """

    def __init__(self, url: str = None):
        """
        Constructor de Calendario
        Args:
            url (str): La nombre del calendario que cargaremos
        """
        self.url = url
        self.calendario = None
        self.cargar_calendario(self.url)

    def cargar_calendario(self, nombre):
        """
        Inicialización del calendario mediante cliente calDAV
        Args:
            nombre: nombre del calendario perteneciente al usuario de calDAV

        """
        self.calendario = cliente.principal().calendar(cal_id=nombre)

    @staticmethod
    def get_fecha_inicio_mes():
        """
        Función para calcular fecha inicio mes

        Returns:
            datetime.datetime
        """
        return arrow.utcnow().to('Europe/Madrid').floor('month').datetime

    # Función para calcular el timestamp del último día del mes
    @staticmethod
    def get_fecha_fin_mes():
        """
        Función para calcular fecha fin mes

        Returns:
            datetime
        """
        return arrow.utcnow().to('Europe/Madrid').ceil('month').datetime

    @staticmethod
    def ordenar_eventos(lista_eventos):
        """
        Ordena por fecha de evento de atrás a delante la lista de eventos que se indica en la entrada
        Args:
            lista_eventos: Lista de eventos a ordenar por fecha

        Returns:
            Lista ordenada de eventos (list(Evento))
        """
        lista_ordenada = lista_eventos
        try:
            lista_ordenada = sorted(lista_eventos, key=lambda x: x.get_fecha_str())
        except BaseException as exception:
            logging.error("Error ordenando lista: " + str(exception))
            return None
        finally:
            return lista_ordenada

    def get_eventos(self, attendee=None):
        """
        Función para obtener los eventos de un calendario  en el periodo del mes actual.

        Args:
            attendee(Por defecto None): Asistente para quien estamos obteniendo lista de eventos.
                Si es None, obtenemos todos los eventos del periodo
                Si tiene un valor, obtenemos solo los eventos con este asistente suscrito.

        Returns:
            list(gestor_calendario.Evento)
        """
        lista_eventos = []
        lista_eventos_aux = []
        no_pedido = False
        sitios_libres = 0
        sin_sitio = False
        try:
            eventosmes = self.calendario.date_search(start=self.fecha_inicial, end=self.fecha_final, expand=True)
            for x in eventosmes:
                lista_eventos_aux.append(Evento(x))

            for e in lista_eventos_aux:
                fecha = e.get_fecha_datetime()
                if self.get_fecha_fin_mes() > datetime.datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0, 0,
                                                                pytz.timezone(
                                                                    'Europe/Madrid')) > self.get_fecha_inicio_mes():
                    logging.debug("Evento en el periodo actual " + str(e))
                    dic_asistentes = e.get_asistentes()
                    if (attendee == None):
                        logging.info("Se ha pedido lista de eventos libres")
                        if dic_asistentes != {}:
                            for asistente in dic_asistentes:
                                if dic_asistentes[asistente]['rol'] == 'OPT-PARTICIPANT':
                                    logging.debug(
                                        "Hay un asistente 'Optativo' en un evento. Significa que ya alguien pidió ceder el evento")
                                    sitios_libres += 1
                                if dic_asistentes[asistente]['rol'] == 'NON-PARTICIPANT':
                                    logging.debug(
                                        "Hay un asistente 'No Participante' en un evento. Significa que ya alguien pidió obtener el evento que alguien cedió")
                                    sitios_libres -= 1
                            if sitios_libres > 0:
                                lista_eventos.append(e)
                    elif (attendee != None):
                        logging.info("Se ha pedido lista de eventos de una persona")
                        if dic_asistentes != {}:
                            for asistente in dic_asistentes:
                                if (attendee in asistente):
                                    logging.debug("Evento con el usuario incluido Atendee " + str(asistente))
                                    lista_eventos.append(e)

            logging.debug("Lista de eventos en get_eventos:" + str(lista_eventos))
            lista_ordenada = self.ordenar_eventos(lista_eventos)
            return lista_ordenada
        except BaseException as e:
            logging.error("Error cargando eventos: " + str(e))
            print("Error cargando eventos: " + str(e))
            return None

    def get_evento(self, uid_evento):
        """
        Obtiene un evento a partir de la uid del evento
        Args:
            uid_evento: identificador único del evento

        Returns:
            gestor_calendario.Evento: con uid=uid_evento o None en caso de no encontrarse
        """
        try:
            return Evento(self.calendario.event_by_uid(uid=uid_evento))
        except Exception as e:
            logging.error("Error consiguiendo evento de calendario: " + str(e))
            return None

    def set_evento(self, evento):
        try:
            evento_encontrado = self.calendario.event_by_uid(uid=evento.get_uid())
            if isinstance(evento_encontrado, caldav.Event):
                evento_encontrado = evento.Event
                evento_encontrado.save()

            return True
        except caldav.lib.error.NotFoundError as e:
            logging.debug("Evento {} no existente en calendario. Función ejecutada {}".format(evento.get_uid(),
                                                                                              sys._getframe(
                                                                                                  1).f_code.co_name))
            print(str(evento))
            logging.debug("Evento a introducir {} en calendario {} con data {}".format(str(evento),
                                                                                       str(self.calendario.canonical_url),
                                                                                       str(evento.Event.data)))
            self.calendario.save_event(evento.Event.data)
            return True
        except Exception as e:
            logging.error("Error en la insercion de evento: " + str(e))
            return False

    def ceder_evento(self, asistente, uidevento, evento=None):

        try:
            logging.debug("Tipo de evento: " + str(type(evento)))
            evento_buscado = self.get_evento(uid_evento=uidevento)
            if not isinstance(evento, Evento) and isinstance(evento_buscado, Evento):
                asistentes = evento_buscado.get_asistentes()
                for attendee in asistentes:
                    if attendee == asistente:
                        asistentes[attendee]['rol'] = 'OPT-PARTICIPANT'
                        evento_buscado.set_asistente(attendee, asistentes[attendee])

                evento_cedido = self.set_evento(evento_buscado)
                if evento_cedido == True:
                    return evento_buscado

            if isinstance(evento, Evento):

                asistentes = evento.get_asistentes()

                for attendee in asistentes:
                    if attendee == asistente:
                        asistentes[attendee]['rol'] = 'OPT-PARTICIPANT'
                        evento.set_asistente(attendee, asistentes[attendee])

                evento_cedido = self.set_evento(evento)

                if evento_cedido == True:
                    return evento

        except Exception as e:
            logging.error("Error cediendo evento: {}. Funcion {}".format(e, sys._getframe(1).f_code.co_name))
            return False

    def tomar_evento(self, attendee, uidevento):
        for e in self.calendario.events:
            if e.uid == uidevento:
                pass
