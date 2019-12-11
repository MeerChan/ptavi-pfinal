#!/usr/bin/python3

import socketserver
import sys
import time
import json

class PrHandler(ContentHandler):
    """Class Handler."""

    def __init__(self):
        """Inicializo los diccionarios"""
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
    """
    Echo server class
    """
    dicc_reg = {}
    dicc_passw = {}

    def json2register(self):
        """Paso el json a mi diccionario REGISTER"""
        try:
            with open(REGISTERS, 'r') as jsonfile:
                self.dicc_reg = json.load(jsonfile)
        except FileNotFoundError:
            pass

    def json2password(self):
        """Descargo fichero json en el diccionario."""
        try:
            with open(PASSWORDS, 'r') as jsonfile:
                self.dicc_passw = json.load(jsonfile)
        except FileNotFoundError:
            pass

    def register2json(self):
        """
        Escribir diccionario.
        En formato json en el fichero que nos dice el xml
        """
        with open(REGISTERS, 'w') as jsonfile:
            json.dump(self.dicc_reg, jsonfile, indent=4)



    def handle(self):
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        # COmpruebo si ya esta creado el json
        self.json2register()
        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        milinea = ''
        for line in self.rfile:
            milinea += line.decode('utf-8')
        if milinea != '\r\n':
            print("El cliente nos manda ", milinea)
            # Quitamosos el expires: que no usamos con _
            (peticion, address, sip, _, expire) = milinea.split()
            if peticion == 'REGISTER':
                IP = self.client_address[0]
                # quito el sip, quedandome con el segundo obejeto del split
                user = address.split(':')[1]
                # Timpo en el que caducaria la sesion (actual+expires)
                Tiempo = time.time() + int(expire)
                # convierto el tiempo a horas min segundos
                TiempoHMS = time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.gmtime(Tiempo))
                # tiempo actual
                Ahora = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.gmtime(time.time()))
                self.dicc[user] = {'address': IP, 'expires': TiempoHMS}
                userBorrados = []
                for user in self.dicc:
                    if Ahora >= self.dicc[user]['expires']:
                        userBorrados.append(user)
                # COmo no podemos modificar el tamaño del diccionario mientras
                # lo recorremos necesitamos hacer esto
                for user in userBorrados:
                    del self.dicc[user]
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
