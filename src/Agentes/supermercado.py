from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour

from spade.message import Message
from ..logger import logger
from ..config import *
import random
from ..BDI.Creencias import *
from ..BDI.Deseo import *
from ..BDI.Intenciones import *
from ..logger import * 
import json
import datetime
class SupermercadoAgent(Agent):
    def __init__(
        self,
        jid,
        password,
        supermercado_id,
        productos,
        smart_super_jids: list[str],   # ahora es lista
        desires=None
    ):
        x, y = random.randint(0, 100), random.randint(0, 100)
        full_jid = f"{jid}/{supermercado_id}"
        super().__init__(full_jid, password)
        self.supermercado_id = supermercado_id
        self.full_jid = full_jid
        self.ubicacion = (x, y)
        self.smart_super_jids = smart_super_jids
        # Inventario
        self.productos = self.generar_criterios_productos()
        supermercados_ubicaciones[self.supermercado_id] = self.ubicacion

        # Creencias: clientes y ventas
        self.creencias = Creencias()
        self.creencias.actualizar("clientes", {})
        self.creencias.actualizar("ventas", [])

        # Registros de ventas
        self.ventas_delta = []
        self.ventas_registradas_hist = []
        self.smart_super_jid = smart_super_jids
        self.creation_time = datetime.datetime.now()
        # Deseos
        if desires is None:
            self.desires = [
                Deseo("vender_productos", {"stock": self.productos}),
                Deseo("atraer_clientes")
            ]
        else:
            self.desires = desires
    class BDIBehaviour(PeriodicBehaviour):
        """
        BDI explícito:
         1) Observe: lee creencias actuales (ventas, clientes).
         2) Delibera: decide qué deseo atender (vender_productos vs atraer_clientes).
         3) Ejecuta: llama a la acción correspondiente.
        """
        async def run(self):
            agent = self.agent

            # --- 1) Observación de creencias ---
            ventas = agent.creencias.obtener("ventas") or []
            clientes = agent.creencias.obtener("clientes") or {}

            # --- 2) Deliberación ---
            # Prioridad 1: vender_productos (si hay stock bajo en varias referencias)
            low_stock = [p for p, d in agent.productos.items() if d["stock"] < 100]
            if low_stock:
                intención = "rotar_variedades"
            else:
                # Prioridad 2: atraer_clientes (si pocos clientes recientes)
                num_clientes = len(clientes)
                if num_clientes < 5:
                    intención = "atraer_clientes"
                else:
                    # Si ya hay actividad: nada que hacer
                    intención = None

            # --- 3) Ejecución de la intención ---
            if intención == "rotar_variedades":
                logging.info(f"[{agent.supermercado_id}] Intención: rotar_variedades")
                await asyncio.to_thread(agent.cambiar_variedades)

            elif intención == "atraer_clientes":
                logging.info(f"[{agent.supermercado_id}] Intención: atraer_clientes")
                # Aquí podrías implementar, p.ej., cambiar precios o promociones.
                # Como demo, simplemente reinicio el registro de clientes:
                agent.creencias.actualizar("clientes", {})

            # Si no hay intención, simplemente salta al siguiente ciclo.
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
        for producto, datos in list(self.productos.items()):
            if producto in possible_varieties:
                current = datos["variedad"]
                opciones = [v for v in possible_varieties[producto] if v != current]
                nueva = random.choice(opciones) if opciones else current

                # Copiamos los valores éticos y stock de la nueva variedad
                detalle = predefined_ethics[nueva].copy()
                detalle["stock"] = datos["stock"]
                detalle["variedad"] = nueva

                # Actualizamos en el inventario
                self.productos[producto] = detalle

                logging.info(
                    f"[{self.supermercado_id}] Cambió {producto} "
                    f"de {current} a {nueva}"
                )
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
                for var, qty in productos_comprados.items():
                    base = var.split("_")[0]
                    if base in self.agent.productos:
                        self.agent.productos[base]["stock"] = max(
                            0, self.agent.productos[base]["stock"] - qty
                        )
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
            respuesta.body = json.dumps({
                "tipo": "Peticion_Cliente",
                "productos": self.agent.productos,
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