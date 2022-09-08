# BotGuardianes
Repositorio para el desarrollo de Bot para el soporte a la gestión de actividades asistenciales

Este proyecto está desarrollado con Python 3.10.

Aunque su funcionalidad está probada en Python 3.8, se recomienda partir de la versión 3.10


Instalar dependencias con python -m pip install --user -r requisitos_python.txt

Si se usa en modo administrador, quitar --user

Una vez instalados los requisitos, se requiere renombrar la carpeta config_ejemplo a config
En el fichero config.yaml se rellenan los datos de configuración necesarios.

## Desarrollo

Para desarrollar este proyecto se requiere instalar las dependencias con el método anteriormente descrito

También se puede hacer desarrollo usando entornos virtuales de Python para evitar interferencias
de módulos instalados de Python

Los tests funcionan en el testrunner de Pycharm. Para hacer funcionar los tests con el binario de pytest
se requiere cambiar la estructura de carpetas, 