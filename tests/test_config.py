import yaml
import unipath
from modulos.config import config
import os
import pytest_check as check


def test_cargar_config():
    """
        Con esta función comprobamos la carga de configuración.

        Se crean diccionarios con los datos que tiene el fichero de prueba config_test.yaml
        """
    datos_calendario = {
        "url_servidor": "http://URL-SERVIDOR",
        "url_propuestas": "propuestas",
        "url_definitivos": "principal",
        "usuario": "usuario",
        "contrasena": "usuario"
    }
    datos_telegram = {
        "token_bot": "cadenaalfanumerica2245566",
        "canal_id": -1001111111111,
        "canal_id_admin": -1002222222222
    }
    datos_sqlite={
        "path":"./data/relaciones_id.sqlite"
    }
    datos_REST = {
        "url_insertartelegramID": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors/telegramID",
        "url_getIDporemail": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors/idDoctor",
        "url_getnombreporID": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors",
        "url_getIDrestporIDtel": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors/idDoctor",
        "url_getrol": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors/rol",
        "url_getTelegramID": "http://URL-SERVIDOR-REST:8080/guardians/api/doctors/telegramID",
        "contrasena": "password",
        "usuario": "usuario"
    }
    configuracion = config(unipath.Path(os.path.dirname(__file__) + r'\config_test.yaml'))

    check.equal(datos_calendario, configuracion.configfile['calendarios'])
    check.equal(datos_REST, configuracion.configfile['REST'])
    check.equal(datos_telegram, configuracion.configfile['telegram'])


