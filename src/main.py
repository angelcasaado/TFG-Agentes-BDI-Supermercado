import nest_asyncio
import asyncio
import random
import math
import json
import matplotlib.pyplot as plt
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour

from spade.message import Message
import os
import pandas as pd
from datetime import datetime
import copy  # Para deepcopy
import logging
from .config import *
from .Agentes.supermercado_inteligente import SupermercadoInteligente
from .Agentes.supermercado import SupermercadoAgent
from .Agentes.cliente import ClienteAgent
from matplotlib.lines import Line2D





# Se aplica nest_asyncio para entornos con bucle de eventos activo
nest_asyncio.apply()

# -------------------------------------------------
# Configuración de la carpeta "capturas"
# -------------------------------------------------
capturas_path = os.path.join(os.getcwd(), "capturas")
if not os.path.exists(capturas_path):
    os.makedirs(capturas_path)



###############################################################################
# Agente Supermercado (normal)
###############################################################################
async def iniciar_cliente(cliente):
    await cliente.start()


async def main():
    contador = 0
    indice_cuenta = 0
    indice_cuenta_cliente = 0
    supermercados_jids = []
    supermercados = []

    smart_supermercados = []
    # ——— Crear N supermercados inteligentes ———
    for i in range(NUM_INTELIGENTES):
        jid = USUARIO_JID_SUPER[i % len(USUARIO_JID_SUPER)]
        pwd = PASSWORD_SUPER[i % len(PASSWORD_SUPER)]
        smart = SupermercadoInteligente(
            jid,
            pwd,
            modo_adaptativo=adapatativo,
            peer_smart_jids=[]   # se rellena justo después
        )
        smart_supermercados.append(smart)

    # Obtener lista de bare jids de todos los inteligentes
    smart_jids = [s.jid for s in smart_supermercados]
    for s in smart_supermercados:
        # La primera vez lo inicializaste vacío,
        # ahora sí le metes la lista real
        s.peer_smart_jids = [jid for jid in smart_jids if jid != s.jid]

   

    # Arrancar todos los inteligentes y añadir sus jids al vector global
    for s in smart_supermercados:
        await s.start()
        supermercados_jids.append(s.jid)

    # ——— Crear supermercados normales como antes ———
    for i in range(NUM_SUPERMERCADOS):
        sup = SupermercadoAgent(
            USUARIO_JID_SUPER[indice_cuenta],
            PASSWORD_SUPER[indice_cuenta],
            f"SUPERMERCADO_{i + 1}",
            possible_products,
            # ahora poder smart_supermercados si quieres que reciban todos
            smart_jids ,  # <─ ajusta según convenga
        )
        supermercados.append(sup)
        supermercados_jids.append(sup.full_jid)
        contador += 1
        if contador % 20 == 0:
            indice_cuenta = (indice_cuenta + 1) % len(USUARIO_JID_SUPER)

    # Clientes
    clientes = []
    for i in range(NUM_CLIENTES):
        cli = ClienteAgent(
            USUARIO_JID_CLIENTE[indice_cuenta_cliente],
            PASSWORD_CLIENTE[indice_cuenta_cliente],
            f"CLIENTE_{i + 1}",
            supermercados_jids,
            possible_products
        )
        clientes.append(cli)
        contador += 1
        if contador % 20 == 0:
            indice_cuenta_cliente = (
                indice_cuenta_cliente + 1) % len(USUARIO_JID_CLIENTE)

    # Iniciar agentes
    
    for sup in supermercados:
        await sup.start()
    tareas = [asyncio.ensure_future(iniciar_cliente(cli)) for cli in clientes]
    await asyncio.gather(*tareas)

    # Esperar finalización
    while len(clients_finished) < NUM_CLIENTES:
        await asyncio.sleep(1)

    # Detener agentes
    for smart in smart_supermercados:
        await smart.stop()
    for sup in supermercados:
        await sup.stop()
    for cli in clientes:
        await cli.stop()
    jid_alias = {}

    # Supermercados inteligentes
    for idx, smart in enumerate(smart_supermercados, start=1):
        jid_alias[smart.jid] = f"SUPERMERCADO_SMART_{idx}"

    # Supermercados “normales”
    for sup in supermercados:
        jid_alias[sup.full_jid] = sup.supermercado_id
    # ——— Generar plots de decisiones ———
    jid_alias = {}
    smart_jids = set()
    for idx, smart in enumerate(smart_supermercados, start=1):
        jid_alias[smart.jid] = f"SUPERMERCADO_SMART_{idx}"
        smart_jids.add(smart.jid)
    for sup in supermercados:
        jid_alias[sup.full_jid] = sup.supermercado_id

    # ——— Generar plots de decisiones ———
    purchase_plots = {}
    for decision in decisiones:
        if decision["accion"] in ("compra", "compra_indispensable"):
            num = decision["numero_compra"]
            purchase_plots.setdefault(num, []).append(decision)

    for num, decs in purchase_plots.items():
        plt.figure(figsize=(10, 10))

        # Dibujado de puntos y flechas
        for d in decs:
            cid = d["cliente_id"]
            sid = d["supermercado_elegido"]
            if cid in clientes_ubicaciones and sid in supermercados_ubicaciones:
                c_loc = clientes_ubicaciones[cid]
                s_loc = supermercados_ubicaciones[sid]

                # Cliente
                plt.scatter(*c_loc, color='gray')
                plt.text(c_loc[0] + 1, c_loc[1] + 1, cid, fontsize=9)

                # Supermercado
                is_smart = sid in smart_jids
                mcolor = 'red' if is_smart else 'blue'
                plt.scatter(*s_loc, color=mcolor)
                display_sid = jid_alias.get(sid, sid.split('@')[0])
                plt.text(
                    s_loc[0] + 1,
                    s_loc[1] + 1,
                    display_sid,
                    fontsize=9,
                    verticalalignment="bottom",
                    horizontalalignment="left"
                )

                # Flecha (línea discontinua)
                plt.plot(
                    [c_loc[0], s_loc[0]],
                    [c_loc[1], s_loc[1]],
                    'k--'
                )

        # ——— Leyenda ———
        legend_elements = [
            Line2D([0], [0], marker='o', color='w',
                label='Cliente', markerfacecolor='gray', markersize=8),
            Line2D([0], [0], marker='o', color='w',
                label='Supermercado normal', markerfacecolor='blue', markersize=8),
            Line2D([0], [0], marker='o', color='w',
                label='Supermercado SMART', markerfacecolor='red', markersize=8),
            Line2D([0], [0], linestyle='--', color='black',
                label='Trayecto', markersize=0)
        ]
        plt.legend(handles=legend_elements, loc='upper right')

        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title(f"Decisiones de compra #{num}")

        path = os.path.join(
            capturas_path,
            f"clientes_supermercados_compra_{num}.png"
        )
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Plot compra #{num} guardado en: {path}")
    # ——— Exportar a Excel ———
    df_decisiones = pd.DataFrame(decisiones)

    # Clientes y supermercados normales
    df_agentes = pd.DataFrame(
        [{
            "Tipo": "Cliente",
            "ID": cli.cliente_id,
            "Ubicacion": str(cli.ubicacion),
            "Creencias": str(cli.creencias.data),
            "Deseos": ", ".join(str(d) for d in cli.desires),
            "Hora de creacion": cli.creation_time.strftime("%Y-%m-%d %H:%M:%S")
        } for cli in clientes] +
        [{
            "Tipo": "Supermercado",
            "ID": sup.supermercado_id,
            "Ubicacion": str(supermercados_ubicaciones[sup.supermercado_id]),
            "Creencias": str(sup.creencias.data),
            "Deseos": ", ".join(str(d) for d in sup.desires),
            "Hora de creacion": sup.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Ventas registradas": str(sup.ventas_registradas_hist)
        } for sup in supermercados] +
        # ahora múltiples inteligentes
        [{
            "Tipo": "SupermercadoInteligente",
            "ID": smart.jid,
            "Ubicacion": str(smart.ubicacion),
            "Creencias": str(smart.creencias.data),
            "Deseos": ", ".join(str(d) for d in smart.desires),
            "Hora de creacion": smart.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Ventas recibidas": str(smart.ventas_recibidas)
        } for smart in smart_supermercados]
    )

    df_creencias = pd.DataFrame(historial_creencias)

    # Ventas registradas normales
    ventas_dict = {
        sup.supermercado_id: [json.dumps(v) for v in sup.ventas_registradas_hist]
        for sup in supermercados
    }
    max_len = max((len(v) for v in ventas_dict.values()), default=0)
    for lst in ventas_dict.values():
        lst += [None] * (max_len - len(lst))
    df_ventas = pd.DataFrame(ventas_dict)

    # Ventas recibidas por inteligentes (todos)
    df_inteligentes = pd.concat([
        pd.DataFrame({
            "SupermercadoInteligente": [smart.jid] * len(smart.ventas_recibidas),
            "Ventas recibidas": [json.dumps(v) for v in smart.ventas_recibidas]
        })
        for smart in smart_supermercados
    ], ignore_index=True)

    df_cambios = pd.DataFrame(cambios_productos_log) if cambios_productos_log else pd.DataFrame()
    df_prod_int = pd.DataFrame(productos_inteligentes_log) if productos_inteligentes_log else pd.DataFrame()
    df_eval     = pd.DataFrame(evaluacion_cambios_log)     if evaluacion_cambios_log else pd.DataFrame()
    df_atraccion = pd.DataFrame(atraccion_eventos_log)
    
    excel_path = os.path.join(os.getcwd(), "Resultados_simulacion.xlsx")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_decisiones.to_excel(writer, sheet_name="Decisiones", index=False)
        df_agentes.to_excel(writer,   sheet_name="Agentes",      index=False)
        df_creencias.to_excel(writer, sheet_name="Cambios de Creencias", index=False)
        df_ventas.to_excel(writer,    sheet_name="Ventas Registradas",  index=False)
        df_inteligentes.to_excel(writer, sheet_name="Ventas Inteligentes", index=False)
        df_cambios.to_excel(writer,  sheet_name="Cambios de Productos", index=False)
        df_prod_int.to_excel(writer, sheet_name="Productos Inteligentes", index=False)
        df_eval.to_excel(writer,     sheet_name="Evaluacion Cambios",  index=False)
        df_atraccion.to_excel(writer, sheet_name="Eventos_Atraccion", index=False)
        # ——— Bar plot para todos los supermercados inteligentes ———
        df_purchases = df_decisiones[df_decisiones['accion'].isin(['compra', 'compra_indispensable'])]

        # Filtrar solo supermercados inteligentes
        df_purchases_smart = df_purchases[df_purchases['supermercado_jid'].isin([smart.jid for smart in smart_supermercados])]

        # Contar clientes únicos por ronda
        counts_total = df_purchases_smart.groupby('numero_compra')['cliente_id'].nunique()

        # Obtener primera y última ronda
        first_total = counts_total.get(1, 0)
        last_round_total = int(counts_total.index.max()) if not counts_total.empty else 1
        last_total = counts_total.get(last_round_total, 0)

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar([1, last_round_total], [first_total, last_total], width=0.5)

        ax.set_xticks([1, last_round_total])
        ax.set_xticklabels(['Compra 1', f'Compra {last_round_total}'], fontsize=12)
        ax.set_ylabel('Clientes que acudieron (total)', fontsize=12)
        ax.set_title('Total Visitas Supermercados Inteligentes\nRonda 1 vs Ronda Final', fontsize=14)
        ax.grid(axis='y', linestyle='--', alpha=0.6)

        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h}', xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 5), textcoords='offset points',
                        ha='center', va='bottom', fontsize=11)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()

        bar_path = os.path.join(capturas_path, 'visitas_totales_smart_ronda1_vs_final.png')
        plt.savefig(bar_path, dpi=300, bbox_inches='tight')
        plt.close()

        logging.info(f"Bar plot total visitas supermercados inteligentes guardado en: {bar_path}")

if __name__ == "__main__":
    asyncio.run(main())
