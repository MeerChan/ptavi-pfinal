#!/usr/bin/python3
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import UaHandler, log, rtp
import os

class HandlerServer(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    #Creo la lista rtp, que constara de una ip y un puerto
    rtp = []
    #Funcion para enviar mensajes al proxy
    def enviar_proxy(self, linea, ip, port):
        """Envia mensajes al proxy."""
        self.wfile.write(bytes(linea, 'utf-8'))
        print('Enviamos al Proxy:\r\n', linea)
        linea = linea.replace("\r\n", " ")
        log('Sent to ' + ip + ':' + port + ': ' + linea, LOG_PATH)

    def handle(self):
        Client_IP = str(self.client_address[0])
        Client_PORT = str(self.client_address[1])

        milinea = ''
        for line in self.rfile:
            milinea += line.decode('utf-8')
            linea_buena = milinea.replace("\r\n", " ")
            log('Received from ' + IP_PROXY + ':' +
                str(PORT_PROXY) + ': ' + linea_buena, LOG_PATH)
            print("llega ", milinea)

            line = milinea.split()
        if line[0] == 'INVITE':
            print(line)
            #Guardo la ip y el puerto donde enviare el audio
            self.rtp.append(line[10])
            self.rtp.append(line[13])
            mensaje = ('SIP/2.0 100 Trying\r\n\r\n' +
                       'SIP/2.0 180 Ringing\r\n\r\n' +
                       'SIP/2.0 200 OK\r\n' +
                       'Content-Type: application/sdp\r\n\r\n' +
                       'v=0\r\n' + 'o=' + ADRESS + ' ' + IP + '\r\n' +
                       's=misesion\r\n' + 'm=audio ' + str(PORT_AUDIO) +
                       ' RTP' + '\r\n\r\n')
            self.enviar_proxy(mensaje, Client_IP, Client_PORT)
        elif line[0] == 'ACK':
            print(self.rtp[0])
            print(self.rtp[1])
            mensaje = rtp(self.rtp[0], self.rtp[1], AUDIO_PATH)
            os.system(mensaje)
            log('Sent to ' + self.rtp[0] + ':' + str(self.rtp[1]) + ': ' +
                    mensaje, LOG_PATH)
        elif line[0] == 'BYE':
            mensaje = 'SIP/2.0 200 OK\r\n\r\n'
            self.enviar_proxy(mensaje, Client_IP, Client_PORT)
        elif line[0] != ('INVITE', 'ACK', 'BYE'):
            mensaje = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.enviar_proxy(mensaje, Client_IP, Client_PORT)
            log("Error: SIP/2.0 405 Method Not Allowed", LOG_PATH)
            print('El metodo esta mal escrito')
        else:
            mensaje = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            log("Error: SIP/2.0 400 Bad Request", LOG_PATH)
            print('No deberia llegar aqui, saltaria el error anterior ')

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python uaserver.py config")

    parser = make_parser()
    uHandler = UaHandler()
    parser.setContentHandler(uHandler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python uaserver.py config")
    CONFIGURACION = uHandler.get_tags()

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

    serv = socketserver.UDPServer((IP, PUERTO), HandlerServer)
    print('Listening...')
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
