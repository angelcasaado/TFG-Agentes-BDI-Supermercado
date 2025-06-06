# Simulación de Supermercados Inteligentes con Agentes BDI

Este proyecto implementa una simulación de interacción entre **clientes**, **supermercados normales** y **supermercados inteligentes** utilizando el paradigma **BDI** (Belief-Desire-Intention) y el framework **SPADE** para agentes basados en XMPP. El objetivo es modelar cómo los clientes toman decisiones de compra éticas y de distancia, así como cómo los supermercados—tanto tradicionales como “inteligentes”—gestionan su inventario, rotan variedades y compiten por atraer clientes.

---

## 📋 Contenido del Repositorio

```
.
├── __init__.py
├── config.py
├── logger.py
├── main.py
├── BDI/
│   ├── Creencias.py
│   ├── Deseo.py
│   └── Intenciones.py
├── Agentes/
│   ├── cliente.py
│   ├── supermercado.py
│   └── supermercado_inteligente.py
└── capturas/                      # Carpeta generada para guardar gráficos PNG
└── Resultados_simulacion.xlsx     # Reporte generado tras ejecutar la simulación
└── csv's/                         # CSVs generados (decisiones.csv, agentes.csv, etc.)
└── log.txt                        # Archivo de log con eventos de ejecución
```

