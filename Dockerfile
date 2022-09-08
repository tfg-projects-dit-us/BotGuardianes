FROM ubuntu:22.04

ADD ./modulos /BotGuardianes/modulos
ADD ./MainBot.py /BotGuardianes
ADD ./requirements.txt /BotGuardianes
ADD ./config_ejemplo /BotGuardianes/config_ejemplo
RUN mkdir /BotGuardianes/data
WORKDIR /BotGuardianes
RUN apt update
RUN apt upgrade -y
RUN apt install python3.10 pip gettext-base language-pack-es -y
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt
