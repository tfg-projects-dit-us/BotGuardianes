# BotGuardianes
Repositorio para el desarrollo de Bot para el soporte a la gestión de actividades asistenciales

Este proyecto está desarrollado con Python 3.10.

Aunque su funcionalidad está probada en Python 3.8, se recomienda partir de la versión 3.10


Instalar dependencias con python -m pip install --user -r requirements.txt

Si se usa con privilegios de administrador, quitar --user

Una vez instalados los requisitos, se requiere renombrar la carpeta config_ejemplo a config
En el fichero config.yaml se rellenan los datos de configuración necesarios.

## Desarrollo

Para desarrollar este proyecto se requiere instalar las dependencias con el método anteriormente descrito

También se puede hacer desarrollo usando entornos virtuales de Python para evitar interferencias
de módulos instalados de Python

Los tests funcionan en el testrunner de Pycharm, y también con el binario de pytest

Es importante crear un fichero de configuración en /data/config/config.yaml 
con los datos rellenos para poder desarrollar la aplicación.

## Producción

1- Instala [Docker](https://docs.docker.com/engine/install/#server)

2- Clona este repositorio en su rama ``desarrollo``

3- 

