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
