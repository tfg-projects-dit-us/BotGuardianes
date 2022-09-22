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

Basta con copiar el config.yaml de la carpeta config_ejemplo y sustituir los valores necesarios

Para crear un bot nuevo basta con seguir la [guia de creacion de bot](https://core.telegram.org/bots#6-botfather)

Desde Botfather obtenemos el token del bot.

También hay que crear dos canales de Telegram, uno es el de Publicaciones de Guardias y el otro de Publicaciones para administradores.

Para crear un canal en Telegram, se pulsa en Nuevo Canal en la interfaz de Telegram. Para obtener la ID, basta con copiar el enlace de un mensaje del canal ya creado. 
Tendrá la estructura de https://t.me/c/ID_CANAL/ID_MENSAJE. Para poder utilizarlo en la configuración, se coloca -100 delante de la ID obtenida.
Ejemplo: -100XXXXXXXXXX

En la sección de "Producción" está explicado cada parámetro.

En el fichero REST_calendarios.postman_collection.json se encuentran las URL para hacer uso de la API REST. 
Si se quiere hacer uso de más secciones de la API, este fichero es necesario
## Generacion de documentación

Para generar la documentación, y con los requirements instalados, hay que abrir una sesión de consola,
navegar hasta la carpeta donde se sitúa el repositorio y ejecutar

``mkdocs build``

Esto generará la documentación en la carpeta site (omitida en .gitignore para no subirla al repositorio)

Para alojarla en el Github Pages, solo hay que enviar el comando

`` mkdocs gh-deploy``

Si queremos subirla a otra sección, tan solo hay que subir el contenido de la carpeta ``site`` al servidor deseado.

La configuración de mkdocs se hace en el fichero mkdocs.yml, y se indica en la sección nav qué ficheros en Markdown queremos utilizar para la navegación

Los ficheros .md contienen una cadena que mkdocstrings parsea desde los comentarios de código siguiendo el estilo de
[Google docstring](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings)

Para que el comentario se autogenere es necesario que el plugin mkdocstrings se mantenga en el fichero de configuración.


## Producción

1 - Instala [Docker](https://docs.docker.com/engine/install/#server)

2 - Clona este repositorio desde su rama ``desarrollo``

3 - Configura las variables de entorno en docker-compose.yml, que se necesitan de la configuración del proyecto https://github.com/tfg-projects-dit-us/ServicioDeCalendarios

Las primeras variables son para el servicio de almacenamiento de calendarios.

      - URL_SERVIDOR= Url del servidor DAViCal

      - CAL_PROPUESTAS= nombre del calendario de propuestas

      - CAL_PRINCIPAL= nombre del calendario principal

      - USER_CALENDAR=usuario para editar ambos calendarios

      - PASS_CALENDAR= contraseña para editar ambos calendarios


El segundo bloque para la API de Telegram

      - TOKEN_BOT=token obtenido en BotFather al crear el bot.

      - ID_CANAL= ID del canal donde se van a publicar las ofertas deactividad. Para obtenerlo, basta con copiar el enlace de un mensaje del canal ya creado.
        Tendrá la estructura de https://t.me/c/ID_CANAL/ID_MENSAJE. Para poder utilizarlo en la configuración, se coloca -100 delante de la ID obtenida
        Ejemplo -100XXXXXXXXXX
      - ID_CANAL_ADMIN= Siguiendo el mismo paso que antes, se configura la ID del canal de publicación de aprobaciones y denegaciones de cambios para administradores

El tercer bloque, después del PATH de SQLITE son variables para la API REST

      - REST_INSERTA_TELEGRAM_ID= url para insertar la ID de Telegram. Para la versión actual, esto es HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors/telegramID

      - REST_GET_ID_POR_EMAIL= url para obtener la ID del servicio REST a partir del email. Para la versión actual, HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors/idDoctor

      - REST_GET_NOMBRE_POR_ID= URL para obtener el nombre del doctor a partir de la ID del servicio REST. Para la versión actual, HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors

      - REST_GET_ID_REST_POR_ID_TEL= URL para obtener la ID del servicio REST a partir de la ID de TElegram. Para la versión actual, HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors/idDoctor

      - REST_GET_ROL= URL para obtener los roles de un doctor en la API REST. Para la versión actual, HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors/rol

      - REST_GET_TELEGRAM_ID= URL para obtener la ID de telegram a partir de la ID del servicio REST. Para la versión actual, HTTP://IP_SERVIDOR:PUERTO/guardians/api/doctors/telegramID
    
      - REST_EVENTO=URL para enviar un evento modificado al calendario del servicio REST

      - REST_PASSWORD=Password para utilizar el servicio REST

      - REST_USUARIO= usuario para utilizar el servicio REST.

4 - Si se cambia el repositorio de Dockerhub donde se almacena, se debe indicar en la línea image: y colocar el correspondiente.

5 - La API REST y el servicio de alojamiento de calendarios deben estar iniciados antes que este servicio

6 - Se puede utilizar docker-compose-completo.yml para iniciar todos los servicios necesarios a la vez. 
Si se inicia por primera vez con este fichero, es necesario configurar un usuario en DAViCal y crear el calendario de propuestas y principal para dicho usuario.

