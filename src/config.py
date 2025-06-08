import asyncio

# Bloqueo para asegurar la exclusión mutua en decisiones concurrentes
decisiones_lock = asyncio.Lock()

# -----------------------------------------------------------------------------
# Parámetros de comportamiento de cambio de variedades en supermercados normales
# -----------------------------------------------------------------------------
# Habilita o deshabilita la rotación automática de variedades de super normal
ENABLE_VARIETY_CHANGE = True
# Intervalo en segundos para cambiar variedades si está habilitado 
VARIETY_CHANGE_INTERVAL = 20

# -----------------------------------------------------------------------------
# Pesos para la función de puntuación de los clientes
# -----------------------------------------------------------------------------
# Peso relativo de criterios éticos en la elección de supermercado
WEIGHT_ETHICAL = 1.0
# Peso relativo de la distancia en la elección de supermercado
WEIGHT_DISTANCE = 0

# -----------------------------------------------------------------------------
# Límites y umbrales de compras de los clientes
# -----------------------------------------------------------------------------
# Máximo número de rondas de compra permitidas
MAX_PURCHASES = 750
# Umbral mínimo de unidades para considerar un producto como indispensable
THRESHOLD_INDISPENSABLE = 2

# -----------------------------------------------------------------------------
# Parámetros de proximidad y cantidad de agentes
# -----------------------------------------------------------------------------
# Distancia máxima (euclidiana) para considerar ventas cercanas
CERCANO_THRESHOLD = 200
# Número de supermercados normales en la simulación
NUM_SUPERMERCADOS = 15
# Número de supermercados inteligentes en la simulación
NUM_INTELIGENTES = 2
# Número de clientes en la simulación
NUM_CLIENTES = 50

# Modo adaptativo por defecto para supermercados inteligentes
# Opciones: "atraccion_clientes" o "reevaluacion_productos"
adaptativo = "atraccion_clientes"

# Listas globales para llevar logs y estado de la simulación
cambios_productos_log = []       # Registra cambios de variedades en inteligentes
productos_inteligentes_log = []  # Captura inventario tras adaptación
evaluacion_cambios_log = []      # Detalles de evaluación de ventas cercanas
decisiones = []                  # Historial de decisiones de clientes
historial_creencias = []         # Registro de cambios de creencias
clients_finished = []            # Clientes que han terminado su ciclo
atraccion_eventos_log = []       # Eventos de atracción/adopción de catálogo

# -----------------------------------------------------------------------------
# Definición de Productos, Variedades y Valores Éticos Predefinidos
# -----------------------------------------------------------------------------
# Lista de nombres de productos manejados en la simulación
possible_products = [
    "Manzana",
    "Leche",
    "Pan",
    "Carne",
    "Arroz",
    "Pasta",
    "Huevos",
    "Jugo",
    "Queso",
]

# Variedades disponibles para cada producto
possible_varieties = {
    "Manzana": [f"Manzana_{i}" for i in range(1, 6)],
    "Leche":   [f"Leche_{i}"   for i in range(1, 6)],
    "Pan":     [f"Pan_{i}"     for i in range(1, 6)],
    "Carne":   [f"Carne_{i}"   for i in range(1, 6)],
    "Arroz":   [f"Arroz_{i}"   for i in range(1, 6)],
    "Pasta":   [f"Pasta_{i}"   for i in range(1, 6)],
    "Huevos":  [f"Huevos_{i}"  for i in range(1, 6)],
    "Jugo":    [f"Jugo_{i}"    for i in range(1, 6)],
    "Queso":   [f"Queso_{i}"   for i in range(1, 6)],
}

# Diccionario para almacenar valores éticos predeterminados por variedad
predefined_ethics = {}
for product in possible_products:
    # Solo procesar si existen variedades definidas
    if product in possible_varieties:
        for i in range(1, 6):
            variety_name = f"{product}_{i}"
            # Cada criterio ético escala con el índice de variedad
            predefined_ethics[variety_name] = {
                "huella_ecologica":      round(0.1 * i, 2),  # Impacto ambiental
                "producto_ecologico":    round(1 - 0.1 * i, 2),  # % ecológico
                "pocos_intermediarios":  round(0.05 * i, 2),    # Cadena corta
                "alta_calidad":          round(0.2 * i, 2),     # Calidad percibida
                "origen_nacional":       round(0.15 * i, 2),    # % nacional
                "origen_local":          round(0.1 * i, 2),     # % local
                "origen_pais_desarrollo":round(0.05 * i, 2),    # % país en desarrollo
            }

# -----------------------------------------------------------------------------
# Credenciales y JIDs para agentes SPADE
# -----------------------------------------------------------------------------
# JIDs de administradores (supermercados)
USUARIO_JID_SUPER = [
    "tfgancasa3@jabber.hot-chilli.net",
    "tfgancasa4@jabber.hot-chilli.net",
    "tfgancasa7@jabber.hot-chilli.net",
]
# JIDs de clientes
USUARIO_JID_CLIENTE = [
    "tfgancasa6@jabber.hot-chilli.net",
    "tfgancasa5@jabber.hot-chilli.net",
    "tfgancasa8@jabber.hot-chilli.net",
    "tfgancasa9@jabber.hot-chilli.net",
    "tfgancasa10@jabber.hot-chilli.net",
    "tfgancasa11@jabber.hot-chilli.net",
    "tfgancasa12@jabber.hot-chilli.net",
    "tfgancasa13@jabber.hot-chilli.net",
]
# Contraseñas correspondientes (índice paralelo a JIDs)
PASSWORD_SUPER = ["usuario3", "usuario4", "usuario7"]
PASSWORD_CLIENTE = [
    "usuario6", "usuario5", "usuario8", "usuario9",
    "usuario10", "usuario11", "usuario12", "usuario13",
]

# Diccionarios para mapear ubicaciones dinámicamente
clientes_ubicaciones = {}        # { cliente_id: (x, y) }
supermercados_ubicaciones = {}   # { supermercado_id: (x, y) }
# Relaciones entre entidades (opcional)
relaciones = {}
