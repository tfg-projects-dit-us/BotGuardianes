import datetime
import ics
import pytz
import requests
import calendar


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
        fecha = datetime.date.today()
        self.tsini = datetime.datetime(fecha.year, fecha.month, 1, 0, 0, 0, tzinfo=pytz.timezone('Europe/Madrid'))

    # Función para calcular el timestamp del último día del mes
    def timestampmesfinal(self):
        fecha = datetime.date.today()
        self.tsfin = datetime.datetime(fecha.year, fecha.month, calendar.monthrange(fecha.year, fecha.month)[1], 23, 59,
                                       59, tzinfo=pytz.timezone('Europe/Madrid'))
