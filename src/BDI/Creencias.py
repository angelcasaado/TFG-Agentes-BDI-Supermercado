"""
TFG-Agentes-BDI-Supermercado

Copyright (c) 2025 Angel Casado (https://github.com/angelcasaado)

Este archivo forma parte de TFG-Agentes-BDI-Supermercado.
Se distribuye bajo la licencia MIT. Para más detalles, consulta el archivo LICENSE
en la raíz del repositorio.
"""
class Creencias:
    def __init__(self):
        self.data = {}

    def actualizar(self, key, value):
        self.data[key] = value

    def obtener(self, key):
        return self.data.get(key, None)

    def __repr__(self):
        return str(self.data)
