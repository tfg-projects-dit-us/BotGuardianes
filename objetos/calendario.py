import datetime
import pytz
import logging
import arrow
import requests
import calendar
import ics
import caldav

class calendario:
    url = None
    user = None
    password = None
    tsini = None
    tsfin = None
    calendario = None

    def __init__(self, url: str = None, user: str = None, password: str = None):
        self.url = url
        self.user = user
        self.password = password
        self.tsini = None
        self.tsfin = None
        self.cargarCalendario(self.url, self.user, self.password)
        self.timestampmesinicio()
        self.timestampmesfinal()

    def cargarCalendario(self, url, user, password):
        self.calendario = ics.Calendar(requests.get(url, auth=(user, password)).text)

    def recargaCalendario(self):
        self.calendario = ics.Calendar(requests.get(self.url, auth=(self.user, self.password)).text)
    def actualizarCalendario(self):
        pass
    # Función para calcular el timestamp del primer día del mes
    def timestampmesinicio(self):
        self.tsini=arrow.utcnow().to('Europe/Madrid').floor('month')
        return self.tsini
    # Función para calcular el timestamp del último día del mes
    def timestampmesfinal(self):
        self.tsfin = arrow.utcnow().to('Europe/Madrid').ceil('month')
        return self.tsfin
    def get_eventos(self,attendee=None):
        lista_eventos=[]
        self.recargaCalendario()
        for e in self.calendario.events:
            if self.timestampmesfinal() > e.begin > self.timestampmesinicio():
                logging.debug("Evento en el periodo actual " + str(e))
                if (attendee==None):
                    if(list(e.attendees) == []):
                        lista_eventos.append(e)
                elif(attendee!=None):
                    if list(e.attendees)!=[]:
                        for asistente in e.attendees:
                            if(attendee in asistente.common_name) :
                                logging.info("Evento con el usuario incluido Atendee " + str(asistente.common_name))
                                lista_eventos.append(e)
        logging.debug("Lista de eventos en get_eventos:" + str(lista_eventos))
        return lista_eventos

    def get_evento(self,uid_evento):
        try:
            evento=False
            for e in self.calendario.events:
                if e.uid == uid_evento:
                    evento=e

            return evento
        except Exception as e:
            logging.error("Error consiguiendo evento de calendario: " + str(e))
            return False

    def set_evento(self,evento):
        busqueda=False
        eventos=self.calendario.events
        try:
            for e in self.calendario.events:
                if e.uid==evento.uid:
                    e=evento
                    busqueda=True
            if busqueda==False:
                self.calendario.events.add(evento)
                busqueda=True
            return busqueda
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