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



url_servicio=None
cliente=None
def start(servicio=None,usuario=None,contrasena=None):
    global url_servicio,cliente
    url_servicio=servicio
    cliente=caldav.DAVClient(url=url_servicio,username=usuario,password=contrasena)
    logging.debug("Iniciado servicio CALDAV")

class Evento:
    '''
    Asistente es un diccionario de diccionarios.
    La clave es el correo del asistente, y da como resultado un diccionario que contiene
    rol y tipo de asistente
    Los roles son:
        - REQ-PARTICIPANT: Significa asistente obligatorio al calendario
        - OPT-PARTICIPANT: Empleado que pretende ceder este turno
        - NON-PARTICIPANT: Empleado que quiere tomar este turno
    Los tipos son (Aun sin uso):
        - INDIVIDUAL: El tipo por defecto
        - GROUP
        - RESOURCE
        - ROOM
    '''

    def __init__(self, evento: caldav.Event):
        self.Event=evento
        self.asistentes={}
    def get_summary(self):
        return str(self.Event.vobject_instance.vevent.summary.value)
    def get_uid(self):
        return str(self.Event.vobject_instance.vevent.uid.value)

    def get_asistentes(self):
        if self.asistentes =={}:
            if hasattr(self.Event.vobject_instance.vevent,'attendee'):
                for asistente in self.Event.vobject_instance.vevent.contents['attendee']:
                    if 'ROLE' in asistente.params.keys() and 'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":asistente.params['ROLE'][0],"tipo":asistente.params['CUTYPE']}})
                    elif  'ROLE' in asistente.params.keys() and not 'CUTYPE' in asistente.params.keys():
                        if asistente.params['ROLE']==['null']:
                            self.asistentes.update(
                                {str(urlparse(asistente.value).path): {"rol": "REQ-PARTICIPANT", "tipo": "INDIVIDUAL"}})
                        else:
                            self.asistentes.update({str(urlparse(asistente.value).path):{"rol":asistente.params['ROLE'][0],"tipo":"INDIVIDUAL"}})
                    elif not 'ROLE' in asistente.params.keys() and  'CUTYPE' in asistente.params.keys():
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":"REQ-PARTICIPANT","tipo":asistente.params['CUTYPE']}})
                    else:
                        self.asistentes.update({str(urlparse(asistente.value).path):{"rol":"REQ-PARTICIPANT","tipo":"INDIVIDUAL"}})
        return self.asistentes

    def set_asistente(self,asistente):
        for attendee in self.asistentes:
            if attendee==asistente:
                self.asistentes.update(asistente)
    def get_fecha_str(self):
        return str(self.Event.vobject_instance.vevent.dtstart.value.strftime('%d-%m-%Y %H:%M'))
    def get_fecha_datetime(self):
        return self.Event.vobject_instance.vevent.dtstart.value

class Calendario:

    def __init__(self, url: str = None):
        self.url = url
        self.tsini = None
        self.tsfin = None
        self.cargarCalendario(self.url)
        self.timestampmesinicio()
        self.timestampmesfinal()

    def cargarCalendario(self, url):
        self.calendario = cliente.principal().calendar(cal_id=url)

    def recargaCalendario(self):
        pass
    def actualizarCalendario(self):
        pass
    # Función para calcular el timestamp del primer día del mes
    def timestampmesinicio(self):
        self.tsini=arrow.utcnow().to('Europe/Madrid').floor('month').datetime
        return self.tsini
    # Función para calcular el timestamp del último día del mes
    def timestampmesfinal(self):
        self.tsfin = arrow.utcnow().to('Europe/Madrid').ceil('month').datetime
        return self.tsfin
    def get_eventos(self,attendee=None):
        lista_eventos=[]
        lista_eventos_aux=[]
        no_pedido=False
        sitios_libres=0
        sin_sitio=False
        try:
            eventosmes=self.calendario.date_search(start=self.tsini,end=self.tsfin,expand=True)
            for x in eventosmes:
                lista_eventos_aux.append(Evento(x))

            for e in  lista_eventos_aux:
                fecha=e.get_fecha_datetime()
                if self.timestampmesfinal() > datetime.datetime(fecha.year,fecha.month,fecha.day,0,0,0,0,pytz.timezone('Europe/Madrid')) > self.timestampmesinicio():
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
            evento_encontrado=self.calendario.event_by_uid(uid=evento.uid)
            if isinstance(evento_encontrado, caldav.Event):
                evento_encontrado=evento
                evento_encontrado.save()
            if isinstance(evento_encontrado, type(None)):
                self.calendario.save(str(evento.Event.icalendar_instance))
            return True
        except Exception as e:
            logging.error("Error en la insercion de evento: " + str(e))
            return False




    def ceder_evento(self,asistente,uidevento,evento=None):

        try:
            logging.debug("Tipo de evento: " + str(type(evento)))
            evento_buscado=self.get_evento(uid_evento=uidevento)
            if not isinstance(evento,Evento) and isinstance(evento_buscado,Evento):

                for attendee in evento_buscado.get_asistentes():
                    if attendee==asistente:
                        attendee['rol']="OPT-PARTICIPANT"
                        evento_buscado.set_asistente(attendee)

                evento_cedido = self.set_evento(evento_buscado)
                if evento_cedido == True:
                    return evento_buscado
            if isinstance(evento,caldav.objects.Event):
                for attendee in evento.vobject_instance.vevent.contents['attendee']:
                    if urlparse(attendee.value).path==asistente:
                        attendee.params['ROLE'][0]="OPT-PARTICIPANT"
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