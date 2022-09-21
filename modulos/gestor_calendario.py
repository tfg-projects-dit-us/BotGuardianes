"""
Módulo para agregar manejo de calendarios y eventos mediante un cliente calDAV

Contiene las clases:

- `Evento`: Clase para envolver un evento tipo caldav.Event
- `Calendario`: Clase para ofrecer métodos de manejo de un calendario

Contiene también los atributos de módulo:

- `cliente`: Variable a nivel de módulo con el objeto de manejo de cliente calDAV

Y el métodos de módulo:

- `start(url_servicio,usuario,contrasena)`: Inicio del cliente calDAV
"""

import datetime
import typing
import sys
from urllib.parse import urlparse
import logging
import itertools
import zoneinfo

import icalendar
import pytz
import arrow
import requests
import caldav


cliente:caldav.DAVClient=None


def start(url_servicio:str, usuario:str=None, contrasena:str=None):
    """
    Método de módulo para cargar el cliente caldav en una variable de método

    Args:
        url_servicio: url donde se encuentra el servidor caldav
        usuario: usuario para acceder al servicio caldav
        contrasena: contraseña del servicio


    """
    global cliente
    try:
        cliente = caldav.DAVClient(url=url_servicio, username=usuario, password=contrasena)
        logging.getLogger( __name__ ).debug("Iniciado url_servicio CALDAV")
    except Exception as e:
        logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))



