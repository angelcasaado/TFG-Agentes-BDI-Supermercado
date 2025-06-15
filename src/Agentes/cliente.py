from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour

from spade.message import Message
from ..logger import *
from ..config import *
import random
import datetime
from ..BDI.Creencias import *
from ..BDI.Deseo import *
from ..BDI.Intenciones import *
import json
import asyncio
import math
class CicloBDIBehaviour(PeriodicBehaviour):
    """
    Un único behaviour periódico que implementa el ciclo BDI:
    1) Revisión de creencias
    2) Generación de deseos / opciones
    3) Deliberación → elección de intención
    4) Planificación/Ejecución → lanzar el behaviour correspondiente
    """
    async def run(self):
        agent = self.agent

        # 1) Revisión de creencias: limpiar ofertas caducadas
        await agent.revisar_creencias()

        # 2) Solicitar ofertas de supermercados faltantes
        
        for sup_jid in agent.supermercados_recursos:
            payload = {"info": "Hola desde el cliente!"}
           
            msg = Message(to=str(sup_jid))
            msg.body = json.dumps({
                "tipo": "Peticion_Cliente",
                "payload": payload
            })
            await self.send(msg)

        # 3) Deliberación: elegir plan según compras e inventario
        num_compras = agent.creencias.obtener("numero_compras") or 0
        inventario = agent.creencias.obtener("productos_obtenidos") or {}
      
        if num_compras >= MAX_PURCHASES:
            plan = "finalizar"
        else:
            faltantes = [
                p for p in agent.indispensables
                if inventario.get(p, 0) < THRESHOLD_INDISPENSABLE
            ]
            if faltantes:
                plan = "compra_indispensable"
            elif sum(inventario.values()) < 8:
                plan = "compra_normal"
            else:
                plan = "consumo"

        # 4) Ejecución: lanzar el behaviour correspondiente
        if plan == "finalizar":
            agent.add_behaviour(HandleFinalizacionBehaviour())
        elif plan == "compra_indispensable":
            agent.add_behaviour(CompraIndispensableBehaviour(faltantes))
        elif plan == "compra_normal":
            agent.add_behaviour(CompraNormalBehaviour())
        else:  # consumo
            agent.add_behaviour(ConsumoBehaviour())

        # Registrar la intención (útil para logging/trazabilidad)
        nueva_int = Intencion(Deseo(plan), f"Plan → {plan}")
        agent.intentions.append(nueva_int)

        
