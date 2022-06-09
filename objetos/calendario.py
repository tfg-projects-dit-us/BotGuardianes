import datetime
import pytz
import logging
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

class Calendario:
    url = None
    tsini = None
    tsfin = None
    calendario = None

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
        no_pedido=False
        sin_sitio=False
        try:
            eventosmes=self.calendario.date_search(start=self.tsini,end=self.tsfin,expand=True)
            for e in eventosmes:
                fecha=e.vobject_instance.vevent.dtstart.value
                if self.timestampmesfinal() > datetime.datetime(fecha.year,fecha.month,fecha.day,0,0,0,0,pytz.timezone('Europe/Madrid')) > self.timestampmesinicio():
                    logging.debug("Evento en el periodo actual " + str(e))
                    if (attendee == None):
                        logging.info("Se ha pedido lista de eventos libres")
                        for asistente in e.vobject_instance.vevent.attendee:
                            if asistente.role.value=='OPT-PARTICIPANT':
                                logging.debug("Hay un asistente 'Optativo' en un evento. Significa que ya alguien pidió ceder el evento")
                                no_pedido=True
                            if asistente.role.value=='NON-PARTICIPANT':
                                logging.debug("Hay un asistente 'No Participante' en un evento. Significa que ya alguien pidió obtener el evento que alguien cedió")
                                sin_sitio=True
                        if no_pedido==True and sin_sitio==False:
                            lista_eventos.append(e)
                    elif (attendee != None):
                        logging.info("Se ha pedido lista de eventos de una persona")
                        lista_asistentes=e.vobject_instance.vevent.attendee
                        for asistente in e.vobject_instance.vevent.attendee:
                            if (attendee in asistente.value):
                                logging.debug("Evento con el usuario incluido Atendee " + str(asistente.common_name))
                                lista_eventos.append(e)
            logging.debug("Lista de eventos en get_eventos:" + str(lista_eventos))
            return lista_eventos
        except BaseException as e:
            logging.error("Error cargando eventos: " + str(e))
            print("Error cargando eventos: " + str(e))



    def get_evento(self,uid_evento):
        try:
            return self.calendario.event_by_uid(uid=uid_evento)
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
                self.calendario.save(str(evento.icalendar_instance))
            return True
        except Exception as e:
            logging.error("Error en la insercion de evento: " + str(e))
            return False




    def ceder_evento(self,asistente,uidevento,evento=None):

        try:
            evento_buscado=self.get_evento(uid_evento=uidevento)
            if not isinstance(evento,ics.icalendar.Event) and isinstance(evento_buscado,ics.icalendar.Event):

                for attendee in evento_buscado.attendees:
                    if attendee.common_name==asistente:
                        attendee.role="OPT-PARTICIPANT"

                evento_cedido = self.set_evento(evento_buscado)
                if evento_cedido == True:
                    return evento_buscado
            if isinstance(evento,ics.icalendar.Event):
                for attendee in evento.attendees:
                    if attendee.common_name==asistente:
                        attendee.role="OPT-PARTICIPANT"
                evento_cedido = self.set_evento(evento)

                if evento_cedido == True:
                    return evento

        except Exception as e:
            logging.error("Error cediendo evento: " +str(e))
            return False
    def tomar_evento(self,attendee,uidevento):
        for e in self.calendario.events:
            if e.uid==uidevento:
                pass