class Evento:
    """
    Clase que envuelve a un objeto de clase caldav.Event

    Genera métodos que permitan operar con este objeto con más facilidad



    En el objeto caldav.Event Attendee es un diccionario de diccionarios.
    La clave es el correo del asistente, y da como resultado un diccionario que contiene
    rol y tipo de asistente. Los envuelve en listas, pero con esta clase vamos a convertirlo en un diccionario
    de diccionarios.

    ```

    Los roles del asistente son:
        REQ-PARTICIPANT: Significa asistente obligatorio al calendario
        OPT-PARTICIPANT: Empleado que pretende ceder este turno
        NON-PARTICIPANT: Empleado que quiere tomar este turno

    Los tipos del asistente son:
        INDIVIDUAL: Se usa para indicar cesiones.
        GROUP: Se usa para indicar intercambio.
        RESOURCE: Sin uso.
        ROOM: Sin uso.

    Ejemplos:


        {
        correo1: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENTE},
        correo2: {rol: ROL_DEL_ASISTENTE,tipo: TIPO_DEL_ASISTENTE}
        }
    ```
    Attributes:
        Event (caldav.Event): Evento tipo caldav.Event
        asistentes (dict[dict]): Diccionario de asistentes

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
        self.get_asistentes()
    def get_summary(self):
        """
        Obtiene nombre de evento o summary

        Returns:
             (str):Cadena con nombre del evento
        """
        return str(self.Event.vobject_instance.vevent.summary.value)

    def get_uid(self):
        """
        Obtiene uid del evento

        Returns:
            (str):Uid del evento
        """
        return str(self.Event.vobject_instance.vevent.uid.value)

    def get_asistentes(self,rol:str="",tipo=""):
        """
        Obtiene un diccionario de diccionarios, con clave el correo del usuario

        La primera vez que se ejecuta, crea el diccionario completo.

        Si se introduce un rol, obtiene un diccionario con los roles de asistentes indicados en el parámetro rol

        Args:
            rol: El rol de asistente que se quiere obtener. Pueden ser OPT-PARTICIPANT, REQ-PARTICIPANT o NON-PARTICIPANT
            tipo: TIpo de asistente que se quiere obtener. Puede ser INDIVIDUAL or GROUP
        Returns:
             (dict[dict]):Devuelve un diccionario de diccionarios con clave principal el correo del usuario.
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
        if rol!="":
            diccionario_aux={}
            cuenta_aux=0
            for asistente in self.asistentes:
                if self.asistentes[asistente]['rol']==rol:
                    diccionario_aux.update({asistente:self.asistentes[asistente]})
                    cuenta_aux+=1
            return diccionario_aux
        if tipo!="":
            diccionario_aux={}
            cuenta_aux=0
            for asistente in self.asistentes:
                if self.asistentes[asistente]['tipo']==tipo:
                    diccionario_aux.update({asistente:self.asistentes[asistente]})
                    cuenta_aux+=1
            return diccionario_aux
        else:
            return self.asistentes

    def set_asistente(self, correo_asistente:str, rol:str="",tipo:str='INDIVIDUAL'):
        """
        Actualiza lista de asistentes en el evento caldav.Event y el propio diccionario de gestor_calendario.Evento


        Args:
            correo_asistente: Correo del asistente que estamos queriendo actualizar
            rol: Valor de rol a definir para el asistente. Si no se incluye, se mantiene como estaba
            tipo: Valor de tipo del asistente. Si no se define, se mantiene como estaba originalmente.

        Returns:
            (int): 0 si es correcto, -1 si sucede una Excepción
        """
        try:
            asistente=self.asistentes[correo_asistente]

        except KeyError as k:
            self.asistentes[correo_asistente]={}

        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return -1

        finally:
            if rol != "":
                self.asistentes[correo_asistente]['rol'] = rol




            self.asistentes[correo_asistente]['tipo'] = tipo

            if hasattr(self.Event.vobject_instance.vevent, 'attendee'):
                existente = False
                for i, attendee in enumerate(self.Event.vobject_instance.vevent.attendee_list):

                    if str(urlparse(attendee.value).path) == correo_asistente:

                        self.Event.vobject_instance.vevent.attendee_list[i].params.update(
                            {'ROLE': [asistente['rol']]})
                        self.Event.vobject_instance.vevent.attendee_list[i].params.update(
                            {'CUTYPE': [asistente['tipo']]})
                        existente = True
                if not existente:
                    try:
                        self.Event.vobject_instance.vevent.add(
                            'attendee;cutype={};role={};partstat=NEEDS-ACTION;SCHEDULE-STATUS=3.7'
                            .format(tipo,rol)
                        ).value="mailto:{}".format(correo_asistente)
                    except Exception as e:
                        logging.getLogger(__name__).error(
                            "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
                        return -1

            else:
                self.Event.vobject_instance.vevent.add(
                    'attendee;cutype={};role={};partstat=NEEDS-ACTION;SCHEDULE-STATUS=3.7'
                            .format(tipo,rol)
                ).value="mailto:{}".format(correo_asistente)
            return 0
    def borrar_asistente(self, asistente:str):
        """
        Borra al asistente de un evento. Se usa cuando se cancela una propuesta por parte de un demandante o cuando se asienta un evento propuesto.

        Comprueba si el asistente está en el evento y lo borra del calendario.


        Args:
            asistente: correo del asistente a borrar

        Returns:
            (bool):True si lo borra con éxito, False si no
        """
        result=False
        try:
            del self.asistentes[asistente]

            existente = False
            for i, attendee in enumerate(self.Event.vobject_instance.vevent.attendee_list):

                if str(urlparse(attendee.value).path) == asistente:
                    del self.Event.vobject_instance.vevent.attendee_list[i]
                    existente = True
            result=True

        except KeyError as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}. El correo del asistente no está incluido en el evento".format(sys._getframe(1).f_code.co_name, e))
            return False
        except Exception as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
            return False
    def asienta_asistentes(self,ofertante:str="",demandante:str=""):
        """
        Asienta los cambios en un evento.

        Borra los usuarios con rol OPT-PARTICIPANT y convierte los NON-PARTICIPANT en REQ-PARTICIPANT

        Returns:
            (tuple[bool,list[str],list[str]]):Tupla que contiene un bool indicando si se hizo el cambio bien y dos listas, lista de correos de usuarios borrados y lista de correos de usuarios asentados
        """
        lista_asentados=[]
        para_borrar=[]
        lista_borrados=[]
        try:
            if ofertante=="" and demandante=="":
                for asistente in self.asistentes:
                    if self.asistentes[asistente]['rol']=='NON-PARTICIPANT':
                        self.set_asistente(asistente,rol='REQ-PARTICIPANT')
                        lista_asentados.append(asistente)
                    if self.asistentes[asistente]['rol']=='OPT-PARTICIPANT':
                        para_borrar.append(asistente)

                for asistente in para_borrar:
                    self.borrar_asistente(asistente)
                    lista_borrados.append(asistente)
                return (True, lista_borrados,lista_asentados)
            else:
                self.borrar_asistente(ofertante)
                self.set_asistente(demandante,rol='REQ-PARTICIPANT',tipo='INDIVIDUAL')
                return (True,)
        except Exception as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
            return (False,)
    def negar_cambio_asistentes(self,ofertante:str,demandante:str):
        """
        Niega el cambio de una guardia, borrando al demandante del evento y poniendo al ofertante de REQ-PARTICIPANT

        Args:
            ofertante: Correo del ofertante
            demandante: Correo del demandante

        Returns:
            (bool): True si realiza la negación, False si no
        """
        try:
            self.set_asistente(ofertante,rol='REQ-PARTICIPANT')
            self.borrar_asistente(demandante)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
            return False
    def get_rol_asistente(self, asistente:str):
        """
        Devuelve el rol del asistente que se pasa por parámetro

        Args:
            asistente: Correo del asistente

        Returns:
            (str):rol del asistente en cadena
        """

        return self.asistentes[asistente]['rol']
    def get_cuenta_asistentes(self):
        """
        Obtiene la cuenta de asistentes a un evento con el rol REQ-PARTICIPANT

        Returns:
            (int):Cantidad de asistentes requeridos a un evento.
        """
        cuenta=0
        self.get_asistentes()
        for asistente in self.asistentes:
            if self.asistentes[asistente]['rol']=="REQ-PARTICIPANT":
                cuenta+=1
        return cuenta
    def get_cuenta_ofertantes(self):
        """
        Obtiene cuenta de ofertantes de un evento

        Returns:
            (int):Obtiene cantidad de asistentes con rol OPT-PARTICIPANT de un evento
        """
        cuenta=0
        self.get_asistentes()
        for asistente in self.asistentes:
            if self.asistentes[asistente]['rol']=="OPT-PARTICIPANT":
                cuenta+=1
        return cuenta

    def get_cuenta_demandantes(self):
        """
        Obtiene cantidad de demandantes de un evento

        Returns:
            (int):Obtiene cantidad de asistentes con el rol NON-PARTICIPANT
        """
        cuenta=0
        self.get_asistentes()
        for asistente in self.asistentes:
            if self.asistentes[asistente]['rol']=="NON-PARTICIPANT":
                cuenta+=1
        return cuenta

    def get_fecha_str(self):
        """
        Obtiene la fecha de inicio del evento en formato cadena

        Returns:
            (str): Fecha en formato [dia-mes-año horas-minutos]
        """
        fecha:datetime.datetime=self.Event.vobject_instance.vevent.dtstart.value
        fecha_madrid=fecha.astimezone(tz=pytz.timezone('Europe/Madrid'))
        return fecha_madrid.strftime('%d-%m-%Y %H:%M')

    def get_fecha_datetime(self):
        """
        Obtiene la fecha de inicio del evento en formato datetime

        Returns:
            (datetime.datetime):Fecha de inicio del evento
        """
        fecha: datetime.datetime = self.Event.vobject_instance.vevent.dtstart.value
        fecha_madrid = fecha.astimezone(tz=pytz.timezone('Europe/Madrid'))
        return fecha_madrid

    def get_sitios_libres(self):
        """
        Obtiene la cantidad de puestos disponibles de un Evento.

        Esto es, que tengan asistentes de rol "OPT-PARTICIPANT"

        Los "NON-PARTICIPANT" cuentan como sitios ya solicitados

        Returns:
            (int):Cantidad de puestos libres
        """
        sitios_libres=0
        if self.asistentes != {}:
            for asistente in self.asistentes:
                if self.asistentes[asistente]['rol'] == 'OPT-PARTICIPANT':
                    logging.getLogger(__name__).debug(
                        "Hay un asistente 'Optativo' en un evento. Significa que ya alguien pidió ceder el evento")
                    sitios_libres += 1
                if self.asistentes[asistente]['rol'] == 'NON-PARTICIPANT':
                    logging.getLogger(__name__).debug(
                        "Hay un asistente 'No Participante' en un evento. Significa que ya alguien pidió obtener el evento que alguien cedió")
                    sitios_libres -= 1

        return sitios_libres

    def get_comprobar_asistente(self, asistente:str, rol:str=""):
        """
        Comprueba si un asistente está en un evento

        Args:
            asistente: Correo del asistente que se comprueba
            rol: Parámetro opcional. Sirve para comprobar si un usuario tiene cierto rol en concreto en el evento
        Returns:
            (bool):True si está ( con el rol en concreto si es especificado), False si no
        """
        resultado=False
        for attendee in self.asistentes:
            if (asistente == attendee):
                logging.getLogger(__name__).debug("Evento con el usuario incluido Atendee {}".format(str(asistente)))
                if rol=="":
                    resultado=True
                elif self.asistentes[asistente]['rol']==rol:
                    resultado=True


        return resultado

    def get_data(self):
        """
        Obtiene los datos del evento en una cadena con formato ical

        Returns:
            (str): String con el evento en formato ical
        """

        return self.Event.data
