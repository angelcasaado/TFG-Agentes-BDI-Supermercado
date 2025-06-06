"""
TFG-Agentes-BDI-Supermercado

Copyright (c) 2025 Angel Casado (https://github.com/angelcasaado)

Este archivo forma parte de TFG-Agentes-BDI-Supermercado.
Se distribuye bajo la licencia MIT. Para más detalles, consulta el archivo LICENSE
en la raíz del repositorio.
"""
class Intencion:

    def __init__(self, deseo, plan):
        self.deseo = deseo
        self.plan = plan

    def __repr__(self):
        return f"Intencion(deseo={self.deseo}, plan={self.plan})"
