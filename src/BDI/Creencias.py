class Creencias:
    def __init__(self):
        self.data = {}

    def actualizar(self, key, value):
        self.data[key] = value

    def obtener(self, key):
        return self.data.get(key, None)

    def __repr__(self):
        return str(self.data)
