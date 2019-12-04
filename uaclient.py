#!/usr/bin/python3
"""
Programa cliente UDP que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import log

class UaHandler(ContentHandler):
    """Class Handler."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = {}
        self.dicc_uaxml = {'account': ['username', 'passwd'],
                            'uaserver': ['ip', 'puerto'],
                            'rtpaudio': ['puerto'],
                            'regproxy': ['ip', 'puerto'],
                            'log': ['path'], 'audio': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        if name in self.dicc_uaxml:
            for atributo in self.dicc_uaxml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario."""
        return self.diccionario


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python uaclient.py config method option")
    try:
        CONFIG = sys.argv[1]
        print(CONFIG)
        METHOD = sys.argv[2].upper()
        if METHOD != 'INVITE' and METHOD != 'BYE' and METHOD != 'REGISTER':
            sys.exit("Method must be REGISTER, INVITE or BYE")
        OPTION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")
    print("funciona")
    parser = make_parser()
    UHandler = UaHandler()
    parser.setContentHandler(UHandler)
    parser.parse(open(CONFIG))
    try:
        parser.parse(open(CONFIG))
    except IOError:
        sys.exit("Config: File not found")
    DICC_CONFIG = UHandler.get_tags()
    # COmprobamos si el xml leido nos da la ip del proxy, sino la asignamos
    if DICC_CONFIG['regproxy_ip'] == '':
        IP_PROXY = '127.0.0.1'
    else:
        IP_PROXY = DICC_CONFIG['regproxy_ip']
    # lo mismo con la ip del server
    if DICC_CONFIG['uaserver_ip'] == '':
        IP = '127.0.0.1'
    else:
        IP = DICC_CONFIG['uaserver_ip']
    # Guardamos los datos leidos en "constantes"
    PORT_PROXY = int(DICC_CONFIG['regproxy_puerto'])
    LOG_PATH = DICC_CONFIG['log_path']
    ADRESS = DICC_CONFIG['account_username']
    PUERTO = DICC_CONFIG['uaserver_puerto']
    PASSWD = DICC_CONFIG['account_passwd']
    PORT_AUDIO = int(DICC_CONFIG['rtpaudio_puerto'])
    AUDIO_PATH = DICC_CONFIG['audio_path']
    # EScribimos en el log
    log("Starting...", LOG_PATH)
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((IP_PROXY, PORT_PROXY))
        print("funciona")
