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
import json, math
import copy
class SupermercadoInteligente(Agent):
    def __init__(
        self,
        jid,
        password,
        productos=None,
        desires=None,
        modo_adaptativo="atraccion_clientes", peer_smart_jids=None  # o "reevaluacion_productos"
    ):
        super().__init__(jid, password)
        self.supermercado_id = jid
        self.creation_time = datetime.datetime.now()
        self.modo_adaptativo = modo_adaptativo
        self.creencias = Creencias()
        ubic = self._init_ubicacion()
        self.ubicacion = ubic
        supermercados_ubicaciones[self.supermercado_id] = ubic
        self.peer_smart_jids = peer_smart_jids or []
        self._init_inventario(productos)
        supermercados_ubicaciones[self.supermercado_id] = self._init_ubicacion()
        
        self._init_inventario(productos)
        self._init_ventas()
        self._init_deseos(desires)

    def _init_ubicacion(self):
        ubic = (random.randint(0,100), random.randint(0,100))
        self.creencias.actualizar("ubicacion", ubic)
        return ubic

    def _init_inventario(self, productos):
        inventario = productos or self.generar_criterios_productos()
        self.productos = inventario
        self.creencias.actualizar("productos", inventario)

    def _init_ventas(self):
        # ventas_recibidas y métricas para ambos modos
        self.ventas_recibidas = []
        self.creencias.actualizar("ventas_recibidas", [])
        self.creencias.actualizar("ventas_recientes", [])
        self.creencias.actualizar("ventas_previas", 0)
        self.creencias.actualizar("max_ventas", 0)
        self.creencias.actualizar("catalogo_exitoso", None)

    def _init_deseos(self, desires):
        if desires is None:
            self.desires = [
                Deseo("vender_productos", {"stock": self.productos}),
                Deseo("adaptarse_supermercados")
            ]
        else:
            self.desires = desires

    def generar_criterios_productos(self):
        """
        Crea para cada producto un criterio ético aleatorio y stock inicial.
        Devuelve un dict:
          { producto: { 'variedad': ..., 'stock': ..., <criterios éticos> } }
        """
        resultado = {}
        for producto in possible_products:
            variedad = (
                random.choice(possible_varieties[producto])
                if producto in possible_varieties else producto
            )
            detalle = predefined_ethics[variedad].copy()
            detalle["stock"] = random.randint(300, 500)
            detalle["variedad"] = variedad
            resultado[producto] = detalle
        return resultado

    def rotar_surtido(self):
        """
        Rota aleatoriamente la variedad de cada producto,
        conservando el stock actual.
        """
        for prod, datos in list(self.productos.items()):
            if prod in possible_varieties:
                current = datos["variedad"]
                opciones = [v for v in possible_varieties[prod] if v != current]
                nueva = random.choice(opciones) if opciones else current
                nuevo_detalle = predefined_ethics[nueva].copy()
                nuevo_detalle["stock"] = datos["stock"]
                nuevo_detalle["variedad"] = nueva
                self.productos[prod] = nuevo_detalle
                logging.info(f"[{self.supermercado_id}] Rotó {prod}: {current} -> {nueva}")

    class RecibirMensaje(CyclicBehaviour):
            """
            Ciclo permanente de escucha en SupermercadoInteligente:
            • Mensajes de ventas de supermercados normales (tipo "ventas_super_normal").
            • Mensajes de petición de cliente (tipo "Peticion_Cliente").
            """
            async def run(self):
                msg = await self.receive(timeout=10)
                if not msg:
                    return

                # Intentar parsear JSON
                try:
                    data = json.loads(msg.body)
                except (json.JSONDecodeError, TypeError):
                    data = {}
                if data.get("tipo") == "metricas_smart":
                    return
                # -- Venta de supermercado normal --
                if data.get("tipo") == "ventas_super_normal":
                    sender = str(msg.sender).split("/")[-1]
                    venta = data.get("venta") or data.get("productos_comprados")
                    wrapper = {"supermercado_id": sender, "ventas": [venta]}
                    # Actualizar listas y creencias
                    self.agent.ventas_recibidas.append(wrapper)
                    recientes = self.agent.creencias.obtener("ventas_recientes") or []
                    recientes.append(venta)
                    
                    self.agent.creencias.actualizar("ventas_recibidas", self.agent.ventas_recibidas)
                    logging.info(f"[{self.agent.supermercado_id}] Venta normal recibida de {sender}: {venta}")
                    return

                # -- Petición de cliente --
                if data.get("tipo") == "Peticion_Cliente":
                    sender = str(msg.sender)
                    logging.info(f"[{self.agent.supermercado_id}] Peticion_Cliente recibida de {sender}: {data}")
                    clientes = self.agent.creencias.obtener("clientes") or {}
                    clientes[sender] = {"request": data.get("payload", msg.body), "timestamp": datetime.datetime.now()}
                    self.agent.creencias.actualizar("clientes", clientes)

                    # Enviar oferta al cliente
                    resp = Message(to=sender)
                    resp.body = json.dumps({
                        "tipo": "Peticion_Cliente",
                        "productos": self.agent.productos,
                        "ubicacion": self.agent.ubicacion
                    })
                    await self.send(resp)
                    logging.info(f"[{self.agent.supermercado_id}] Oferta enviada a {sender} (Peticion_Cliente).")
                    return
                elif data.get("tipo") == "venta":
                    # Extraer los datos de la venta
                    venta = {
                        "cliente_id": data["cliente_id"],
                        "accion": data.get("accion"),
                        "productos": data.get("productos_comprados", {}),
                        "timestamp": data.get("timestamp")
                    }
                    # Actualizar la creencia 'ventas_recientes'
                    recientes = self.agent.creencias.obtener("ventas_recientes") or []
                    recientes.append(venta)
                    self.agent.creencias.actualizar("ventas_recientes", recientes)

                    logging.info(
                        f"[{self.agent.supermercado_id}] Venta inteligente recibida de "
                        f"{venta['cliente_id']}: {venta['productos']}"
                    )
                    return
                # -- Otro mensaje --
                logging.info(f"[{self.agent.supermercado_id}] Mensaje desconocido de {msg.sender}: {msg.body}")
    class EnviarMetricasSmart(PeriodicBehaviour):
        def __init__(self, period, peer_jids: list[str]):
            super().__init__(period=period)
            self.peer_jids = peer_jids

        async def run(self):
            datos = {
                "tipo": "metricas_smart",
                "ventas_recientes": self.agent.creencias.obtener("ventas_recientes") or [],
                "catalogo": self.agent.productos
            }
            for peer in self.peer_jids:
                msg = Message(to=str(peer))
                msg.body = json.dumps(datos)
                await self.send(msg)
                logging.info(f"[{self.agent.supermercado_id}] Métricas enviadas a {peer}")

    class RecibirMetricasSmart(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if not msg:
                return
            try:
                data = json.loads(msg.body)
            except json.JSONDecodeError:
                return
            if data.get("tipo") != "metricas_smart":
                return
            peer = str(msg.sender).split("/")[0]
            ventas = data.get("ventas_recientes", [])
            cat = data.get("catalogo")
            self.agent.creencias.actualizar(f"ventas_per_{peer}", ventas)
            if cat is not None:
                self.agent.creencias.actualizar(f"catalogo_peer_{peer}", cat)
            logging.info(f"[{self.agent.supermercado_id}] Métricas y catálogo recibidos de {peer}")
    class BDIBehaviour(PeriodicBehaviour):
        def __init__(self, period, modo):
            super().__init__(period=period)
            self.modo = modo

        async def run(self):
            agent = self.agent
            # OBSERVAR
            recientes = agent.creencias.obtener("ventas_recientes") or []
            previas  = agent.creencias.obtener("ventas_previas")  or 0
            maxv    = agent.creencias.obtener("max_ventas")     or 0

            # DELIBERAR Y EJECUTAR según modo
            if self.modo == "atraccion_clientes":
                agent = self.agent
                ventas_propias = agent.creencias.obtener("ventas_recientes") or []
                count_propias = len(ventas_propias)

                # 1) Contar ventas de todos
                sales_counts = {agent.supermercado_id: count_propias}
                for peer in agent.peer_smart_jids:
                    ventas_peer = agent.creencias.obtener(f"ventas_per_{peer}") or []
                    sales_counts[peer] = len(ventas_peer)

                # 2) Mejor vendedor
                best_jid, best_count = max(sales_counts.items(), key=lambda kv: kv[1])
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Campos comunes
                base_entry = {
                    "timestamp": timestamp,
                    "agente": agent.supermercado_id,
                    "ventas_propias": count_propias,
                    "ventas_origen": 0,
                    "origen": "",
                    "evento": "",
                }

                if best_jid != agent.supermercado_id and best_count > count_propias:
                    # adopta catálogo
                    peer_catalog = agent.creencias.obtener(f"catalogo_peer_{best_jid}") or {}
                    agent.productos = copy.deepcopy(peer_catalog)
                    agent.creencias.actualizar("catalogo_exitoso", agent.productos)
                    logging.info(f"[{agent.supermercado_id}] Adopta catálogo de {best_jid} ({best_count} vs {count_propias})")

                    entry = base_entry.copy()
                    entry.update({
                        "evento": "adopta_catálogo",
                        "origen": best_jid,
                        "ventas_origen": best_count,
                    })
                    atraccion_eventos_log.append(entry)

                elif best_count == 0:
                    # rota surtido
                    await asyncio.to_thread(agent.rotar_surtido)
                    logging.info(f"[{agent.supermercado_id}] Ninguna venta; rota surtido")

                    entry = base_entry.copy()
                    entry.update({
                        "evento": "rota_surtido",
                    })
                    atraccion_eventos_log.append(entry)

                else:
                    # actualiza histórico
                    maxv = agent.creencias.obtener("max_ventas") or 0
                    if count_propias > maxv:
                        agent.creencias.actualizar("max_ventas", count_propias)
                        agent.creencias.actualizar("catalogo_exitoso", copy.deepcopy(agent.productos))
                        logging.info(f"[{agent.supermercado_id}] Mantiene catálogo propio ({count_propias})")

                        entry = base_entry.copy()
                        entry.update({
                            "evento": "actualiza_histórico",
                        })
                        atraccion_eventos_log.append(entry)

                # 6) Reset y cleanup
                agent.creencias.actualizar("ventas_previas", count_propias)
                agent.creencias.actualizar("ventas_recientes", [])
                
            elif self.modo == "reevaluacion_productos":
                # --- lógica de ReevaluarProductos ---
                nearby_sales = {}
                for info in agent.ventas_recibidas:
                    sid = info["supermercado_id"]
                    loc = supermercados_ubicaciones.get(sid)
                    if loc:
                        dist = math.dist(agent.ubicacion, loc)
                        if dist <= CERCANO_THRESHOLD:
                            for v in info["ventas"]:
                                for var, qty in v.get("productos_comprados", {}).items():
                                    base = var.split("_")[0]
                                    nearby_sales.setdefault(base, {}).setdefault(var, 0)
                                    nearby_sales[base][var] += qty

                cambios = []
                for prod, datos in agent.productos.items():
                    actual = datos["variedad"]
                    best_var, best_qty = actual, nearby_sales.get(prod, {}).get(actual, 0)
                    for var, qty in nearby_sales.get(prod, {}).items():
                        if qty > best_qty:
                            best_var, best_qty = var, qty
                    if best_var != actual:
                        old_stock = datos["stock"]
                        nueva_info = predefined_ethics[best_var].copy()
                        nueva_info["stock"]   = old_stock
                        nueva_info["variedad"] = best_var
                        agent.productos[prod] = nueva_info
                        cambios.append((prod, actual, best_var))
                        logging.info(
                            f"[{agent.supermercado_id}] {prod}: {actual} -> {best_var} (ventas={best_qty})"
                        )
                # aquí podrías registrar 'cambios' en tu log si quieres
                if cambios:
                    cambios_productos_log.extend(cambios)

                    # 2) Guardar snapshot de productos inteligentes
                    productos_inteligentes_log.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "supermercado_id": agent.supermercado_id,
                        "productos": copy.deepcopy(agent.productos)
                    })

                    # 3) Registrar entrada de evaluación
                    evaluacion_entry = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "supermercado_id": agent.supermercado_id,
                        "ventas_evaluadas": copy.deepcopy(agent.ventas_recibidas),
                        "nearby_sales": copy.deepcopy(nearby_sales),
                        "cambios": copy.deepcopy(cambios)
                    }
                    evaluacion_cambios_log.append(evaluacion_entry)
                    logging.info(f"[{agent.supermercado_id}] Evaluación de cambios registrada: {evaluacion_entry}")
                    # ACTUALIZAR estado
                agent.creencias.actualizar("ventas_previas", len(recientes))
                agent.creencias.actualizar("ventas_recientes", [])

    async def setup(self):
        logging.info(f"[{self.supermercado_id}] Iniciado modo={self.modo_adaptativo}")
        self.add_behaviour(self.RecibirMensaje())
        # Comportamientos Smart-Smart
        self.add_behaviour(self.EnviarMetricasSmart(period=15, peer_jids=self.peer_smart_jids))
        self.add_behaviour(self.RecibirMetricasSmart())
        # BDI principal
        self.add_behaviour(self.BDIBehaviour(period=10, modo=self.modo_adaptativo))

