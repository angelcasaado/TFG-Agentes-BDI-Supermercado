from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from ..config import (
    ENABLE_VARIETY_CHANGE,
    VARIETY_CHANGE_INTERVAL,
    possible_products,
    possible_varieties,
    predefined_ethics,
    supermercados_ubicaciones
)
import random
from ..BDI.Creencias import Creencias
from ..BDI.Deseo import Deseo
from ..BDI.Intenciones import Intencion
from ..logger import logging
import json
import datetime
import asyncio


class SupermercadoAgent(Agent):
    def __init__(
        self,
        jid,
        password,
        supermercado_id,
        productos,
        smart_super_jids: list[str],
        desires=None
    ):
        x, y = random.randint(0, 100), random.randint(0, 100)
        full_jid = f"{jid}/{supermercado_id}"
        super().__init__(full_jid, password)
        self.supermercado_id = supermercado_id
        self.full_jid = full_jid
        self.ubicacion = (x, y)
        self.smart_super_jids = smart_super_jids

        # Inventario inicial
        inventario = self.generar_criterios_productos()
        supermercados_ubicaciones[self.supermercado_id] = self.ubicacion

        # Creencias: clientes, ventas e inventario
        self.creencias = Creencias()
        self.creencias.actualizar("clientes", {})
        self.creencias.actualizar("ventas", [])
        self.creencias.actualizar("inventario", inventario)

        # Registros de ventas
        self.ventas_delta = []
        self.ventas_registradas_hist = []
        self.creation_time = datetime.datetime.now()
        # Registro del último cambio de variedades
        self.last_variety_change = datetime.datetime.now()

        # Deseos iniciales
        if desires is None:
            self.desires = [
                Deseo("tener_stock", {})
            ]
            if ENABLE_VARIETY_CHANGE:
                # Añadimos el deseo fijo de rotar variedades si está activado
                self.desires.append(Deseo("rotar_variedades"))
        else:
            self.desires = desires
            if ENABLE_VARIETY_CHANGE and not any(d.nombre == "rotar_variedades" for d in self.desires):
                self.desires.append(Deseo("rotar_variedades"))

        # Intención actual (None si no hay)
        self.intencion = None

    class BDIBehaviour(PeriodicBehaviour):
        """
        Ciclo BDI para SupermercadoAgent:
        1) ACTUALIZAR CRENCIAS (ventas/clientes/inventario)
        2) DELIBERAR: revisar cada deseo en self.agent.desires,
           comprobando si está insatisfecho:
           - "tener_stock": si algún producto < 100 unidades
           - "rotar_variedades": si ha pasado VARIETY_CHANGE_INTERVAL
        3) PLANIFICAR/EJECUTAR la Intención asociada:
           - "rotar_variedades" en ambos casos
        4) REINICIO
        """
        def __init__(self, period):
            super().__init__(period=period)

        async def run(self):
            agent = self.agent
            ahora = datetime.datetime.now()

            # ---------------------------------------------
            # FASE 1: ACTUALIZAR CRENCIAS (ya se actualizan en otros comportamientos)
            clientes = agent.creencias.obtener("clientes") or {}
            ventas = agent.creencias.obtener("ventas") or []
            inventario = agent.creencias.obtener("inventario") or {}

            # ---------------------------------------------
            # FASE 2: DELIBERAR (verificar deseos insatisfechos)
            agent.intencion = None

            # 2.1 Revisar "tener_stock"
            low_stock = [p for p, d in inventario.items() if d["stock"] < 100]
            if any(d.nombre == "tener_stock" for d in agent.desires) and low_stock:
                deseo_ts = next(d for d in agent.desires if d.nombre == "tener_stock")
                agent.intencion = Intencion(deseo_ts, "rotar_variedades")

            # 2.2 Si no se elige "tener_stock", revisar "rotar_variedades"
            if agent.intencion is None and ENABLE_VARIETY_CHANGE:
                tiempo_pasado = (ahora - agent.last_variety_change).total_seconds()
                if any(d.nombre == "rotar_variedades" for d in agent.desires) and tiempo_pasado >= VARIETY_CHANGE_INTERVAL:
                    deseo_rv = next(d for d in agent.desires if d.nombre == "rotar_variedades")
                    agent.intencion = Intencion(deseo_rv, "rotar_variedades")

            # ---------------------------------------------
            # FASE 3: PLANIFICAR/EJECUTAR según Intención
            # ---------------------------------------------
            if agent.intencion is not None:
                plan = agent.intencion.plan
                deseo_act = agent.intencion.deseo

                if plan == "rotar_variedades":
                    logging.info(f"[{agent.supermercado_id}] Intención: rotar_variedades")
                    await asyncio.to_thread(agent.cambiar_variedades)

                    # Si la intención venía de "rotar_variedades", actualizar timestamp
                    if deseo_act.nombre == "rotar_variedades":
                        agent.last_variety_change = datetime.datetime.now()

            # ---------------------------------------------
            # FASE 4: REINICIO DEL CICLO
            # ---------------------------------------------
            return

    def generar_criterios_productos(self):
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

    def cambiar_variedades(self):
        """
        Cambia a una variedad distinta para cada producto en el inventario,
        conservando el stock, y lo registra en el logger.
        """
        inventario = self.creencias.obtener("inventario") or {}
        for producto, datos in list(inventario.items()):
            if producto in possible_varieties:
                current = datos["variedad"]
                opciones = [v for v in possible_varieties[producto] if v != current]
                nueva = random.choice(opciones) if opciones else current

                detalle = predefined_ethics[nueva].copy()
                detalle["stock"] = datos["stock"]
                detalle["variedad"] = nueva

                inventario[producto] = detalle
                logging.info(
                    f"[{self.supermercado_id}] Cambió {producto} "
                    f"de {current} a {nueva}"
                )

        self.creencias.actualizar("inventario", inventario)

    class RotarVariedadesPeriodic(PeriodicBehaviour):
        """
        Si ENABLE_VARIETY_CHANGE es True, cada VARIETY_CHANGE_INTERVAL segundos
        invoca cambiar_variedades() para todos los productos.
        """
        async def run(self):
            await asyncio.to_thread(self.agent.cambiar_variedades)

    class RecibirMensaje(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return

            # Intentar parsear JSON
            body = msg.body or ""
            data = None
            try:
                data = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                data = None

            # Venta
            if isinstance(data, dict) and data.get("tipo") == "venta":
                productos_comprados = data.get("productos_comprados", {})
                inventario = self.agent.creencias.obtener("inventario") or {}
                for var, qty in productos_comprados.items():
                    base = var.split("_")[0]
                    if base in inventario:
                        inventario[base]["stock"] = max(
                            0, inventario[base]["stock"] - qty
                        )
                self.agent.creencias.actualizar("inventario", inventario)
                # Registrar venta
                self.agent.ventas_delta.append(data)
                self.agent.ventas_registradas_hist.append(data)
                self.agent.creencias.actualizar(
                    "ventas", self.agent.ventas_registradas_hist
                )
                logging.info(f"[{self.agent.supermercado_id}] Venta: {data}")
                if ENABLE_VARIETY_CHANGE and len(self.agent.ventas_registradas_hist) % 30 == 0:
                    self.agent.cambiar_variedades()
                return

            # Consulta de cliente o mensaje no JSON
            logging.info(f"[{self.agent.supermercado_id}] Mensaje de {msg.sender}: {body}")
            clientes_cre = self.agent.creencias.obtener("clientes")
            clientes_cre[str(msg.sender)] = body
            self.agent.creencias.actualizar("clientes", clientes_cre)

            # Responder oferta
            respuesta = Message(to=str(msg.sender))
            inventario = self.agent.creencias.obtener("inventario") or {}
            respuesta.body = json.dumps({
                "tipo": "Peticion_Cliente",
                "productos": inventario,
                "ubicacion": self.agent.ubicacion
            })
            await self.send(respuesta)
            logging.info(f"[{self.agent.supermercado_id}] Enviado oferta a {msg.sender}.")

    class EnviarVentasAlSmart(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1)
            while self.agent.ventas_delta:
                venta = self.agent.ventas_delta.pop(0)
                for peer in self.agent.smart_super_jids:
                    msg = Message(to=str(peer))
                    msg.body = json.dumps({
                        "tipo": "ventas_super_normal",
                        "supermercado_id": self.agent.supermercado_id,
                        "venta": venta
                    })
                    await self.send(msg)
                    logging.info(f"[{self.agent.supermercado_id}] Enviando al Smart (ventas_super_normal): {msg.body}")

    async def setup(self):
        logging.info(f"[{self.supermercado_id}] Iniciado en {self.ubicacion}.")

        # 1) Comportamiento de recepción de mensajes
        self.add_behaviour(self.RecibirMensaje())

        # 2) Comportamiento de envío al smart
        self.add_behaviour(self.EnviarVentasAlSmart())

        # 3) BDI explícito, se ejecuta cada 10 segundos
        self.add_behaviour(self.BDIBehaviour(period=10))

        # 4) (Opcional) rotación periódica si la activas
        if ENABLE_VARIETY_CHANGE:
            self.add_behaviour(
                self.RotarVariedadesPeriodic(period=VARIETY_CHANGE_INTERVAL)
            )