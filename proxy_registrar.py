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
    dicc = {}

    def json2register(self):
        """Paso el json a mi diccionario REGISTER"""
        try:
            with open(REGISTRO, 'r') as jsonfile:
                self.dicc_reg = json.load(jsonfile)
        except FileNotFoundError:
            sys.exit("Config: File not found")

    def register2json(self):
        """
        escribo la variable dicc
        en formato json en elfichero registered.json
        """
        with open('registered.json', 'w') as jsonfile:
            json.dump(self.dicc, jsonfile, indent=4)

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
    # Listens at localhost ('') port 6001
    # and calls the EchoHandler class to manage the request
    if len(sys.argv) != 2:
        sys.exit("Usage: server.py port")
    try:
        PORTSERVER = int(sys.argv[1])
    except ValueError:
        sys.exit("Port must be a number")
    except IndexError:
        sys.exit("Usage: server.py port")
    serv = socketserver.UDPServer(('', PORTSERVER), SIPRegisterHandler)

    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