- **config.py**: Parámetros globales (número de agentes, umbrales, pesos éticos, listados de JIDs y contraseñas).
- **logger.py**: Configuración básica de logging (se graba en `log.txt` y en consola).
- **main.py**: Punto de entrada de la simulación. Crea agentes, inicia el ciclo de ejecución y genera informes (gráficos y archivos Excel/CSV).
- **BDI/**:
  - **Creencias.py**: Clase que almacena y actualiza el conjunto de creencias del agente.
  - **Deseo.py**: Clase para representar deseos (objetivos) con sus parámetros y prioridad.
  - **Intenciones.py**: Clase que vincula un deseo con un plan concreto.
- **Agentes/**:
  - **cliente.py**: Implementa el agente `ClienteAgent` que envía peticiones a supermercados, delibera según sus creencias y deseos (compras indispensables, normales, consumo, finalización).
  - **supermercado.py**: Implementa el agente `SupermercadoAgent` (tradicional) que responde a peticiones de clientes, procesa ventas y rota variedades cuando el stock baja.
  - **supermercado_inteligente.py**: Implementa el agente `SupermercadoInteligente`, que recopila métricas de ventas de supermercados normales, compara catálogos con peers y adopta o rota surtido según su modo adaptativo (`atraccion_clientes` o `reevaluacion_productos`).

---

## 🛠 Requisitos Previos

- **Python 3.8+**  
- Librerías de Python (se pueden instalar mediante `pip`):
  - `spade` (framework de agentes BDI basados en XMPP)
  - `pandas`
  - `numpy`
  - `matplotlib`
  - `openpyxl` (para exportar a Excel)
  - `nest_asyncio`

> **Nota**: Se asume que se cuenta con un servidor XMPP disponible para que los agentes puedan comunicarse entre sí. En entornos de pruebas locales, puede usarse un servidor XMPP embebido o una instancia pública de prueba.

---

## ⚙️ Instalación

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/angelcasaado/TFG-Agentes-BDI-Supermercado
   cd nombre-del-proyecto
   ```

2. **Crear y activar un entorno virtual (opcional pero recomendado)**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # Linux/macOS
   # venv\Scripts\activate        # Windows
   ```

3. **Instalar dependencias**  
   ```bash
   pip install spade pandas matplotlib openpyxl nest_asyncio
   ```

---

## 🚀 Uso

1. **Configurar JIDs y credenciales**  
   - En `config.py` se definen los JIDs de agentes “super” y “clientes” y sus contraseñas. Ajusta si es necesario:
     ```python
     USUARIO_JID_SUPER = [
         "tfgancasa3@jabber.hot-chilli.net",
         "tfgancasa4@jabber.hot-chilli.net",
         "tfgancasa7@jabber.hot-chilli.net"
     ]
     PASSWORD_SUPER = ["usuario3", "usuario4", "usuario7"]
     USUARIO_JID_CLIENTE = [
         "tfgancasa6@jabber.hot-chilli.net",
         ...
     ]
     PASSWORD_CLIENTE = ["usuario6", ...]
     ```
   - Asegúrate de que dichos JIDs existan en tu servidor XMPP y estén habilitados.

2. **Ajustar parámetros globales (opcional)**  
   - `NUM_SUPERMERCADOS`, `NUM_INTELIGENTES`, `NUM_CLIENTES`: cantidad de cada tipo de agente.  
   - `MAX_PURCHASES`: número máximo de rondas de compra por cliente.  
   - `ENABLE_VARIETY_CHANGE`, `VARIETY_CHANGE_INTERVAL`: para activar/desactivar y temporizar la rotación automática de variedades en supermercados normales.  
   - Pesos éticos (`WEIGHT_ETHICAL`, `WEIGHT_DISTANCE`): influencian la elección de supermercado por parte del cliente.

3. **Ejecutar la simulación**  
   ```bash
   python main.py
   ```
   - Los agentes se levantarán y comenzarán a interactuar en ciclos periódicos.
   - El cliente envía peticiones a todos los supermercados en cada ventana de 5 segundos (`CicloBDIBehaviour`).
   - Los supermercados tradicionales responden con su catálogo y ubicación; luego los clientes deliberan y compran basándose en criterios éticos y de distancia.
   - Los supermercados inteligentes monitorean ventas de pares y de supermercados normales para adoptar o rotar surtido.

4. **Monitoreo y resultados**  
   - Durante la ejecución, se generará un archivo `log.txt` con todos los eventos importantes (ventas, cambios de surtido, adopción de catálogo, decisiones de clientes, etc.).
   - Al finalizar (cuando todos los clientes hayan completado sus compras o alcanzado `MAX_PURCHASES`), se exportarán:
     - **Gráficos PNG** en la carpeta `capturas/`:
       - Diagramas de trayectos cliente → supermercado para cada ronda de compra.
       - Gráfico de barras comparando visitas a supermercados inteligentes en la primera ronda vs. última.
     - **Archivo Excel**: `Resultados_simulacion.xlsx`, con hojas:
       - `Decisiones`: log de todas las decisiones (compras, consumos, final).
       - `Agentes`: detalles de cada agente (tipo, ID, ubicación, creencias, deseos, hora de creación, ventas).
       - `Ventas Registradas`: historial completo de ventas en supermercados normales.
       - `Ventas Inteligentes`: ventas recibidas/registradas en supermercados inteligentes.
       - `Cambios de Productos`: (si aplica) registro de cambios de surtido en supermercados inteligentes.
       - `Reevaluacion`: (si aplica) datos de evaluación antes de cambiar surtido.
       - `Atraccion_Clientes`: (si aplica) eventos de adopción de catálogo/rotación debido a competencia entre inteligentes.
     - **Carpeta `csv's/`**:
       - `decisiones.csv`, `agentes.csv`, `ventas_registradas.csv`, `ventas_inteligentes.csv`, etc.

---

## 🔍 Estructura de Módulos

### 1. BDI

- **Creencias.py**  
  Clase `Creencias` con métodos:
  - `actualizar(key, value)`: asigna o modifica una entrada en el diccionario interno de creencias.
  - `obtener(key)`: devuelve el valor asociado a la llave o `None` si no existe.
  - Sobrecarga de `__repr__` para mostrar las creencias.

- **Deseo.py**  
  Clase `Deseo` que encapsula:
  - `nombre`: identificador del deseo (por ejemplo, `"comprar_productos"`, `"minimizar_distancia"`, `"vender_productos"`, etc.).
  - `parametros`: diccionario de parámetros asociados.
  - `prioridad`: peso que determina orden en la deliberación.

- **Intenciones.py**  
  Clase `Intencion` que agrupa un objeto `Deseo` con un `plan` (cadena que describe la acción o comportamiento a ejecutar).

### 2. Agentes

- **cliente.py**  
  - `ClienteAgent` extiende `spade.agent.Agent`.  
  - Atributos clave:
    - `cliente_id`: identificador único, p. ej. `"CLIENTE_1"`.  
    - `ubicacion`: coordenadas (x, y) aleatorias en un espacio de 0–100.  
    - `creencias`: instancia de `Creencias` que almacena, por ejemplo:
      - `"supermercados"`: diccionario con estado de cada oferta recibida de supermercados.  
      - `"numero_compras"`: contador de rondas completadas.  
      - `"productos_obtenidos"`: inventario personal de productos.  
      - `"valores_eticos"`: diccionario con valores éticos (peso asignado a huella, calidad, origen, etc.).  
      - `"compro_lo_de_siempre"`: booleano para simular si el cliente prefiere comprar siempre lo mismo.  
    - `indispensables`: lista de productos que debe comprar antes de continuar.  
    - `desires` e `intentions`: listas BDI de deseos iniciales ("comprar_productos", "minimizar_distancia") e intenciones deliberadas.  
  - Behaviours principales:
    - **CicloBDIBehaviour (PeriodicBehaviour, period=5 s)**:
      1. Llama a `revisar_creencias()` para eliminar ofertas caducadas (mayores a 30 s).
      2. Envía una petición a cada supermercado en `supermercados_recursos`.  
      3. Delibera:  
         - Si alcanzó `MAX_PURCHASES`, plan = `"finalizar"`.  
         - Si faltan productos indispensables por debajo de cierto umbral (`THRESHOLD_INDISPENSABLE`), plan = `"compra_indispensable"`.  
         - Si el inventario total es menor a 8 unidades, plan = `"compra_normal"`.  
         - En caso contrario, plan = `"consumo"`.  
      4. Ejecuta el Behaviour apropiado según el plan (p. ej. `CompraIndispensableBehaviour`, `CompraNormalBehaviour`, `ConsumoBehaviour`, `HandleFinalizacionBehaviour`).  
    - **RecibirMensaje (CyclicBehaviour)**: procesa mensajes entrantes:
      - Si el mensaje es de tipo `Peticion_Cliente` de un supermercado, extrae la información de catálogo, ubicación y stock, y la guarda en `creencias["supermercados"]`.
      - Otros tipos de mensajes (JSON malformado o distinto) se descartan o logean.
    - **CompraIndispensableBehaviour**:  
      - Selecciona el “mejor supermercado” usando un cálculo de puntuación que pondera:
        - **score ético**: suma, para cada producto disponible, del valor ético del cliente × valor ético del producto.
        - **penalización por distancia**: distancia euclídea cliente ↔ supermercado (ponderada con `WEIGHT_DISTANCE`).  
      - Para cada producto indispensable faltante: elige cantidad aleatoria (2–6) limitada por stock, actualiza inventario y stock, eleva `numero_compras`.  
      - Registra la decisión en la lista global `decisiones` (con lock `decisiones_lock`) y envía un mensaje de venta al supermercado elegido.  
    - **CompraNormalBehaviour**:  
      - Similar a “compra imprescindible” pero compra cualquier producto con stock > 0 de forma aleatoria (0–5 unidades), priorizando variedad y stock.  
      - Actualiza inventario, `numero_compras`, log de decisiones y envía mensaje de venta.  
    - **ConsumoBehaviour**:  
      - Simula el consumo: resta 1 unidad de cada producto en inventario (si queda > 0), actualiza creencias y registra el evento.  
    - **HandleFinalizacionBehaviour**:  
      - Si el cliente aún tiene inventario, simula un “consumo final” antes de terminar.  
      - Registra la decisión final como `"final"` y notifica que el cliente terminó, agregándolo a la lista global `clients_finished`.

- **supermercado.py**  
  - `SupermercadoAgent` extiende `spade.agent.Agent`.  
  - Atributos clave:
    - `supermercado_id`: cadena tipo `"SUPERMERCADO_1"`, `"SUPERMERCADO_2"`, etc.
    - `ubicacion`: coordenadas (x, y) aleatorias en 0–100.
    - `productos`: inventario inicial generado en `generar_criterios_productos()`, donde cada producto tiene:
      - `variedad`: nombre de variedad (p. ej. `"Manzana_3"`).
      - `stock`: cantidad inicial aleatoria entre 300 y 500.
      - Atributos éticos predefinidos tomados de `predefined_ethics` en `config.py`.
    - `creencias`: almacena:
      - `"clientes"`: diccionario con JIDs y última petición recibida.
      - `"ventas"`: lista de ventas registradas (historial).
    - `ventas_delta`: buffer temporal de ventas recientes (pendientes de enviar al supermercado inteligente).
    - `ventas_registradas_hist`: historial completo de ventas.
    - `smart_super_jid`: lista de JIDs de supermercados inteligentes con los que se comunicará.  
  - Behaviours principales:
    - **RecibirMensaje (CyclicBehaviour)**:  
      - Si recibe un mensaje tipo `"venta"` (JSON desde un cliente), actualiza stock, registra en `ventas_delta` y `ventas_registradas_hist`, actualiza creencias `"ventas"`. Si el número de ventas totales es múltiplo de 30 y `ENABLE_VARIETY_CHANGE=True`, llama a `cambiar_variedades()`.  
      - Si es cualquier otro JSON o petición de cliente (`"Peticion_Cliente"`), responde con un mensaje que incluye su catálogo (`self.productos`) y ubicación, actualizando `creencias["clientes"]`.  
    - **EnviarVentasAlSmart (CyclicBehaviour)**: revisa periódicamente `ventas_delta`; si hay ventas, las envía a cada JID en `smart_super_jids` con tipo `"ventas_super_normal"`.  
    - **BDIBehaviour (PeriodicBehaviour, period=10 s)**:  
      1. Observa creencias propias (ventas, clientes).  
      2. Si existen productos con stock < 100, decide `"rotar_variedades"` y ejecuta `cambiar_variedades()` (en hilo aparte).  
      3. Si no, pero hay menos de 5 clientes recientes, decide `"atraer_clientes"` (por defecto, reinicia creencias de clientes).  
      4. Si no se cumple ninguna condición, no realiza acción.  
    - **RotarVariedadesPeriodic (PeriodicBehaviour, period=VARIETY_CHANGE_INTERVAL s)**: si `ENABLE_VARIETY_CHANGE=True`, invoca `cambiar_variedades()` cada cierto intervalo.  
  - **Métodos auxiliares**:
    - `generar_criterios_productos()`: crea el stock inicial de cada producto con valores éticos y variedad aleatoria.
    - `cambiar_variedades()`: para cada producto, elige una variedad distinta (aleatoria) y conserva el stock; registra el cambio en logs.

- **supermercado_inteligente.py**  
  - `SupermercadoInteligente` extiende `spade.agent.Agent`.  
  - Atributos clave:
    - `supermercado_id`: JID completo del agente (por ejemplo, `"tfgancasa3@jabber.hot-chilli.net/SUPERMERCADO_SMART_1"`).
    - `ubicacion`: par de coordenadas aleatorias.
    - `productos`: inventario inicial (puede heredarlo de un catálogo predefinido o generarlo aleatoriamente con `generar_criterios_productos()`).
    - `creencias`: almacena:
      - `"ubicacion"` del agente.
      - `"productos"`: catálogo propio.
      - `"ventas_recibidas"`: lista de ventas recibidas de supermercados normales.
      - `"ventas_recientes"`, `"ventas_previas"`, `"max_ventas"`, `"catalogo_exitoso"`, `"ventas_per_<peer_jid>"`, `"catalogo_peer_<peer_jid>"`.
    - `peer_smart_jids`: lista de JIDs de otros supermercados inteligentes con los que se intercambiará métricas.  
    - `modo_adaptativo`: puede ser `"atraccion_clientes"` (adoptar catálogo del mejor vendedor) o `"reevaluacion_productos"` (rotar surtido según ventas cercanas).  
  - Behaviours principales:
    - **RecibirMensaje (CyclicBehaviour)**:  
      - Si tipo `"ventas_super_normal"` (envío de supermercado normal), recolecta datos de venta, actualiza `"ventas_recibidas"` y `"ventas_recientes"`.  
      - Si tipo `"Peticion_Cliente"`, guarda la petición en `creencias["clientes"]` y responde al cliente con su catálogo y ubicación (igual que un supermercado normal).  
      - Si tipo `"venta"` (venta inteligente directa), añade a `"ventas_recientes"`.  
    - **EnviarMetricasSmart (PeriodicBehaviour, period=15 s)**: envía a cada peer en `peer_smart_jids` un mensaje `"metricas_smart"` con:
      - `"ventas_recientes"` propias.
      - `"catalogo"` propio.
    - **RecibirMetricasSmart (CyclicBehaviour)**: procesa mensajes `"metricas_smart"` de peers y actualiza:
      - `creencias["ventas_per_<peer>"]` con sus ventas recientes.
      - `creencias["catalogo_peer_<peer>"]` con su catálogo.
    - **BDIBehaviour (PeriodicBehaviour, period=10 s)**:  
      - Si `modo_adaptativo == "atraccion_clientes"`:
        1. Cuenta ventas propias (`count_propias`) y de cada peer (`sales_counts`).
        2. Encuentra mejor vendedor (`best_jid`, `best_count`).  
        3. Si algún peer supera en ventas, adopta su catálogo (`productos = copy.deepcopy(catalogo_peer)`) y registra evento en `atraccion_eventos_log`.  
        4. Si nadie ha vendido (`best_count == 0`), invoca `rotar_surtido()` y registra evento.  
        5. Si las ventas propias superan el histórico (`max_ventas`), actualiza `"max_ventas"` y `"catalogo_exitoso"`.  
        6. Finalmente, reinicia `"ventas_recientes"` y actualiza `"ventas_previas"`.  
      - Si `modo_adaptativo == "reevaluacion_productos"`:
        1. Reúne todas las ventas recibidas de supermercados normales cercanos (distancia ≤ `CERCANO_THRESHOLD`) agrupándolas por producto y variedad.  
        2. Para cada producto, identifica la variedad más vendida entre los vecinos.  
        3. Si difiere de la variedad actual, cambia la variedad (mantiene el stock) y registra el cambio en `cambios_productos_log`.  
        4. Guarda snapshot de catálogo en `productos_inteligentes_log` y registra la evaluación en `evaluacion_cambios_log`.  
        5. Actualiza `"ventas_previas"` y limpia `"ventas_recientes"`.

---

## 📝 Detalle de Configuración (config.py)

En `config.py` se encuentran:

- **Sincronización y locks**:
  ```python
  decisiones_lock = asyncio.Lock()
  ENABLE_VARIETY_CHANGE = True
  VARIETY_CHANGE_INTERVAL = 20       # segundos
  ```
- **Pesos y Umbrales**:
  ```python
  WEIGHT_ETHICAL = 1.0
  WEIGHT_DISTANCE = 0
  MAX_PURCHASES = 30
  THRESHOLD_INDISPENSABLE = 2
  CERCANO_THRESHOLD = 200            # distancia para “cercano” en supermercado inteligente
  ```
- **Número de agentes**:
  ```python
  NUM_SUPERMERCADOS = 15
  NUM_INTELIGENTES = 1
  NUM_CLIENTES = 50
  ```
- **Listados de usuarios y contraseñas** (JIDs y passwords para SPade/XMPP):
  ```python
  USUARIO_JID_SUPER = [ ... ]
  PASSWORD_SUPER      = [ ... ]
  USUARIO_JID_CLIENTE = [ ... ]
  PASSWORD_CLIENTE    = [ ... ]
  ```
- **Definición de productos, variedades y valores éticos**:
  - `possible_products`: lista de nombres de productos (manzana, leche, pan, carne, arroz, pasta, huevos, jugo, queso).
  - `possible_varieties`: diccionario que asocia cada producto a 5 variedades (`Producto_1`, `Producto_2`, …).
  - `predefined_ethics`: para cada variedad, define atributos éticos predefinidos (`huella_ecologica`, `producto_ecologico`, etc.).
- **Estructuras globales para logs e historial** (listas vacías que se van llenando durante la simulación):
  ```python
  cambios_productos_log = []
  productos_inteligentes_log = []
  evaluacion_cambios_log = []
  decisiones = []
  historial_creencias = []
  clients_finished = []
  atraccion_eventos_log = []
  ```
- **Mapas de ubicaciones** (se llenan dinámicamente):
  ```python
  clientes_ubicaciones = {}
  supermercados_ubicaciones = {}
  relaciones = {}
  ```

---

## 📈 Resultados y Salidas

Al ejecutar `python main.py`, se generan varios artefactos:

1. **`log.txt`**  
   - Contiene un registro cronológico de:
     - Inicios de agentes.
     - Peticiones y respuestas entre agentes.
     - Ventas registradas.
     - Cambios de surtido en supermercados.
     - Adopción de catálogos entre supermercados inteligentes.
     - Decisiones y consumos de clientes.
   - Cada línea tiene el formato:
     ```
     2025-06-03 HH:MM:SS - [ID_AGENTE] Mensaje de log…
     ```

2. **Carpeta `capturas/`**  
   - **Diagramas de decisiones de compra**:  
     - `clientes_supermercados_compra_<N>.png` para cada ronda `N` (muestra con puntos y flechas el trayecto de cada cliente hacia el supermercado escogido; clientes en gris, supermercados normales en azul, supermercados inteligentes en rojo).  
   - **Gráfico de barras de visitas inteligentes**:  
     - `visitas_totales_smart_ronda1_vs_final.png`: compara el número de clientes que acudieron a supermercados inteligentes en la primera ronda vs la última.

3. **`Resultados_simulacion.xlsx`**  
   - **Hoja “Decisiones”**: cada fila corresponde a un evento de tipo `"compra"`, `"compra_indispensable"`, `"consumo"` o `"final"` con detalles:
     - `cliente_id`, `accion`, `supermercado_elegido`, `productos_comprados` / `productos_consumidos`, `timestamp`, `numero_compra`, etc.
   - **Hoja “Agentes”**: descripción de cada agente (clientes, supermercados normales e inteligentes) con:
     - Tipo, ID, ubicación, creencias iniciales, deseos, hora de creación, ventas registradas/recibidas.
   - **Hoja “Ventas Registradas”**: historial completo de ventas en supermercados normales.
   - **Hoja “Ventas Inteligentes”**: historial de ventas procesadas por supermercados inteligentes.
   - **Hoja “Cambios de Productos”**: (si aplica) lista de tuplas `(producto, variedad_antigua, variedad_nueva, supermercado_id)`.
   - **Hoja “Productos Inteligentes”**: snapshots de catálogos de supermercados inteligentes tras cada cambio.
   - **Hoja “Reevaluacion”**: detalles de cada evaluación (ventas próximas, `nearby_sales`, cambios sugeridos).
   - **Hoja “Atraccion_Clientes”**: eventos en los que un supermercado inteligente adopta el catálogo de un peer o rota su surtido ante falta de ventas.

4. **Carpeta `csv's/`**  
   - Archivos separados por hoja que replican la información de `Resultados_simulacion.xlsx` en formato CSV:
     - `decisiones.csv`, `agentes.csv`, `ventas_registradas.csv`, `ventas_inteligentes.csv`, `cambios_de_creencias.csv`, `atraccion_clientes.csv`, `reevaluacion.csv`, etc.

---

## 🎯 Casos de Uso y Flujo General

1. **Inicialización**  
   - Se crean `NUM_INTELIGENTES` agentes `SupermercadoInteligente` y `NUM_SUPERMERCADOS` agentes `SupermercadoAgent`.  
   - Luego se crean `NUM_CLIENTES` instancias de `ClienteAgent`.  
   - Cada agente se conecta a un servidor XMPP mediante su JID y contraseña; se registra su ubicación aleatoria en `clientes_ubicaciones` o `supermercados_ubicaciones`.

2. **Interacción Cliente ↔ Supermercado (rondas periódicas)**  
   - Cada cliente, cada 5 s, envía a todos los supermercados un mensaje de petición (`"Peticion_Cliente"`).  
   - Cada supermercado (normal e inteligente) responde con un mensaje `"Peticion_Cliente"` conteniendo:
     - Su catálogo (`productos`: stock y atributos éticos).
     - Su ubicación (`ubicacion`).  
   - El cliente recoge todas estas ofertas en sus creencias.  

3. **Deliberación de Compra**  
   - Tras recibir todas (o las que lleguen en 10 s), el cliente:
     - Verifica si debe finalizar (número de compras ≥ `MAX_PURCHASES`).
     - Verifica si hay productos “indispensables” con stock bajo; si es así, realiza una compra imprescindible.
     - Si no hay faltantes urgentes y el inventario personal es menor a 8 unidades, realiza una compra normal (comprando de forma aleatoria según stock).
     - En caso contrario, simula consumo y ajusta inventario.  
   - El cliente elige el “mejor supermercado” con un puntaje que combina:
     - `score ético` = suma (valor_cliente × valor_producto) por cada criterio ético.
     - `penalización por distancia` = distancia euclídea × `WEIGHT_DISTANCE`.  
   - Después de decidir, el cliente envía un mensaje de venta al supermercado elegido.

4. **Procesamiento de Ventas en Supermercados Normales**  
   - Al recibir un mensaje de venta, el supermercado normal actualiza su inventario (dismunuye stock), agrega la venta a `ventas_delta` y `ventas_registradas_hist`, y actualiza `creencias["ventas"]`.
   - Cada 30 ventas, rota automáticamente el surtido (cambia la variedad de cada producto a otra distinta).
   - En paralelo, el supermercado empuja cada nueva venta en `ventas_delta` a todos sus peers inteligentes (cada 1 s).

5. **Procesamiento en Supermercados Inteligentes**  
   - **Modo “atraccion_clientes”** (por defecto):
     - Cada 15 s envían métricas a sus peers inteligentes (`ventas_recientes` y `catalogo`).
     - Cada 10 s:  
       - Comparan sus ventas recientes con las de los peers.  
       - Si algún peer vende más, adoptan su catálogo (copia profunda).  
       - Si nadie vende, rotan su surtido internamente.  
       - Si superan su máximo histórico de ventas, actualizan su catálogo exitoso.  
   - **Modo “reevaluacion_productos”**:
     - Cada 10 s agrupan las ventas recibidas de supermercados normales ubicados a ≤ `CERCANO_THRESHOLD`.
     - Identifican, para cada producto, la variedad más vendida en esa vecindad.  
     - Si difiere de la propia, cambian la variedad (conservando stock) y registran en logs.  
     - Guardan snapshots y entradas de evaluación para análisis posterior.

6. **Finalización**  
   - Una vez que **todos** los clientes han completado sus rondas de compra o alcanzado `MAX_PURCHASES` (lista `clients_finished`), se detienen todos los agentes.
   - Se generan automáticamente los informes (Excel, CSV, gráficos) y se cierran.

---

## 📚 Ejemplos de Uso

1. **Ejecutar con parámetros por defecto**  
   ```bash
   python main.py
   ```
   - Crea 1 supermercado inteligente, 15 supermercados normales y 50 clientes.
   - Se graban logs en `log.txt`.
   - Al final, se generan `Resultados_simulacion.xlsx`, gráfico de visitas inteligentes y diagramas de trayectos.

2. **Modificar número de agentes**  
   En `config.py`:
   ```python
   NUM_INTELIGENTES = 2
   NUM_SUPERMERCADOS = 10
   NUM_CLIENTES = 30
   ```
   Luego:
   ```bash
   python main.py
   ```

3. **Cambiar modo adaptativo de supermercados inteligentes**  
   En `main.py`, al instanciar:
   ```python
   smart = SupermercadoInteligente(
       jid, pwd, modo_adaptativo="reevaluacion_productos", peer_smart_jids=[]
   )
   ```
   — o bien, pasar el argumento correspondiente desde variables de entorno o parámetros de línea de comandos (personalización adicional).

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Puedes sugerir mejoras en:

- Estrategias de deliberación BDI de clientes (p. ej., nuevos criterios éticos o lógica de deseos).
- Lógica de adaptación de supermercados inteligentes (experimentar con diferentes umbrales, modos, métricas).
- Visualizaciones y reportes más detallados (dashboard interactivo, gráficas de tiempo real).
- Tests unitarios y de integración para los comportamientos de los agentes.
- Documentación adicional y ejemplos de casos de uso.

Para contribuir:
1. Haz un “fork” del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz “commit”.
4. Abre un **Pull Request** describiendo tu propuesta y cómo probarla.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.

---

## 📝 Contacto

- **Autor**: Ángel Casado Bellisco 
- **Email**: acasado1091@gmail.com 
- **Repositorio**: https://github.com/angelcasaado/TFG-Agentes-BDI-Supermercado/

Para preguntas, reportes de errores o sugerencias, crea un “issue” en GitHub o escríbeme directamente.

---

¡Gracias por usar esta simulación de supermercados inteligentes! Espero que te sea útil para explorar dinámicas BDI, algoritmos éticos de decisión y adaptación cooperativa/competitiva en entornos multi-agente.  
# TFG-Agentes-BDI-Supermercado
