from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour

from spade.message import Message
from ..logger import logging
from ..config import (
    CERCANO_THRESHOLD,
    cambios_productos_log,
    productos_inteligentes_log,
    evaluacion_cambios_log,
    atraccion_eventos_log,
    possible_products,
    possible_varieties,
    predefined_ethics
)
import random
import datetime
from ..BDI.Creencias import Creencias
from ..BDI.Deseo import Deseo
from ..BDI.Intenciones import Intencion
import json, math
import copy
import asyncio

class SupermercadoInteligente(Agent):
    def __init__(
        self,
        jid,
        password,
        productos=None,
        desires=None,
        modo_adaptativo="atraccion_clientes",
        peer_smart_jids=None  # o "reevaluacion_productos"
    ):
        super().__init__(jid, password)
        self.supermercado_id = jid
        self.creation_time = datetime.datetime.now()
        self.modo_adaptativo = modo_adaptativo
        self.creencias = Creencias()
        
        # Inicializar y almacenar ubicación en creencias
        ubic = self._init_ubicacion()
        # Actualizar mapeo de ubicaciones de supermercados en creencias
        todas_ubic = self.creencias.obtener("supermercados_ubicaciones") or {}
        todas_ubic[self.supermercado_id] = ubic
        self.creencias.actualizar("supermercados_ubicaciones", todas_ubic)

        # Inicializar inventario y almacenarlo en creencias
        self._init_inventario(productos)

        # Inicializar ventas
        self._init_ventas()

        # Inicializar deseos
        self._init_deseos(desires)

        # Almacenar peer_smart_jids en creencias
        peers = peer_smart_jids or []
        self.creencias.actualizar("peer_smart_jids", peers)

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
                Deseo("tener_stock"),
                Deseo("adaptarse_supermercados", {})
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
                    "ubicacion": self.agent.creencias.obtener("ubicacion")
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
        """
        Ciclo periódico de envío de métricas desde SupermercadoInteligente a sus peers:
        • Cada vez que se ejecuta, obtiene métricas locales (ventas recientes, max ventas).
        • Envía un mensaje a cada JID en peer_smart_jids con los datos actuales.
        """
        def __init__(self, period):
            super().__init__(period=period)

        async def run(self):
            agent = self.agent
            datos = {
                "tipo": "metricas_smart",
                "ventas_recientes": agent.creencias.obtener("ventas_recientes") or [],
                "catalogo": agent.creencias.obtener("productos")
            }
            peers = agent.creencias.obtener("peer_smart_jids") or []
            for peer in peers:
                msg = Message(to=str(peer))
                msg.body = json.dumps(datos)
                await self.send(msg)
                logging.info(f"[{agent.supermercado_id}] Métricas enviadas a {peer}")

    class RecibirMetricasSmart(CyclicBehaviour):
        """
        Ciclo permanente de recepción de métricas de peers de SupermercadoInteligente:
        • Espera mensajes de tipo "metricas_smart".
        • Al recibir, actualiza las creencias con las métricas del peer.
        """
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
            agent = self.agent
            agent.creencias.actualizar(f"ventas_per_{peer}", ventas)
            if cat is not None:
                agent.creencias.actualizar(f"catalogo_peer_{peer}", cat)
            logging.info(f"[{agent.supermercado_id}] Métricas y catálogo recibidos de {peer}")

    class BDIBehaviour(PeriodicBehaviour):
        """
        Ciclo BDI principal para SupermercadoInteligente:
        1) CAPTAR Y ACTUALIZAR CRENCIAS
        2) DELIBERAR: elegir Deseo → Intención
        3) PLANIFICAR/EJECUTAR según la Intención
        4) REINICIAR (se repite periódicamente)
        """
        def __init__(self, period, modo):
            super().__init__(period=period)
            self.modo = modo

        async def run(self):
            agent = self.agent

            # ---------------------------------------------
            # FASE 1: CAPTAR CAMBIOS Y ACTUALIZAR CRENCIAS
            # ---------------------------------------------
            recientes = agent.creencias.obtener("ventas_recientes") or []
            ventas_propias = len(recientes)

            # ---------------------------------------------
            # FASE 2: DELIBERACIÓN (evaluar creencias para elegir Deseo → Intención)
            # ---------------------------------------------
            if self.modo == "atraccion_clientes":
                # (a) Calcular ventas propias y de peers
                sales_counts = {agent.supermercado_id: ventas_propias}
                peers = agent.creencias.obtener("peer_smart_jids") or []
                for peer in peers:
                    ventas_peer = agent.creencias.obtener(f"ventas_per_{peer}") or []
                    sales_counts[peer] = len(ventas_peer)

                # (b) Determinar quién es el “mejor vendedor”
                best_jid, best_count = max(sales_counts.items(), key=lambda kv: kv[1])

                if best_jid != agent.supermercado_id and best_count > ventas_propias:
                    for deseo in agent.desires:
                        if deseo.nombre == "adaptarse_supermercados":
                            deseo.payload = {"origen": best_jid, "ventas_origen": best_count}
                            agent.intencion = Intencion(deseo, "adaptarse_catalogo")
                            break

                    peer_catalog = agent.creencias.obtener(f"catalogo_peer_{best_jid}") or {}
                    agent.creencias.actualizar("productos", copy.deepcopy(peer_catalog))
                    agent.creencias.actualizar("catalogo_exitoso", copy.deepcopy(peer_catalog))
                    logging.info(
                        f"[{agent.supermercado_id}] Adopta catálogo de {best_jid} "
                        f"({best_count} vs {ventas_propias})"
                    )

                    entry = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "agente": agent.supermercado_id,
                        "ventas_propias": ventas_propias,
                        "ventas_origen": best_count,
                        "origen": best_jid,
                        "evento": "adopta_catálogo"
                    }
                    atraccion_eventos_log.append(entry)

                elif ventas_propias == 0:
                    for deseo in agent.desires:
                        if deseo.nombre == "tener_stock":
                            agent.intencion = Intencion(deseo, "rota_surtido")
                            break

                    await asyncio.to_thread(agent.rotar_surtido)
                    logging.info(f"[{agent.supermercado_id}] Ninguna venta; rota surtido")

                    entry = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "agente": agent.supermercado_id,
                        "ventas_propias": ventas_propias,
                        "ventas_origen": 0,
                        "origen": "",
                        "evento": "rota_surtido"
                    }
                    atraccion_eventos_log.append(entry)

                else:
                    for deseo in agent.desires:
                        if deseo.nombre == "tener_stock":
                            agent.intencion = Intencion(deseo, "actualiza_historico")
                            break

                    maxv = agent.creencias.obtener("max_ventas") or 0
                    if ventas_propias > maxv:
                        agent.creencias.actualizar("max_ventas", ventas_propias)
                        agent.creencias.actualizar("catalogo_exitoso", copy.deepcopy(agent.creencias.obtener("productos")))
                        logging.info(f"[{agent.supermercado_id}] Mantiene catálogo propio ({ventas_propias})")

                        entry = {
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "agente": agent.supermercado_id,
                            "ventas_propias": ventas_propias,
                            "ventas_origen": 0,
                            "origen": "",
                            "evento": "actualiza_historico"
                        }
                        atraccion_eventos_log.append(entry)

                agent.creencias.actualizar("ventas_previas", ventas_propias)
                agent.creencias.actualizar("ventas_recientes", [])

            elif self.modo == "reevaluacion_productos":
                # ---------------------------------------------
                # FASE 1: CAPTAR CAMBIOS (ventas cercanas) y ACTUALIZAR CRENCIAS
                # ---------------------------------------------
                nearby_sales = {}
                ventas_recibidas = agent.creencias.obtener("ventas_recibidas") or []
                ubicaciones = agent.creencias.obtener("supermercados_ubicaciones") or {}
                mi_ubic = agent.creencias.obtener("ubicacion")
                for info in ventas_recibidas:
                    sid = info["supermercado_id"]
                    loc = ubicaciones.get(sid)
                    if loc and math.dist(mi_ubic, loc) <= CERCANO_THRESHOLD:
                        for v in info["ventas"]:
                            for var, qty in v.get("productos_comprados", {}).items():
                                base = var.split("_")[0]
                                nearby_sales.setdefault(base, {}).setdefault(var, 0)
                                nearby_sales[base][var] += qty

                # ---------------------------------------------
                # FASE 2: DELIBERACIÓN (se forma el Deseo “adaptarse_supermercados” si hay cambios)
                # ---------------------------------------------
                productos = agent.creencias.obtener("productos") or {}
                cambios = []
                for prod, datos in productos.items():
                    actual = datos["variedad"]
                    best_var, best_qty = actual, nearby_sales.get(prod, {}).get(actual, 0)
                    for var, qty in nearby_sales.get(prod, {}).items():
                        if qty > best_qty:
                            best_var, best_qty = var, qty
                    if best_var != actual:
                        old_stock = datos["stock"]
                        nueva_info = predefined_ethics[best_var].copy()
                        nueva_info["stock"] = old_stock
                        nueva_info["variedad"] = best_var
                        productos[prod] = nueva_info
                        cambios.append((prod, actual, best_var, agent.supermercado_id))
                        logging.info(
                            f"[{agent.supermercado_id}] {prod}: {actual} → {best_var} "
                            f"(ventas={best_qty})"
                        )

                if cambios:
                    for deseo in agent.desires:
                        if deseo.nombre == "adaptarse_supermercados":
                            deseo.payload = {"cambios": cambios}
                            agent.intencion = Intencion(deseo, "reevaluacion_productos")
                            break

                    cambios_productos_log.extend(cambios)
                    productos_inteligentes_log.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "supermercado_id": agent.supermercado_id,
                        "productos": copy.deepcopy(productos)
                    })

                    evaluacion_entry = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "supermercado_id": agent.supermercado_id,
                        "ventas_evaluadas": copy.deepcopy(ventas_recibidas),
                        "nearby_sales": copy.deepcopy(nearby_sales),
                        "cambios": copy.deepcopy(cambios)
                    }
                    evaluacion_cambios_log.append(evaluacion_entry)
                    logging.info(f"[{agent.supermercado_id}] Evaluación de cambios registrada: {evaluacion_entry}")

                agent.creencias.actualizar("productos", productos)
                agent.creencias.actualizar("ventas_previas", len(recientes))
                agent.creencias.actualizar("ventas_recientes", [])

    async def setup(self):
        logging.info(f"[{self.supermercado_id}] Iniciado modo={self.modo_adaptativo}")
        self.add_behaviour(self.RecibirMensaje())
        # Comportamientos Smart-Smart
        self.add_behaviour(self.EnviarMetricasSmart(period=15))
        self.add_behaviour(self.RecibirMetricasSmart())
        # BDI principal
        self.add_behaviour(self.BDIBehaviour(period=10, modo=self.modo_adaptativo))
