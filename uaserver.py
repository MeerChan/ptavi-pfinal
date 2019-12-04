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

class HandlerServer(socketserver.DatagramRequestHandler):
    """
    Handler
    """

def log(mensaje, log_path):
    """Abre un fichero log para poder escribir en el."""
    fich = open(log_path, "a")
    fich.write(time.strftime('%Y%m%d%H%M%S '))
    fich.write(mensaje+"\r\n")
    fich.close()


if __name__ == "__main__":

    if len(sys.argv) != 4:
        sys.exit("Usage: python3 server.py IP port audio_file")
    try:
        IPSERVER = sys.argv[1]
        PORTSERVER = int(sys.argv[2])
        AUDIO = sys.argv[3]
    except ValueError:
        sys.exit("Port must be a number")
    except IndexError:
        sys.exit("Usage: python3 server.py IP port audio_file")
    serv = socketserver.UDPServer((IPSERVER, PORTSERVER), SIPRegisterHandler)

    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
