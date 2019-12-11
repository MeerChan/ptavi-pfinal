#!/usr/bin/python3
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import time
import json
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import UaHandler

class HandlerServer(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    
    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """

        milinea = ''
        for line in self.rfile:
            milinea += line.decode('utf-8')
        if milinea != '\r\n':
            (peticion, sipLOGIN_ip, port) = milinea.split()
            if peticion == 'INVITE':
                self.wfile.write(b"SIP/2.0 100 TRYING\r\n\r\n"
                                 + b"SIP/2.0 180 RINGING\r\n\r\n"
                                 + b"SIP/2.0 200 OK\r\n\r\n")
            elif peticion == 'ACK':
                # aEjecutar es un string
                # con lo que se ha de ejecutar en la shell
                aEjecutar = 'mp32rtp -i 127.0.0.1 -p 23032 < ' + AUDIO
                print("Se ejecuta: ", aEjecutar)
                os.system(aEjecutar)
            elif peticion == 'BYE':
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            elif peticion != ('INVITE', 'ACK', 'BYE'):
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                # nunca deberia llegar a aqui si se usa mi cliente
                self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")

def log(mensaje, log_path):
    """Abre un fichero log para poder escribir en el."""
    fich = open(log_path, "a")
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(mensaje+"\r\n")
    fich.close()

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python uaserver.py config")

    parser = make_parser()
    uHandler = UaHandler()
    parser.setContentHandler(u2Handler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = u2Handler.get_tags()

    if CONFIGURACION['uaserver_ip'] == '':
        IP = '127.0.0.1'
    else:
        IP = CONFIGURACION['uaserver_ip']
    if CONFIGURACION['regproxy_ip'] == '':
        IP_PROXY = '127.0.0.1'
    else:
        IP_PROXY = CONFIGURACION['regproxy_ip']

    LOG_PATH = CONFIGURACION['log_path']
    PUERTO = int(CONFIGURACION['uaserver_puerto'])
    PORT_PROXY = int(CONFIGURACION['regproxy_puerto'])
    ADRESS = CONFIGURACION['account_username']
    PORT_AUDIO = int(CONFIGURACION['rtpaudio_puerto'])
    AUDIO_PATH = CONFIGURACION['audio_path']

    serv = socketserver.UDPServer((IP, PUERTO), EchoHandler)
    print('Listening...')
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
