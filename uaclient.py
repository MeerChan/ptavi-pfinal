#!/usr/bin/python3
"""
Programa cliente UDP que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import log rtp

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

def password(passwd, nonce):
    """Devuelve el nonce de respuesta."""
    m = hashlib.md5()
    m.update(bytes(passwd, 'utf-8'))
    m.update(bytes(nonce, 'utf-8'))
    return m.hexdigest()

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

        if METHOD == 'REGISTER':
            LINEA = (METHOD + ' sip:' + ADRESS + ':' + PUERTO +
                     ' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n\r\n')
        elif METHOD == 'INVITE':
            LINEA = (METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n' +
                     'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' +
                     'o=' + ADRESS + ' ' + IP + '\r\n' + 's=VoyALaCocina\r\n' +
                     'm=audio ' + str(PORT_AUDIO) + ' RTP' + '\r\n\r\n')
        elif METHOD == 'BYE':
            LINEA = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'
        else:
            LINEA = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'

        my_socket.send(bytes(LINEA, 'utf-8'))
        print('Enviamos al Proxy:\r\n', LINEA)
        linea_buena = LINEA.replace("\r\n", " ")
        log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
            lineao_buena, LOG_PATH)

        try:
            DATA_RECV = my_socket.recv(1024)
        except ConnectionRefusedError:
            sys.exit("Conexion fallida")
            log("Error: No server listening at " + SERVER_PROXY +
                " port " + str(PORT_PROXY), LOG_PATH)
        RECV = DATA_RECV.decode('utf-8')
        print('Recibo del Proxy:\r\n', RECV)
        RECV_bueno = RECV.replace("\r\n", " ")
        log('Received from ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
            RECV_bueno, LOG_PATH)

        RECV_SPLIT = RECV.split()
        if RECV_SPLIT[1] == '401':
            NONCE_RECV = RECV_SPLIT[mirar proxy].split('"')[mirar proxy]
            NONCE_RESP = password(PASSWD, NONCE_RECV)
            LINEA = (METHOD + ' sip:' + ADRESS + ':' + PUERTO +
                     ' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n' +
                     'Authorization: Digest response="' + NONCE_RESP + '"' +
                     '\r\n\r\n')
            my_socket.send(bytes(LINEA, 'utf-8'))
            print('Enviamos al Proxy:\r\n', LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                LINEA, LOG_PATH)
            DATA = my_socket.recv(1024)
            RECV = DATA.decode('utf-8')
            print('Recibo del Proxy:\r\n', RECV)
            MENS = RECV.replace("\r\n", " ")
            log('Received from ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                MENS, LOG_PATH)
        elif (RECV_SPLIT[1] == '100' and RECV_SPLIT[4] == '180' and
              RECV_SPLIT[7] == '200'):
            SERVER_IP = RECV_SPLIT[16]
            PORT_RTP = RECV_SPLIT[19]
            LINEA = 'ACK sip:' + OPTION + ' SIP/2.0\r\n\r\n'
            my_socket.send(bytes(LINEA, 'utf-8'))
            print('Enviamos al Proxy:\r\n', LINEA)
            LINEA = LINEA.replace("\r\n", " ")
            log('Sent to ' + IP_PROXY + ':' + str(PORT_PROXY) + ': ' +
                LINEA, LOG_PATH)
            print(SERVER_IP)
            LINEA = rtp(SERVER_IP, PORT_RTP, AUDIO_PATH)
            log('Sent to ' + SERVER_IP + ':' + PORT_RTP + ': ' +
                LINEA, LOG_PATH)
        elif RECV_SPLIT[1] == '404':
            log("Error: " + RECV, LOG_PATH)
        elif RECV_SPLIT[1] == '405':
            log("Error: " + RECV, LOG_PATH)
        elif RECV_SPLIT[1] == '400':
            log("Error: " + RECV, LOG_PATH)

        log('Finishing.', LOG_PATH)
