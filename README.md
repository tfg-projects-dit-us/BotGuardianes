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

## Generacion de documentación

Para generar la documentación, y con los requirements instalados, hay que abrir una sesión de consola,
navegar hasta la carpeta donde se sitúa el repositorio y ejecutar

``mkdocs build``

Esto generará la documentación en la carpeta site (omitida para no subirla al repositorio)

Para alojarla en el Github Pages, solo hay que enviar el comando

`` mkdocs gh-deploy``

Si queremos subirla a otra sección, tan solo hay que subir el contenido de la carpeta site al servidor deseado.

La configuración de mkdocs se hace en el fichero mkdocs.yml, y se indica en la sección nav qué ficheros en Markdown queremos utilizar para la navegación

Los ficheros .md contienen una cadena que mkdocstrings parsea desde los comentarios de código siguiendo el estilo de
[Google docstring](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings)

Para que el comentario se autogenere es necesario que el plugin mkdocstrings se mantenga en el fichero de configuración.


## Producción

1 - Instala [Docker](https://docs.docker.com/engine/install/#server)

2 - Clona este repositorio en su rama ``desarrollo``

3 - Configura las variables de entorno en docker-compose.yml. 
Las primeras variables son para el servicio de almacenamiento de calendarios.

El segundo bloque para la API de Telegram

El tercer bloque, después del PATH de SQLITE son variables para la API REST

4 - Si se cambia el repositorio de Dockerhub, se debe indicar en la línea image: y colocar el correspondiente.

5 - La API REST y el servicio de alojamiento de calendarios deben estar iniciados antes que este servicio

6 - Se puede utilizar docker-compose-completo.yml para iniciar todos los servicios necesarios a la vez. 
Si se inicia por primera vez con este fichero, es necesario configurar un usuario en DAViCal y crear el calendario de propuestas y principal para dicho usuario.
