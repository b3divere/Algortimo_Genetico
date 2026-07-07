"""
Este script NO reimplementa el algoritmo: importa las funciones desde
laberinto_ag.py y solo se encarga de la parte visual/interactiva.

Ejecutar con:
    streamlit run app_streamlit.py
"""

import json
import tempfile
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from Algoritmo import (
    algoritmo_genetico,
    cargar_laberinto_csv,
    ejecutar_individuo,
    validar_laberinto,
)

# =============================================================================
# CONFIGURACION DE LA PAGINA
# =============================================================================
st.set_page_config(page_title="AG Laberinto", page_icon="🧭", layout="wide")
st.title("Algoritmo genético — resolución de laberintos")
st.caption("Interfaz gráfica sobre laberinto_ag.py (INFO-1159)")

COLORES_CELDAS = {
    "X": "#2b2b2b",   # muro
    "0": "#f5f5f5",   # camino libre
    "1": "#4c8bf5",   # salida
    "2": "#2ecc71",   # llegada
}


# =============================================================================
# HELPERS DE VISUALIZACION
# =============================================================================
def dibujar_laberinto(laberinto, trayectoria=None, hasta_paso=None, titulo="", escala=0.5):
    """Dibuja la grilla del laberinto y, opcionalmente, la trayectoria recorrida
    hasta el paso indicado (para poder animarla con un slider).

    `escala` es el tamaño de cada celda en pulgadas (tamaño fijo, no se
    recalcula según filas/columnas). Si quieres que se vea más chico en
    pantalla, achica el contenedor donde se dibuja, no esta escala.
    """
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])

    ancho = total_columnas * escala + 1
    alto = total_filas * escala + 1
    fig, ax = plt.subplots(figsize=(ancho, alto))

    for i in range(total_filas):
        for j in range(total_columnas):
            color = COLORES_CELDAS.get(laberinto[i][j], "#ffffff")
            ax.add_patch(
                plt.Rectangle((j, total_filas - i - 1), 1, 1, facecolor=color, edgecolor="#cccccc")
            )

    if trayectoria:
        recorte = trayectoria if hasta_paso is None else trayectoria[: hasta_paso + 1]
        xs = [col + 0.5 for (_, col) in recorte]
        ys = [total_filas - fila - 0.5 for (fila, _) in recorte]

        ax.plot(xs, ys, color="#e74c3c", linewidth=2, zorder=3)
        ax.scatter(xs, ys, color="#e74c3c", s=25, zorder=4)
        # Marca la posicion actual (ultimo punto del recorte) con una estrella
        ax.scatter(xs[-1], ys[-1], color="#c0392b", s=180, marker="*", zorder=5)

    ax.set_xlim(0, total_columnas)
    ax.set_ylim(0, total_filas)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(titulo)

    return fig


def trayectoria_de_posiciones(cromosoma, laberinto, posicion_inicial, direccion_inicial):
    """Recalcula la trayectoria (fila, columna) de un cromosoma ya evaluado,
    para poder graficarla (algoritmo_genetico no la devuelve para cada
    individuo, solo el resumen numerico)."""
    datos = ejecutar_individuo(
        cromosoma, laberinto, posicion_inicial, direccion_inicial, None
    )
    return datos["trayectoria"]


# =============================================================================
# BARRA LATERAL: CONFIGURACION Y ARCHIVOS
# =============================================================================
st.sidebar.header("Configuración")

modo_config = st.sidebar.radio(
    "Origen de los parámetros", ["Archivo config.json", "Ajustar manualmente"]
)

archivo_config_subido = st.sidebar.file_uploader("config.json (opcional)", type="json")
archivo_csv_subido = st.sidebar.file_uploader("Laberinto (.csv)", type="csv")

if modo_config == "Archivo config.json":
    if archivo_config_subido is not None:
        config = json.load(archivo_config_subido)
    else:
        ruta_default = Path("config.json")
        if ruta_default.exists():
            config = json.loads(ruta_default.read_text(encoding="utf-8"))
        else:
            st.sidebar.warning("No se encontró config.json local; sube uno o cambia a modo manual.")
            config = {"csv": "laberinto_valido.csv", "n": 15, "pm": 0.15, "N": 21, "G": 300, "ps": 0.3, "seed": 7}

    n = int(config["n"])
    pm = float(config["pm"])
    N = int(config["N"])
    G = int(config["G"])
    ps = float(config["ps"])
    seed = int(config["seed"])
    ruta_csv_config = config.get("csv", "laberinto_valido.csv")
