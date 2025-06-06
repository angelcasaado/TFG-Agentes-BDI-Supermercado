"""
TFG-Agentes-BDI-Supermercado

Copyright (c) 2025 Angel Casado (https://github.com/angelcasaado)

Este archivo forma parte de TFG-Agentes-BDI-Supermercado.
Se distribuye bajo la licencia MIT. Para más detalles, consulta el archivo LICENSE
en la raíz del repositorio.
"""
class Deseo:
    def __init__(self, nombre, parametros=None, prioridad=1):
        self.nombre = nombre
        self.parametros = parametros if parametros is not None else {}
        self.prioridad = prioridad
        
    def __repr__(self):
        return f"Deseo({
            self.nombre}, {
            self.parametros}, prioridad={
            self.prioridad})"
