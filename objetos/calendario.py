import datetime

class calendario:
    def __init__(self,url=none,user=none,password=none):
        self.url = url
        self.user = user
        self.password = password
        self.tsini=none
        self.tsfin=none
        
    #Función para calcular el timestamp del primer día del mes
    def timestampmesinicio():
        fecha=datetime.date.today()
        self.tsini=datetime.datetime(fecha.year,fecha.month,1,0,0,0,tzinfo=pytz.timezone('Europe/Madrid'))


    #Función para calcular el timestamp del último día del mes
    def timestampmesfinal():
        fecha=datetime.date.today()
        self.tsfin=datetime.datetime(fecha.year,fecha.month,calendar.monthrange(fecha.year,fecha.month)[1],23,59,59,tzinfo=pytz.timezone('Europe/Madrid'))