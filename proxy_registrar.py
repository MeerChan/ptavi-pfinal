# !/usr/bin/python3
"""Programa de un servidor-proxy."""
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socket
import time
import json
from uaclient import log, password
import random


class PrHandler(ContentHandler):
    """Class Handler."""

    def __init__(self):
        """Inicializo los diccionarios."""
        self.diccionario = {}
        self.dicc_prxml = {'server': ['name', 'ip', 'puerto'],
                           'database': ['path', 'passwdpath'],
                           'log': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        diccionario = {}
        if name in self.dicc_prxml:
            for atributo in self.dicc_prxml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Echo server class."""

    dicc_reg = {}
    dicc_passw = {}
    nonce = {}

    def json2password(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(PASSWORDS, 'r') as jsonfile:
                self.dicc_passw = json.load(jsonfile)
        except FileNotFoundError:
            pass

    def register2json(self):
        """Escribir dicc en formato json en el fichero que nos dice el xml."""
        with open(REGISTERS, 'w') as jsonfile:
            json.dump(self.dicc_reg, jsonfile, indent=4)

    def enviar_cliente(self, ip, port, linea):
        """Envio mensajes al uaclient."""
        self.wfile.write(bytes(linea, 'utf-8'))
        print('mandamos al cliente: ', linea)
        linea_buena = linea.replace("\r\n", " ")
        log('Sent to ' + ip + ':' + str(port) + ': ' + linea_buena, LOG_PATH)

    def enviar_server(self, ip, port, mensaje):
        """Envio los mensajes al uaserver."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip, port))
            mensaje_split = mensaje.split('\r\n\r\n')
            mens_proxy = (mensaje_split[0] + '\r\nVia: SIP/2.0/UDP ' +
                          IP + ':' + str(PORT_SERVER) + '\r\n\r\n' +
                          mensaje_split[1])
            print('mandamos al servidor: ', mens_proxy)
            my_socket.send(bytes(mens_proxy, 'utf-8'))
            mens_proxy = mens_proxy.replace("\r\n", " ")
            log('Sent to ' + ip + ':' + str(port) + ': ' +
                mens_proxy, LOG_PATH)

            try:
                data = my_socket.recv(1024).decode('utf-8')
                print('recibimos del servidor: ', data)
            except ConnectionRefusedError:
                log("Error: No server listening at " + ip +
                    " port " + str(port), LOG_PATH)
            RECB = data.split()
            env_proxy = ''
            try:
                if RECB[7] == '200':
                    recb_proxy = data.split('\r\n\r\n')
                    env_proxy = (recb_proxy[0] + '\r\n\r\n' + recb_proxy[1] +
                                 '\r\n\r\n' + recb_proxy[2] +
                                 '\r\nVia: SIP/2.0/UDP ' + IP + ':' +
                                 str(PORT_SERVER) + '\r\n\r\n' + recb_proxy[3])
            except IndexError:
                env_proxy = data
            if env_proxy != '':
                log_send = env_proxy.replace("\r\n", " ")
                log('Received from ' + ip + ':' +
                    str(port) + ': ' + log_send, LOG_PATH)
                self.enviar_cliente(ip, port, env_proxy)

    def user_not_found(self):
        """Mensaje de usuario no encontrado."""
        linea_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
        log_send = linea_send.replace("\r\n", " ")
        log('Error: ' + log_send, LOG_PATH)
        self.wfile.write(bytes(linea_send, 'utf-8'))

    def handle(self):
        """Escribe dirección y puerto del cliente."""
        ip_client = str(self.client_address[0])
        port_client = str(self.client_address[1])
        self.json2password()
        milinea = ''
        for line in self.rfile:
            milinea += line.decode('utf-8')
            linea_buena = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_buena, LOG_PATH)
            milinea_split = milinea.split()
        if milinea_split[0] == 'REGISTER' and len(milinea_split) == 5:
            # Si la longuitud es 5, primer register
            TimeExp = time.time() + int(milinea_split[4])
            now = time.time()
            user = milinea_split[1].split(':')[1]
            port = milinea_split[1].split(':')[2]
            linea_recb = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_recb, LOG_PATH)
            if user in self.dicc_passw.keys():
                if user in self.dicc_reg.keys():
                    if milinea_split[4] == '0':
                        # si el expires es 0 lo borro
                        del self.dicc_reg[user]
                        linea_send = "SIP/2.0 200 OK\r\n\r\n"
                    else:
                        # es raro que llegue aqui
                        self.dicc_reg[user] = {'ip': ip_client,
                                               'expires': TimeExp,
                                               'puerto': port,
                                               'registro': now}
                        linea_send = "SIP/2.0 200 OK\r\n\r\n"
                else:
                    # como es el primer register, le mando el nonce
                    self.nonce[user] = str(random.randint(0, 100000000))
                    linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                                  'WWW Authenticate: Digest ' +
                                  'nonce="' + self.nonce[user] +
                                  '""\r\n\r\n')
                self.enviar_cliente(ip_client, port_client, linea_send)
            else:
                self.user_not_found()
        elif milinea_split[0] == 'REGISTER' and len(milinea_split) == 8:
            TimeExp = time.time() + int(milinea_split[4])
            now = time.time()
            user = milinea_split[1].split(':')[1]
            port = milinea_split[1].split(':')[2]
            linea_recb = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_recb, LOG_PATH)
            passw = self.dicc_passw[user]['passwd']
            nonce = password(passw, self.nonce[user])
            nonce_recv = milinea_split[7].split('"')[1]
            # si el nonce es bueno lo regisstro
            if nonce == nonce_recv:
                if milinea_split[4] == '0':
                    del self.dicc_reg[user]
                    linea_send = "SIP/2.0 200 OK\r\n\r\n"
                else:
                    self.dicc_reg[user] = {'ip': ip_client,
                                           'expires': TimeExp,
                                           'puerto': port,
                                           'registro': now}
                    linea_send = "SIP/2.0 200 OK\r\n\r\n"
            else:
                self.nonce[user] = str(random.randint(0, 100000000))
                linea_send = ('SIP/2.0 401 Unauthorized\r\n' +
                              'WWW Authenticate: Digest ' +
                              'nonce="' + self.nonce[user] +
                              '"\r\n\r\n')
            self.enviar_cliente(ip_client, port_client, linea_send)
        elif milinea_split[0] == 'INVITE':
            linea_recb = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_recb, LOG_PATH)
            user = milinea_split[6].split('=')[1]
            if user in self.dicc_reg.keys():
                server = milinea_split[1].split(':')[1]
                if server in self.dicc_reg.keys():
                    ip_destino = self.dicc_reg[server]['ip']
                    port_destino = int(self.dicc_reg[server]['puerto'])
                    self.enviar_server(ip_destino, port_destino, milinea)
                else:
                    self.user_not_found()
            else:
                self.user_not_found()
        elif milinea_split[0] == 'ACK':
            linea_recb = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_recb, LOG_PATH)
            server = milinea_split[1].split(':')[1]
            if server in self.dicc_reg.keys():
                ip_destino = self.dicc_reg[server]['ip']
                port_destino = int(self.dicc_reg[server]['puerto'])
                self.enviar_server(ip_destino, port_destino, milinea)
            else:
                self.user_not_found()
        elif milinea_split[0] == 'BYE':
            linea_recb = milinea.replace("\r\n", " ")
            log('Received from ' + ip_client + ':' +
                port_client + ': ' + linea_recb, LOG_PATH)
            server = milinea_split[1].split(':')[1]
            if server in self.dicc_reg.keys():
                ip_destino = self.dicc_reg[server]['ip']
                port_destino = int(self.dicc_reg[server]['puerto'])
                self.enviar_server(ip_destino, port_destino, milinea)
            else:
                self.user_not_found()
        elif milinea_split[0] != ('REGISTER', 'INVITE', 'ACK', 'BYE'):
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
            log("Error: SIP/2.0 405 Method Not Allowed", LOG_PATH)
            print('metodo erroneo')
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n\r\n")
            log("Error: SIP/2.0 400 Bad Request", LOG_PATH)
            print('no deberia llegar aqui')
        self.register2json()


if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except (IndexError, ValueError):
        sys.exit("Usage: python proxy_registrar.py config")

    parser = make_parser()
    pHandler = PrHandler()
    parser.setContentHandler(pHandler)
    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError:
        sys.exit("Usage: python proxy_registrar.py config")
    CONFIGURACION = pHandler.get_tags()

    if CONFIGURACION['server_ip'] == '':
        IP = '127.0.0.1'
    else:
        IP = CONFIGURACION['server_ip']

    PORT_SERVER = int(CONFIGURACION['server_puerto'])
    PROXY = CONFIGURACION['server_name']
    LOG_PATH = CONFIGURACION['log_path']
    REGISTERS = CONFIGURACION['database_path']
    PASSWORDS = CONFIGURACION['database_passwdpath']

    serv = socketserver.UDPServer((IP, PORT_SERVER), SIPRegisterHandler)
    print("Server " + PROXY + " listening at port " + str(PORT_SERVER))
    log("Starting...", LOG_PATH)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        log("Finishing.", LOG_PATH)