class Calendario:
    """
    Clase para manejar un calendario con cliente calDAV

    Attributes:
            url (str): Nombre del calendario
            calendario (caldav.Calendar): Calendario conectado con cliente calDAV

    """

    def __init__(self, url: str = None):
        """
        Constructor de Calendario

        Args:
            url (str): La nombre del calendario que cargaremos
        """
        self.url:str = url
        self.calendario:caldav.Calendar = None
        self.cargar_calendario(self.url)

    def cargar_calendario(self, nombre:str):
        """
        Inicialización del calendario mediante cliente calDAV

        Args:
            nombre: nombre del calendario perteneciente al usuario de calDAV

        """
        global cliente
        self.calendario = cliente.principal().calendar(cal_id=nombre)

    @staticmethod
    def get_fecha_inicio_mes():
        """
        Función para calcular fecha inicio mes

        Returns:
            (datetime.datetime):Fecha en formato datetime
        """
        return arrow.utcnow().to('Europe/Madrid').floor('month').datetime

    @staticmethod
    def get_fecha_hoy():
        """
        Función para calcular fecha de hoy

        Returns:
            (datetime.datetime):Fecha en formato datetime
        """
        return arrow.utcnow().to('Europe/Madrid').floor('hour').datetime
    # Función para calcular el timestamp del último día del mes
    @staticmethod
    def get_fecha_fin_mes():
        """
        Función para calcular fecha fin mes

        Returns:
           (datetime.datetime):Fecha en formato datetime
        """
        return arrow.utcnow().to('Europe/Madrid').ceil('month').datetime

    @staticmethod
    def ordenar_eventos(lista_eventos:list[Evento]):
        """
        Ordena por fecha de evento de atrás a delante la lista de eventos que se indica en la entrada

        Args:
            lista_eventos: Lista de eventos a ordenar por fecha

        Returns:
            (list[Evento]|None):Lista ordenada de eventos
        """
        lista_ordenada:list[Evento] = lista_eventos
        try:
            lista_ordenada = sorted(lista_eventos, key=lambda x: x.get_fecha_str())
        except BaseException as exception:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,exception ))
            return None
        finally:
            return lista_ordenada

    def get_eventos(self, attendee:str|None=None,rol:str="",completos:bool=False):
        """
        Obtiene los eventos de un calendario en el periodo del mes actual.

        Args:
            attendee: Asistente para quien estamos obteniendo lista de eventos.
                Si es None, obtenemos todos los eventos del periodo
                Si tiene un valor, obtenemos solo los eventos con este asistente suscrito.
            rol: Rol del asistente. Se utiliza para buscar eventos con cierto rol del participante
            completos: Se solicitan eventos que ya se puede ejecutar una cesión o intercambio.

        Returns:
            (list[Evento]):Lista de Evento
        """
        lista_eventos = []
        lista_eventos_aux = []
        no_pedido = False
        sitios_libres = 0
        sin_sitio = False
        try:
            eventosmes = self.calendario.date_search(start=self.get_fecha_hoy(), end=self.get_fecha_fin_mes(), expand=True)
            for x in eventosmes:
                lista_eventos_aux.append(Evento(x))

            for e in lista_eventos_aux:
                fecha = e.get_fecha_datetime()
                if self.get_fecha_fin_mes() > datetime.datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0, 0,
                                                                pytz.timezone(
                                                                    'Europe/Madrid')) > self.get_fecha_inicio_mes():
                    logging.getLogger( __name__ ).debug("Evento en el periodo actual " + str(e))
                    if (completos==True):
                        logging.getLogger( __name__ ).info("Se ha pedido lista de eventos para aprobar o denegar")
                        if e.get_cuenta_demandantes() == e.get_cuenta_ofertantes() and e.get_sitios_libres()==0:
                            lista_eventos.append(e)
                    elif (attendee == None and completos==False):
                        logging.getLogger( __name__ ).info("Se ha pedido lista de eventos libres")
                        if e.get_sitios_libres() > 0:
                            lista_eventos.append(e)
                    elif (attendee != None and completos==False):
                        logging.getLogger( __name__ ).info("Se ha pedido lista de eventos de una persona")
                        if e.get_comprobar_asistente(attendee,rol=rol):
                            lista_eventos.append(e)

            logging.getLogger( __name__ ).debug("Lista de eventos en get_eventos:" + str(lista_eventos))
            lista_ordenada = self.ordenar_eventos(lista_eventos)
            return lista_ordenada
        except BaseException as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            print("Error cargando eventos: " + str(e))
            return None

    def get_evento(self, uid_evento:str):
        """
        Obtiene un evento a partir de la uid del evento

        Args:
            uid_evento: identificador único del evento

        Returns:
            (Evento|None):Evento con uid=uid_evento o None en caso de no encontrarse
        """
        try:
            return Evento(self.calendario.event_by_uid(uid=uid_evento))
        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return None


    def asentar_cambios(self,uid_evento:str):
        """
        Asienta los cambios de un evento. Para ello, borra los usuarios de OPT-PARTICIPANT y convierte los NON-PARTICIPANT en REQ-PARTICIPANT.
        Esta función se utiliza desde el calendario de propuestas normalmente.

        Args:
            uid_evento: Identificador único del evento
        Returns:
            (tuple[list[str],list[str],Evento]): Tupla que contiene dos listas, lista de correos de usuarios borrados y lista de correos de usuarios asentados, y el evento
        """
        try:
            evento=self.get_evento(uid_evento)
            (borrados,asentados)=evento.asienta_asistentes()
            return (borrados,asentados,evento)
        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return ([],[],None)

    def set_evento(self, evento: Evento):
        """
        Guarda un evento en el calendario

        Args:
            evento: (gestor_calendario.Evento) Evento a guardar

        Returns:
            (bool):Verdadero si pudo hacerlo, falso si no
        """
        try:
            evento_encontrado = self.calendario.event_by_uid(uid=evento.get_uid())
            if isinstance(evento_encontrado, caldav.Event):
                evento_encontrado.data=evento.Event.data
                self.calendario.save_event(evento_encontrado.data)
                return True
        except caldav.lib.error.NotFoundError as e:
            logging.getLogger( __name__ ).info("Evento {} no existente en calendario. Función ejecutada {}".format(evento.get_uid(),
                                                                                              sys._getframe(
                                                                                                  1).f_code.co_name))
            logging.getLogger( __name__ ).info("Evento a introducir {} en calendario {} con data {}".format(str(evento),
                                                                                       str(self.calendario.canonical_url),
                                                                                       str(evento.Event.data)))
            self.calendario.save_event(evento.Event.data)
            return True
        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return False

    def ofertar_evento(self, correo_usuario: str, uid_evento: str, tipo:str= 'INDIVIDUAL', evento: Evento = None):
        """
        Busca un evento con la uid concretada en el calendario designado.
        Si no lo encuentra, usará el evento que se le pase por parámetros

        Cambia el rol al asistente a OPT-PARTICIPANT, el tipo a INDIVIDUAL y guarda el evento en el calendario

        Args:
            correo_usuario: Correo del usuario que se está tratando de cambiar el rol
            uid_evento: UID del evento que se está buscando en el calendario
            evento: Evento que se pretende introducir en el calendario para casos en los que no se encuentra el evento

        Returns:
            (Evento|None):Evento que se ha podido guardar en el calendario o None en caso de Excepción.
        """
        try:
            logging.getLogger( __name__ ).debug("Tipo de evento: " + str(type(evento)))
            evento_buscado = self.get_evento(uid_evento=uid_evento)
            if isinstance(evento_buscado, Evento):
                if evento_buscado.get_comprobar_asistente(correo_usuario):
                    evento_buscado.set_asistente(correo_usuario, rol="OPT-PARTICIPANT",tipo=tipo)

                evento_cedido = self.set_evento(evento_buscado)
                if evento_cedido == True:
                    return evento_buscado

            if isinstance(evento, Evento) and not isinstance(evento_buscado, Evento) :

                if evento.get_comprobar_asistente(correo_usuario):
                    evento.set_asistente(correo_usuario, rol="OPT-PARTICIPANT",tipo=tipo)

                evento_cedido = self.set_evento(evento)

                if evento_cedido == True:
                    return self.get_evento(uid_evento=uid_evento)

        except Exception as e:
            logging.getLogger( __name__ ).info("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            raise Exception

    def cancelar_evento(self, correo_usuario: str, uid_evento: str):
        """
        Busca un evento con la uid concretada en el calendario designado.
        Si no lo encuentra, usará el evento que se le pase por parámetros

        Esta acción depende del usuario que la envíe. Si es un usuario que estaba en NON-PARTICIPANT, lo borra del evento.
        Si es un usuario OPT-PARTICIPANT, lo vuelve a poner REQ-PARTICIPANT
        En el caso de que sea un OPT-PARTICIPANT, se evaluará si quedan sitios libres
        Si no queda ningun usuario en OPT-PARTICIPANT y se está demandando el turno, se borrará el evento,
        avisando previamente a los usuarios afectados

        Args:
            correo_usuario: Correo del usuario que se está tratando de cambiar el rol
            uid_evento: UID del evento que se está buscando en el calendario

        Returns:
            (Evento|None): Evento que se ha podido guardar en el calendario o None en caso de Excepción.
        """
        evento_cancelado=False
        try:
            logging.getLogger(__name__).debug("Tipo de evento: " + str(type(evento_cancelado)))
            evento_buscado = self.get_evento(uid_evento=uid_evento)
            if isinstance(evento_buscado, Evento):
                rol_asistente=evento_buscado.get_rol_asistente(asistente=correo_usuario)
                if rol_asistente=="OPT-PARTICIPANT":

                    ofertantes=evento_buscado.get_cuenta_ofertantes()
                    demandantes=evento_buscado.get_cuenta_demandantes()
                    asistentes=evento_buscado.get_cuenta_asistentes()

                    if ofertantes > demandantes:
                        evento_buscado.set_asistente(correo_usuario, rol="REQ-PARTICIPANT")
                        evento_cancelado = self.set_evento(evento_buscado)
                    """Se envía un mensaje al usuario indicando que no puede realizar esta acción"""

                    ofertantes = evento_buscado.get_cuenta_ofertantes()
                    if ofertantes == 0:
                        evento_buscado.Event.delete()
                        evento_cancelado=True
                if rol_asistente=="NON-PARTICIPANT":
                    evento_buscado.borrar_asistente(correo_usuario)
                    evento_cancelado = self.set_evento(evento_buscado)



                if evento_cancelado == True:
                    return evento_buscado

        except Exception as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
            return None
    def borrar_evento(self,uid_evento:str)->bool:
        """
        Borra el evento del calendario con la uid correspondiente

        Args:
            uid_evento: uid del evento que se desea borrar

        Returns:
            Devuelve True si lo borró, False si no
        """
        try:
            evento_buscado = self.get_evento(uid_evento=uid_evento)
            if isinstance(evento_buscado, Evento):
                evento_buscado.Event.delete()
                return True
            else:
                return False
        except Exception as e:
            logging.getLogger(__name__).error(
                "Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name, e))
            return False
    def tomar_evento(self, correo_usuario:str , uid_evento:str,tipo='INDIVIDUAL')->Evento|None:
        """
        Busca un evento en el calendario y añade el correo_usuario con el rol NON-PARTICIPANT

        Args:
            correo_usuario: Correo del usuario que tomará la plaza libre del evento
            uid_evento: Identificador único del evento

        Returns:
            Evento que se ha podido guardar en el calendario o None en caso de Excepción.
        """
        try:
            evento_buscado = self.get_evento(uid_evento=uid_evento)
            if isinstance(evento_buscado, Evento):
                if evento_buscado.get_comprobar_asistente(correo_usuario)!=True and evento_buscado.get_sitios_libres() > 0:
                    evento_buscado.set_asistente(correo_usuario, rol="NON-PARTICIPANT",tipo=tipo)
                    evento_tomado = self.set_evento(evento_buscado)
                    if evento_tomado == True:
                        return evento_buscado
        except Exception as e:
            logging.getLogger( __name__ ).error("Excepción en función {}. Motivo: {}".format(sys._getframe(1).f_code.co_name,e ))
            return None