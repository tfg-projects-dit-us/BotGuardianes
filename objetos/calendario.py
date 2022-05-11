import datetime
import pytz
import logging
import arrow
import requests
import calendar
import ics

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
        for e in self.calendario.events:
            if self.timestampmesfinal() > e.begin > self.timestampmesinicio():
                logging.debug("Evento en el periodo actual " + str(e))
                if (attendee==None):
                    if(list(e.attendees) == []):
                        lista_eventos.append(e)
                elif(attendee!=None):
                    if attendee in list(e.attendees)[0].common_name:
                        logging.info("Evento con el usuario incluido" + str(e))
                        lista_eventos.append(e)
        return lista_eventos
    def tomar_evento(self,attendee,uidevento):
        for e in self.calendario.events:
            if e.uid==uidevento:
                pass