else:
    n = st.sidebar.number_input("n (longitud del cromosoma)", min_value=2, value=15)
    pm = st.sidebar.slider("pm (prob. de mutación)", 0.0, 1.0, 0.15)
    N = st.sidebar.number_input("N (tamaño de población, impar)", min_value=3, value=21, step=2)
    G = st.sidebar.number_input("G (generaciones)", min_value=1, value=300)
    ps = st.sidebar.slider("ps (presión selectiva)", 0.01, 0.99, 0.3)
    seed = st.sidebar.number_input("seed", value=7)
    ruta_csv_config = "laberinto_valido.csv"

# Velocidad de la reproduccion automatica
velocidad_reproduccion = st.sidebar.slider(
    "Velocidad de reproducción automática (seg/paso)", 0.1, 2.0, 0.5, 0.1,
)

# Resolver la ruta del CSV: subido > la del config/manual > default
if archivo_csv_subido is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.write(archivo_csv_subido.getvalue())
    tmp.close()
    ruta_csv = tmp.name
else:
    ruta_csv = ruta_csv_config

ejecutar = st.sidebar.button("Ejecutar algoritmo genético", type="primary")

# =============================================================================
# EJECUCION
# =============================================================================
if ejecutar:
    if N % 2 == 0:
        st.error("N debe ser impar.")
        st.stop()

    try:
        with st.spinner("Corriendo el algoritmo genético..."):
            resultado = algoritmo_genetico(
                ruta_csv, n, pm, N, G, ps, seed,
                mostrar_graficos=False, verbose=False,
            )
        st.session_state["resultado"] = resultado
        # Al ejecutar de nuevo, reiniciamos el estado de reproduccion
        st.session_state["reproduciendo"] = False
        st.session_state.pop("cromosoma_actual", None)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo del laberinto: {ruta_csv}")
        st.stop()
    except ValueError as error:
        st.error(f"Laberinto inválido: {error}")
        st.stop()

# =============================================================================
# RESULTADOS
# =============================================================================
if "resultado" not in st.session_state:
    st.info("Configura los parámetros en la barra lateral y presiona **Ejecutar algoritmo genético**.")
    st.stop()

resultado = st.session_state["resultado"]
mejor_global = resultado["mejor_global"]
mejores_unicos = resultado["mejores_unicos"]
laberinto = resultado["laberinto"]
posicion_inicial = resultado["posicion_inicial"]
direccion_inicial = resultado["direccion_inicial"]

st.subheader("Resumen del mejor individuo global")
col1, col2, col3, col4 = st.columns(4)
col1.metric("J(x)", mejor_global["J"])
col2.metric("Válido", "Sí" if mejor_global["valido"] else "No")
col3.metric("Distancia final (D)", mejor_global["distancia"])
col4.metric("Pasos (τ)", mejor_global["tau"])

st.code(f"Cromosoma: {mejor_global['cromosoma']}", language="text")

# --- Graficos de evolucion -----------------------------------------------
st.subheader("Evolución de la búsqueda")
c1, c2 = st.columns(2)

with c1:
    fig, ax = plt.subplots()
    ax.plot(range(1, len(resultado["historial_mejor_j"]) + 1), resultado["historial_mejor_j"], marker="o")
    ax.set_yscale("log")
    ax.set_xlabel("Generación")
    ax.set_ylabel("Mejor J(x) global (log)")
    ax.set_title("Mejor J(x) por generación")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    st.pyplot(fig)

with c2:
    fig, ax = plt.subplots()
    ax.plot(range(1, len(resultado["historial_prop_validas"]) + 1), resultado["historial_prop_validas"], marker="o")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Generación")
    ax.set_ylabel("Proporción de soluciones válidas")
    ax.set_title("Proporción de válidas por generación")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)

# --- Trayectorias de los mejores cromosomas, lado a lado -------------------
st.subheader("Trayectoria en el laberinto")

# Precalculamos la trayectoria de cada cromosoma una sola vez
trayectorias = [
    trayectoria_de_posiciones(ind["cromosoma"], laberinto, posicion_inicial, direccion_inicial)
    for ind in mejores_unicos
]

# Inicializar/asegurar el paso de cada panel
for indice, tray in enumerate(trayectorias):
    key_paso = f"paso_actual_{indice}"
    if key_paso not in st.session_state:
        st.session_state[key_paso] = len(tray) - 1

# Botones globales: controlan TODOS los paneles a la vez
col_reset_g, col_play_g = st.columns(2)
with col_reset_g:
    reiniciar_click = st.button("Reiniciar todo", width="stretch")
