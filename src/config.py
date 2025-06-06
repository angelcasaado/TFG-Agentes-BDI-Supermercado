"""
TFG-Agentes-BDI-Supermercado

Copyright (c) 2025 Angel Casado (https://github.com/angelcasaado)

Este archivo forma parte de TFG-Agentes-BDI-Supermercado.
Se distribuye bajo la licencia MIT. Para más detalles, consulta el archivo LICENSE
en la raíz del repositorio.
"""
import asyncio
decisiones_lock = asyncio.Lock()
ENABLE_VARIETY_CHANGE = True
VARIETY_CHANGE_INTERVAL = 20 
WEIGHT_ETHICAL = 1.0
# Importancia de la distancia
WEIGHT_DISTANCE = 0

MAX_PURCHASES = 750
THRESHOLD_INDISPENSABLE = 2
CERCANO_THRESHOLD = 200
NUM_SUPERMERCADOS = 15
NUM_INTELIGENTES = 2
NUM_CLIENTES = 50
adapatativo = "atraccion_clientes"
cambios_productos_log = []
productos_inteligentes_log = []
evaluacion_cambios_log = []
decisiones = []
historial_creencias = []
clients_finished = []
atraccion_eventos_log = []
###############################################################################
# Definición de Productos, Variedades y Valores Éticos Predefinidos
###############################################################################
possible_products = ["Manzana",
                     "Leche",
                     "Pan",
                     "Carne",
                     "Arroz",
                     "Pasta",
                     "Huevos",
                     "Jugo",
                     "Queso"]

possible_varieties = {
    "Manzana": ["Manzana_1", "Manzana_2", "Manzana_3", "Manzana_4", "Manzana_5"],
    "Leche": ["Leche_1", "Leche_2", "Leche_3", "Leche_4", "Leche_5"],
    "Pan": ["Pan_1", "Pan_2", "Pan_3", "Pan_4", "Pan_5"],
    "Carne": ["Carne_1", "Carne_2", "Carne_3", "Carne_4", "Carne_5"],
    "Arroz": ["Arroz_1", "Arroz_2", "Arroz_3", "Arroz_4", "Arroz_5"],
    "Pasta": ["Pasta_1", "Pasta_2", "Pasta_3", "Pasta_4", "Pasta_5"],
    "Huevos": ["Huevos_1", "Huevos_2", "Huevos_3", "Huevos_4", "Huevos_5"],
    "Jugo": ["Jugo_1", "Jugo_2", "Jugo_3", "Jugo_4", "Jugo_5"],
    "Queso": ["Queso_1", "Queso_2", "Queso_3", "Queso_4", "Queso_5"]
}

predefined_ethics = {}
for product in possible_products:
    if product in possible_varieties:
        for i in range(1, 6):
            variety_name = f"{product}_{i}"
            predefined_ethics[variety_name] = {
                "huella_ecologica": round(0.1 * i, 2),
                "producto_ecologico": round(1 - 0.1 * i, 2),
                "pocos_intermediarios": round(0.05 * i, 2),
                "alta_calidad": round(0.2 * i, 2),
                "origen_nacional": round(0.15 * i, 2),
                "origen_local": round(0.1 * i, 2),
                "origen_pais_desarrollo": round(0.05 * i, 2)
            }

USUARIO_JID_SUPER = [
    "tfgancasa3@jabber.hot-chilli.net",
    "tfgancasa4@jabber.hot-chilli.net",
    "tfgancasa7@jabber.hot-chilli.net"
]
USUARIO_JID_CLIENTE = [
    "tfgancasa6@jabber.hot-chilli.net",
    "tfgancasa5@jabber.hot-chilli.net",
    "tfgancasa8@jabber.hot-chilli.net",
    "tfgancasa9@jabber.hot-chilli.net",
    "tfgancasa10@jabber.hot-chilli.net",
    "tfgancasa11@jabber.hot-chilli.net",
    "tfgancasa12@jabber.hot-chilli.net",
    "tfgancasa13@jabber.hot-chilli.net"
]
PASSWORD_SUPER = ["usuario3", "usuario4", "usuario7"]
PASSWORD_CLIENTE = [
    "usuario6", "usuario5", "usuario8", "usuario9",
    "usuario10", "usuario11", "usuario12", "usuario13"
]

clientes_ubicaciones = {}
supermercados_ubicaciones = {}
relaciones = {}