class ClienteAgent(Agent):
    def __init__(
            self,
            jid,
            password,
            cliente_id,
            supermercados_recursos,
            possible_products,
            desires=None):
        """
        Inicializa un agente cliente.

        Parámetros:
            jid (str): JID base del cliente.
            password (str): Contraseña de XMPP.
            cliente_id (str): Identificador único (p. ej. "CLIENTE_1").
            supermercados_recursos (list): Lista de JIDs de supermercados a consultar.
            possible_products (list): Lista de nombres de productos posibles.
            desires (list, opcional): Deseos iniciales; si es None, se generan por defecto.
        """
        x, y = random.randint(0, 100), random.randint(0, 100)
        full_jid = f"{jid}/{cliente_id}"
        super().__init__(full_jid, password)
        self.cliente_id = cliente_id
        self.full_jid = full_jid
        self.ubicacion = (x, y)
        self.usar_ubicacion = True
        initial_products = random.sample(possible_products, k=2)
        self.possible_products = possible_products
        self.supermercados_recursos = supermercados_recursos
        clientes_ubicaciones[self.cliente_id] = self.ubicacion
        self.creation_time = datetime.datetime.now()
        self.creencias = Creencias()
        self.creencias.actualizar("supermercados", {})
        self.creencias.actualizar("numero_compras", 0)
        self.creencias.actualizar(
            "productos_obtenidos", {
                p: 0 for p in possible_products})
        valores_eticos = {
            "huella_ecologica": round(random.uniform(0, 1), 2),
            "producto_ecologico": round(random.uniform(0, 1), 2),
            "pocos_intermediarios": round(random.uniform(0, 1), 2),
            "alta_calidad": round(random.uniform(0, 1), 2),
            "origen_nacional": round(random.uniform(0, 1), 2),
            "origen_local": round(random.uniform(0, 1), 2),
            "origen_pais_desarrollo": round(random.uniform(0, 1), 2)
        }
        self.creencias.actualizar("valores_eticos", valores_eticos)
        compro_lo_de_siempre = random.choice([True, False])
        self.creencias.actualizar("compro_lo_de_siempre", compro_lo_de_siempre)
        self.indispensables = random.sample(possible_products, k=3)
        if desires is None:
            self.desires = [
                Deseo(
                    "comprar_productos", {
                        "productos": initial_products}, prioridad=1), Deseo(
                    "minimizar_distancia", prioridad=1)]
        else:
            self.desires = desires
        self.intentions = []
        self.pensando = False
        self.creencias_lock = asyncio.Lock()
    async def revisar_creencias(self):
        """
        Ahora protegemos la lectura-escritura de self.creencias con el lock.
        """
        async with self.creencias_lock:
            actuales = self.creencias.obtener("supermercados") or {}
            frescos = {}
            now = datetime.datetime.now()
            for sup_jid, datos in actuales.items():
                ts = datos.get("timestamp")
                if ts is None or (now - ts).total_seconds() < 30:
                    frescos[sup_jid] = datos
            self.creencias.actualizar("supermercados", frescos)

    def calcular_distancia(self, ubicacion_super):
        """
        Calcula la distancia euclídea desde el cliente hasta un supermercado.

        Parámetros:
            ubicacion_super (tuple): Coordenadas (x, y) del supermercado.

        Retorna:
            float: Distancia calculada.
        """
        return math.sqrt((self.ubicacion[0] - ubicacion_super[0])**2 +
                         (self.ubicacion[1] - ubicacion_super[1])**2)

    def calcular_mejor_supermercado(self):
            """
            Determina el supermercado óptimo según:
            - Preferencias éticas del cliente (ponderadas por WEIGHT_ETHICAL).
            - Distancia al supermercado (ponderada por WEIGHT_DISTANCE).
            
            Retorna:
                str: JID del supermercado con mejor puntuación.
            """
            best_supermercado = None
            best_score = -float('inf')
            valores_eticos = self.creencias.obtener("valores_eticos")

            # Pesos globales definidos al inicio del módulo
            priority_ethical = WEIGHT_ETHICAL
            priority_distance = WEIGHT_DISTANCE
            total_priority = priority_ethical + priority_distance

            for supermercado, data in self.creencias.obtener("supermercados").items():
                productos, ubicacion = data["productos"], data["ubicacion"]
                # Calcular distancia solo si el cliente usa ubicación
                distance = self.calcular_distancia(ubicacion) if self.usar_ubicacion else 0

                # Calcular la puntuación ética según los valores del cliente y los criterios del producto
                ethical_score = 0
                for prod in self.possible_products:
                    if prod in productos and productos[prod].get("stock", 0) > 0:
                        for criterio, valor_producto in productos[prod].items():
                            if criterio in ("stock", "variedad"):
                                continue
                            if criterio in valores_eticos:
                                valor_cliente = valores_eticos[criterio]
                                ethical_score += valor_cliente * valor_producto

                # Puntuación final: proporción de ética menos proporción de distancia
                score_final = (
                    (priority_ethical / total_priority) * ethical_score
                    - (priority_distance / total_priority) * distance
                )

                if score_final > best_score:
                    best_score = score_final
                    best_supermercado = supermercado

            return best_supermercado
    async def setup(self):
        logging.info(f"[{self.cliente_id}] Iniciado en {self.ubicacion}.")
        # petición inicial
        self.add_behaviour(CicloBDIBehaviour(period=5))
        self.add_behaviour(self.RecibirMensaje())
        
        # revisión periódica de intención
        
    class RecibirMensaje(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            try:
                body = msg.body or ""
                data = None
                data = json.loads(body)
                if data.get("tipo") == "Peticion_Cliente":
                    datos = json.loads(msg.body)
                    creencias = self.agent.creencias.obtener("supermercados") or {}
                    creencias[str(msg.sender)] = {
                        "productos": datos["productos"],
                        "ubicacion": datos["ubicacion"],
                        "timestamp": datetime.datetime.now()
                    }
                    self.agent.creencias.actualizar("supermercados", creencias)
                    logging.info(f"[{self.agent.cliente_id}] Oferta de {msg.sender} recibida.")
            except json.JSONDecodeError:
                pass
            
                        





class HandleFinalizacionBehaviour(OneShotBehaviour):
    async def run(self):
        inventario = self.agent.creencias.obtener("productos_obtenidos")
        # Consumo final si queda algo
        if sum(inventario.values()) > 0:
            consumo = {}
            inventario_previo = dict(inventario)
            for prod, qty in inventario.items():
                if qty > 0:
                    consumo[prod] = 1
                    inventario[prod] -= 1
            self.agent.creencias.actualizar("productos_obtenidos", inventario)
            decision = {
                "cliente_id": self.agent.cliente_id,
                "accion": "consumo",
                "productos_consumidos": consumo,
                "inventario_previo": inventario_previo,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "numero_compra": self.agent.creencias.obtener("numero_compras")
            }
            async with decisiones_lock:
                decisiones.append(decision)

        # Registro de final
        final_decision = {
            "cliente_id": self.agent.cliente_id,
            "accion": "final",
            "mensaje": (
                "Ha terminado (consumo final)" 
                if sum(inventario.values()) >= 0 
                else "Ha terminado (sin inventario)"),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "numero_compra": self.agent.creencias.obtener("numero_compras")
        }
        async with decisiones_lock:
            decisiones.append(final_decision)
            if self.agent.cliente_id not in clients_finished:
                clients_finished.append(self.agent.cliente_id)


class CompraIndispensableBehaviour(OneShotBehaviour):
    def __init__(self, faltantes):
        super().__init__()
        self.faltantes = faltantes

    async def run(self):
        # 0) Evitar exceso y leer número de compras bajo lock
        async with self.agent.creencias_lock:
            num_cmp = self.agent.creencias.obtener("numero_compras") or 0
            if num_cmp >= MAX_PURCHASES:
                return

            # 1) Elegir supermercado
            best_super = self.agent.calcular_mejor_supermercado()
            if not best_super:
                return

            # Obtener datos del supermercado y del inventario
            creencias_sup = self.agent.creencias.obtener("supermercados")
            sup_data = creencias_sup[best_super]
            productos_sup = sup_data["productos"]
            inventario = self.agent.creencias.obtener("productos_obtenidos")

            # 2) Preparar la compra
            new_purchase = {}
            for prod in self.faltantes:
                stock_disp = productos_sup.get(prod, {}).get("stock", 0)
                if stock_disp > 0:
                    qty = min(random.randint(2, 6), stock_disp)
                    var = productos_sup[prod]["variedad"]
                    new_purchase[var] = new_purchase.get(var, 0) + qty
                    productos_sup[prod]["stock"] -= qty
                    inventario[prod] += qty

            # 3) Actualizar creencias del cliente
            current_comp = num_cmp + 1
            self.agent.creencias.actualizar("productos_obtenidos", inventario)
            self.agent.creencias.actualizar("numero_compras", current_comp)

        # 4) Construir y guardar la decisión
        decision = {
            "cliente_id": self.agent.cliente_id,
            "accion": "compra_indispensable",
            "supermercado_elegido": best_super.split("/")[-1],
            "supermercado_jid": best_super,
            "productos_comprados": new_purchase,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "numero_compra": current_comp,
            "indispensables_faltantes": self.faltantes
        }
        async with decisiones_lock:
            decisiones.append(decision)

        # 5) Enviar mensaje al supermercado
        self.agent.add_behaviour(EnviarMensajeCompra(decision))


class CompraNormalBehaviour(OneShotBehaviour):
    async def run(self):
        # 0) Evitar exceso y leer número de compras bajo lock
        async with self.agent.creencias_lock:
            num_cmp = self.agent.creencias.obtener("numero_compras") or 0
            if num_cmp >= MAX_PURCHASES:
                return

            # 1) Elegir supermercado
            best_super = self.agent.calcular_mejor_supermercado()
            if not best_super:
                return

            creencias_sup = self.agent.creencias.obtener("supermercados")
            sup_data = creencias_sup[best_super]
            productos_sup = sup_data["productos"]
            inventario = self.agent.creencias.obtener("productos_obtenidos")

            # 2) Preparar la compra
            new_purchase = {}
            for prod, det in productos_sup.items():
                stock_disp = det.get("stock", 0)
                if stock_disp > 0:
                    qty = min(random.randint(0, 5), stock_disp)
                    if qty > 0:
                        var = det["variedad"]
                        new_purchase[var] = new_purchase.get(var, 0) + qty
                        det["stock"] -= qty
                        inventario[prod] += qty

            # 3) Actualizar creencias del cliente
            current_comp = num_cmp + 1
            self.agent.creencias.actualizar("productos_obtenidos", inventario)
            self.agent.creencias.actualizar("numero_compras", current_comp)

        # 4) Construir y guardar la decisión
        decision = {
            "cliente_id": self.agent.cliente_id,
            "accion": "compra",
            "supermercado_elegido": best_super.split("/")[-1],
            "supermercado_jid": best_super,
            "productos_comprados": new_purchase,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "numero_compra": current_comp
        }
        async with decisiones_lock:
            decisiones.append(decision)

        # 5) Enviar mensaje al supermercado
        self.agent.add_behaviour(EnviarMensajeCompra(decision))


class ConsumoBehaviour(OneShotBehaviour):
    async def run(self):
        # 1) Consumir del inventario bajo lock
        async with self.agent.creencias_lock:
            inventario = self.agent.creencias.obtener("productos_obtenidos")
            consumo = {p: 1 for p, q in inventario.items() if q > 0}
            for prod in consumo:
                inventario[prod] -= 1
            self.agent.creencias.actualizar("productos_obtenidos", inventario)
            current_comp = self.agent.creencias.obtener("numero_compras")

        # 2) Construir y guardar la decisión
        decision = {
            "cliente_id": self.agent.cliente_id,
            "accion": "consumo",
            "productos_consumidos": consumo,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "numero_compra": current_comp
        }
        async with decisiones_lock:
            decisiones.append(decision)
class EnviarMensajeCompra(OneShotBehaviour):
    def __init__(self, decision):
        """
    Inicializa un comportamiento de un solo disparo para enviar una compra.

    Parámetros:
        decision (dict): Estructura con datos de la decisión (productos, JID destino, timestamp…).
    """
        super().__init__()
        self.decision = decision

    async def run(self):
        """
        Construye y envía el mensaje de tipo
        “venta” al supermercado correspondiente
        usando la información en self.decision.
        """
        msg = Message(to=str(self.decision["supermercado_jid"]))
        msg.body = json.dumps({
            "cliente_id": self.agent.cliente_id,
            "accion": self.decision["accion"],
            "productos_comprados": self.decision.get("productos_comprados", {}),
            "timestamp": self.decision["timestamp"],
            "tipo": "venta"
        })
        await self.send(msg)
        logging.info(f"[{self.agent.cliente_id}] Envió mensaje de "
                     f"compra a {self.decision['supermercado_jid']} "
                     f"con productos: {self.decision.get('productos_comprados', {})}")