with col_play_g:
    reproducir_click = st.button("Reproducir todo", width="stretch")

if reiniciar_click:
    for indice in range(len(trayectorias)):
        st.session_state[f"paso_actual_{indice}"] = 0

# Aplicar cualquier paso pendiente (dejado por una reproducción anterior)
# ANTES de crear los sliders de esta corrida.
for indice in range(len(trayectorias)):
    key_pendiente = f"paso_pendiente_{indice}"
    if key_pendiente in st.session_state:
        st.session_state[f"paso_actual_{indice}"] = st.session_state.pop(key_pendiente)


def _render_panel(indice, individuo, tray, paso_a_mostrar, placeholder):
    cromosoma = individuo["cromosoma"]
    gen_actual = cromosoma[paso_a_mostrar - 1] if paso_a_mostrar > 0 else "—"
    fig = dibujar_laberinto(
        laberinto, tray, hasta_paso=paso_a_mostrar,
        titulo=f"Paso {paso_a_mostrar}/{len(tray) - 1}  (gen={gen_actual})",
    )
    placeholder.pyplot(fig)
    plt.close(fig)


# --- Layout: sliders + placeholders, uno por panel, de a 2 por fila --------
COLUMNAS_POR_FILA = 2
pasos_actuales = []       # valor actual del slider de cada panel (para saber desde donde reproducir)
placeholders = []         # placeholder de cada panel, en el mismo orden que mejores_unicos

# Posiciones donde el gen difiere entre los cromosomas mostrados (para resaltarlas en amarillo)
largo_max_cromosoma = max(len(ind["cromosoma"]) for ind in mejores_unicos)
posiciones_distintas = {
    pos for pos in range(largo_max_cromosoma)
    if len({ind["cromosoma"][pos] for ind in mejores_unicos if pos < len(ind["cromosoma"])}) > 1
}

for inicio_fila in range(0, len(mejores_unicos), COLUMNAS_POR_FILA):
    columnas = st.columns(COLUMNAS_POR_FILA)
    for offset, columna in enumerate(columnas):
        indice = inicio_fila + offset
        if indice >= len(mejores_unicos):
            continue
        individuo = mejores_unicos[indice]
        tray = trayectorias[indice]
        with columna:
            genes_html = " ".join(
                f'<span style="background-color:#f5d90a;color:#000;padding:2px 6px;'
                f'border-radius:4px;font-family:monospace;">{gen}</span>'
                if pos in posiciones_distintas else
                f'<span style="background-color:#2b2b2b;color:#7ee787;padding:2px 6px;'
                f'border-radius:4px;font-family:monospace;">{gen}</span>'
                for pos, gen in enumerate(individuo["cromosoma"])
            )
            st.markdown(
                f"**#{indice + 1}** J={individuo['J']} · pasos={individuo['pasos']}"
                f"&nbsp;&nbsp; {genes_html}",
                unsafe_allow_html=True,
            )
            paso = st.slider(
                "Paso", 0, len(tray) - 1,
                key=f"paso_actual_{indice}",
            )
            placeholder_figura = st.empty()
            _render_panel(indice, individuo, tray, paso, placeholder_figura)
            pasos_actuales.append(paso)
            placeholders.append(placeholder_figura)

# --- Reproducción sincronizada de todos los paneles -------------------------
if reproducir_click:
    largo_max = max(len(t) for t in trayectorias)
    # Si todos ya estaban al final, reproduce desde el principio
    inicio = 0 if all(p >= len(t) - 1 for p, t in zip(pasos_actuales, trayectorias)) else min(pasos_actuales)

    for paso_global in range(inicio, largo_max):
        for indice, (individuo, tray, placeholder) in enumerate(zip(mejores_unicos, trayectorias, placeholders)):
            paso_local = min(paso_global, len(tray) - 1)
            _render_panel(indice, individuo, tray, paso_local, placeholder)
        time.sleep(velocidad_reproduccion)

    for indice, tray in enumerate(trayectorias):
        st.session_state[f"paso_pendiente_{indice}"] = len(tray) - 1
    st.rerun()


# --- Tabla de mejores unicos ------------------------------------------------
st.subheader("Mejores cromosomas únicos (J*)")
st.dataframe(
    [{"#": i + 1, "J": ind["J"], "pasos (τ)": ind["pasos"], "cromosoma": " ".join(ind["cromosoma"])}
     for i, ind in enumerate(mejores_unicos)],
    width="stretch",
)