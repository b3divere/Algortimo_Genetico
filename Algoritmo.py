from random import choices, choice, randint, random, randrange, seed as fijar_semilla
from typing import Callable, List, NamedTuple, Tuple
from functools import partial
from time import time
import csv
import json
import matplotlib.pyplot as plt
import argparse

# =============================================================================
# CONSTANTES
# =============================================================================
DIRECCIONES = ("N", "E", "S", "O")
A = ["H", "A", "M", "Q"]
VECTORES = {
    "N": (-1, 0),
    "E": (0, 1),
    "S": (1, 0),
    "O": (0, -1)
}

Pos = Tuple[int, int]

# =============================================================================
# PARÁMETROS DEL ALGORITMO
# =============================================================================
# n  -> longitud del cromosoma
# pm -> probabilidad de mutación por gen
# N  -> número de cromosomas por generación (debe ser impar)
# G  -> número total de generaciones
# ps -> parámetro de presión selectiva (ranking geométrico)
# seed -> semilla aleatoria para reproducibilidad

CAMPOS_CONFIG_REQUERIDOS = ("csv", "n", "pm", "N", "G", "ps", "seed")

# Lee la ruta del archivo de configuración desde línea de comandos y delega la carga.
def leer_parametros():
    parser = argparse.ArgumentParser(
        description="Algoritmo genetico para la resolucion de laberintos"
    )
    parser.add_argument("--config", type=str, default="config.json",
                         help="Ruta del archivo de configuracion JSON")

    argumentos = parser.parse_args()

    return cargar_configuracion(argumentos.config)


# Carga y valida los parámetros del algoritmo desde un archivo JSON.
def cargar_configuracion(ruta_config):
    with open(ruta_config, "r", encoding="utf-8") as archivo_config:
        config = json.load(archivo_config)

    faltantes = [campo for campo in CAMPOS_CONFIG_REQUERIDOS if campo not in config]
    if faltantes:
        raise ValueError(
            f"Faltan claves en el archivo de configuracion '{ruta_config}': {faltantes}"
        )

    return (
        config["csv"],
        config["n"],
        config["pm"],
        config["N"],
        config["G"],
        config["ps"],
        config["seed"],
    )

# =============================================================================
# ETAPA 1: LECTURA, PARÁMETROS Y VALIDACIÓN DEL LABERINTO (5%)
# =============================================================================

# Lee el CSV del laberinto y lo retorna como matriz de filas.
def cargar_laberinto_csv(ruta_csv):
    laberinto = []

    with open(ruta_csv, "r", encoding="utf-8") as archivo:
        lector = csv.reader(archivo, delimiter=",")

        for fila in lector:
            laberinto.append(fila)

    return laberinto

# Verifica que todas las celdas del laberinto usen símbolos válidos.
def validar_simbolos(laberinto):
    simbolos_validos = {"0","1","2","X"}
    
    for i, fila in enumerate(laberinto):
        for j, celda in enumerate(fila):
            if celda not in simbolos_validos:
                raise ValueError(f"Simbolo invalido '{celda}' en la posicion ({i},{j})")

# Ubica la única celda de salida ('1') del laberinto.
def encontrar_salida(laberinto):
    posiciones = [
        (i, j)
        for i, fila in enumerate(laberinto)
        for j, celda in enumerate(fila)
        if celda == "1"
    ]
 
    if len(posiciones) != 1:
        raise ValueError(
            f"Debe existir exactamente una salida ('1'); se encontraron {len(posiciones)}."
        )
 
    return posiciones[0]

# Ubica la única celda de llegada ('2') del laberinto.
def encontrar_llegada(laberinto):
    posiciones = [
        (i, j)
        for i, fila in enumerate(laberinto)
        for j, celda in enumerate(fila)
        if celda == "2"
    ]
    
    if len(posiciones) != 1:
        raise ValueError(f"Debe existir exactamente una llegada ('2'); se encontraron {len(posiciones)}.")

    return posiciones[0]

# Verifica que todo el perímetro del laberinto sea muro.
def validar_muros_perimetrales(laberinto):
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])
 
    for i in range(total_filas):
        for j in range(total_columnas):
            en_el_perimetro = i == 0 or i == total_filas - 1 or j == 0 or j == total_columnas - 1
            
            if en_el_perimetro and laberinto[i][j] != "X":
                raise ValueError(f"El perimetro debe ser todo muro; falla en la posicion ({i},{j}).")

# Verifica que las celdas interiores vecinas a una posición (salida o llegada) estén despejadas.
def validar_zona_despejada(laberinto, posicion):
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])
    fila, columna = posicion
 
    for a in range(fila - 1, fila + 2):
        for b in range(columna - 1, columna + 2):
            if (a, b) == (fila, columna):
                continue
 
            es_celda_interior = 1 <= a <= total_filas - 2 and 1 <= b <= total_columnas - 2
 
            if es_celda_interior and laberinto[a][b] == "X":
                raise ValueError(
                    f"La celda interior ({a},{b}), junto a ({fila},{columna}), es un muro; "
                    "debe estar despejada."
                )

# Ejecuta todas las validaciones estructurales del laberinto y retorna salida y llegada.
def validar_laberinto(laberinto):
    total_filas = len(laberinto)
    if total_filas == 0:
        raise ValueError("El laberinto esta vacio.")
 
    total_columnas = len(laberinto[0])
    for i, fila in enumerate(laberinto):
        if len(fila) != total_columnas:
            raise ValueError(f"La fila {i} no tiene el mismo numero de columnas que las demas.")
 
    validar_simbolos(laberinto)
    validar_muros_perimetrales(laberinto)
 
    posicion_salida = encontrar_salida(laberinto)
    posicion_llegada = encontrar_llegada(laberinto)
 
    if posicion_salida[0] != 1:
        raise ValueError("La salida debe estar en la primera fila interior válida (fila 2, indexacion 1).")
 
    if posicion_llegada[0] != total_filas - 2:
        raise ValueError("La llegada debe estar en la última fila interior válida (fila m-1, indexacion 1).")
 
    validar_zona_despejada(laberinto, posicion_salida)
    validar_zona_despejada(laberinto, posicion_llegada)
 
    return posicion_salida, posicion_llegada

# =============================================================================
# ETAPA 2: REPRESENTACIÓN DEL INDIVIDUO Y EJECUCIÓN DEL CROMOSOMA (5%)
# =============================================================================

# Genera un cromosoma aleatorio de la longitud dada (genes H, A, M, Q).
def cromosoma(longitud):
    return choices(A, k=longitud)

# Genera una población inicial de N cromosomas de longitud n.
def poblacion(N, n):
    if N % 2 == 0 or N < 3:
        raise ValueError("El tamaño de la poblacion debe ser impar y >= 3")
    
    return [cromosoma(n) for _ in range(N)]

# Indica si una posición está dentro del laberinto y no es muro.
def es_transitable(laberinto, pos):
    fila, columna = pos
    
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])
    
    if fila < 0 or fila >= total_filas:
        return False
    if columna < 0 or columna >= total_columnas:
        return False
    
    return laberinto[fila][columna] != "X"

# Simula el movimiento del individuo en el laberinto y retorna trayectoria y datos crudos.
def ejecutar_individuo(individuo, laberinto, posicion_inicial, direccion_inicial, posicion_llegada):
    direccion = direccion_inicial
    posicion = posicion_inicial
    
    trayectoria = [posicion]
    choques = 0
    bloques_giros = []
    contador_giros = 0
    acciones_en_meta = 0

    for gen in individuo:
        pos_anterior = posicion
        
        if pos_anterior == posicion_llegada and gen in ("H", "A", "M"):
            acciones_en_meta += 1

        if gen == "M":
            vector = VECTORES[direccion]
            pos_tentativa = (posicion[0] + vector[0], posicion[1] + vector[1])

            if es_transitable(laberinto, pos_tentativa):
                posicion = pos_tentativa
                if contador_giros > 0:
                    bloques_giros.append(contador_giros)
                contador_giros = 0
            else:
                choques += 1

        elif gen == "A":
            indice = DIRECCIONES.index(direccion)
            direccion = DIRECCIONES[(indice - 1) % 4]
            contador_giros += 1

        elif gen == "H":
            indice = DIRECCIONES.index(direccion)
            direccion = DIRECCIONES[(indice + 1) % 4]
            contador_giros += 1

        elif gen == "Q":
            pass

        trayectoria.append(posicion)

    if contador_giros > 0:
        bloques_giros.append(contador_giros)

    return {
        "trayectoria": trayectoria,
        "choques": choques,
        "bloques_giros": bloques_giros,
        "acciones_en_meta": acciones_en_meta,
        "posicion_final": posicion
    }

# =============================================================================
# ETAPA 3: FUNCIÓN OBJETIVO, VALIDEZ Y PENALIDADES (15%)
# =============================================================================

# Calcula la distancia Manhattan entre la posición final y la llegada.
def distancia_manhattan(posicion_final, posicion_llegada):
    return abs(posicion_final[0] - posicion_llegada[0]) + abs(posicion_final[1] - posicion_llegada[1])

# Retorna los instantes en que la trayectoria entra efectivamente a la llegada.
def llegada_efectiva(trayectoria, posicion_llegada):
    tz = []

    for t in range(1, len(trayectoria)):
        posicion_anterior = trayectoria[t - 1]
        posicion_actual = trayectoria[t]

        if posicion_anterior != posicion_llegada and posicion_actual == posicion_llegada:
            tz.append(t)

    return tz

# Retorna el último instante de llegada efectiva, o None si nunca llegó.
def ultima_llegada_efectiva(conjunto_tz):
    if len(conjunto_tz) == 0:
        return None
    return max(conjunto_tz)

# Calcula tau(x): el instante de detención válida tras la última llegada, o n+1 si no aplica.
def tau(individuo, conjunto_tz, ultima_llegada):
    n = len(individuo)

    if len(conjunto_tz) == 0:
        return n + 1

    if ultima_llegada >= n:
        return n + 1

    genes_despues = individuo[ultima_llegada:]

    todos_son_q = all(gen == "Q" for gen in genes_despues)

    if todos_son_q:
        return ultima_llegada
    else:
        return n + 1

# Determina si el cromosoma llegó a la meta y se detuvo válidamente.
def es_valida(conjunto_tz, tau_valor, n):
    return len(conjunto_tz) > 0 and tau_valor <= n

# =============================================================================
# PENALIZACIONES
# =============================================================================

# Penaliza las pausas (Q) intermedias antes del último gen activo.
def penalizacion_pausa(individuo):
    ultimo_activo = -1
    for k, gen in enumerate(individuo):
        if gen != "Q":
            ultimo_activo = k
            
    if ultimo_activo == -1:
        return 0
        
    pausas_interiores = sum(1 for k in range(ultimo_activo) if individuo[k] == "Q")
    return pausas_interiores * 10


# Penaliza los choques contra muros.
def penalizacion_choques(contador_choques):
    return contador_choques * 30


# Calcula f(b) para un bloque de giros consecutivos de tamaño b.
def f_bloque(b):
    if b <= 1: return 0
    if b == 2: return 10
    if b == 3: return 30
    return 120 * (b - 3)

# Penaliza los bloques de giros consecutivos según f(b).
def penalizacion_bloques_giros(lista_bloques_giros):
    return sum(f_bloque(b) for b in lista_bloques_giros)

# Penaliza las acciones activas realizadas después de llegar a la meta.
def penalizacion_post_meta(acciones_activas_post_meta):
    return acciones_activas_post_meta * 100

# Penaliza las Q prematuras cuando el individuo no es válido.
def penalizacion_detencion_prematura(individuo, individuo_es_valido):
    if individuo_es_valido: return 0
    
    ultimo_activo = -1
    for k, gen in enumerate(individuo):
        if gen != "Q":
            ultimo_activo = k
            
    q_prematuras = len(individuo) - (ultimo_activo + 1)
    return q_prematuras * 10

# Aplica una penalización fija cuando el individuo no es válido.
def penalizacion_invalidez(individuo_es_valido):
    return 0 if individuo_es_valido else 10000

# Combina distancia, tau y todas las penalizaciones en la función objetivo J(x).
def funcion_objetivo(distancia, tau_valor, pq, pc, pr, pa, pprem, pinv):
    return distancia + tau_valor + pq + pc + pr + pa + pprem + pinv

# Convierte J(x) en fitness (a menor J, mayor fitness).
def calcular_fitness(j_valor):
    return -j_valor

# =============================================================================
# ETAPA 4: SELECCIÓN POR RANKING GEOMÉTRICO Y ELITISMO (8%)
# =============================================================================

# Calcula rho(x): 0 si válido, 1 si llegó pero no válido, 2 si nunca llegó.
def rho(individuo_es_valido, llego_alguna_vez):
    if individuo_es_valido:
        return 0
    elif llego_alguna_vez:
        return 1
    else:
        return 2

# Ordena la población evaluada lexicográficamente por (rho, J, distancia, tau).
def ordenar_poblacion(poblacion_evaluada):
    poblacion_evaluada.sort(key=lambda ind: (ind["rho"], ind["J"], ind["distancia"], ind["tau"]))
    return poblacion_evaluada

# Calcula las probabilidades normalizadas de ranking geométrico para N individuos.
def probabilidades_normalizadas(N, ps):
    probabilidades = []
    
    denominador = 1 - (1 - ps)**N
    
    for i in range(1, N +1):
        pi = (ps * (1 - ps)**(i - 1)) / denominador
        probabilidades.append(pi)
    
    return probabilidades

# Calcula la distribución acumulada Ci a partir de las probabilidades Pi.
def distribucion_acumulada(probabilidades):
    ci = []
    suma_actual = 0
    
    for p in probabilidades:
        suma_actual += p
        ci.append(suma_actual)
    return ci

# Selecciona un padre por ranking geométrico usando la distribución acumulada.
def seleccionar_padre(poblacion_ordenada, distribucion_acumulada_ci):
    u = random()
    
    for i in range(len(distribucion_acumulada_ci)):
        if u <= distribucion_acumulada_ci[i]:
            return poblacion_ordenada[i]
    
    return poblacion_ordenada[-1]

# Construye la nueva generación conservando el mejor individuo global (elitismo).
def aplicar_elitismo(mejor_global, descendientes):
    nueva_poblacion = [mejor_global["cromosoma"]]
    
    for hijo in descendientes:
        nueva_poblacion.append(hijo)
        
    return nueva_poblacion

# =============================================================================
# ETAPA 5: CRUZAMIENTO, MUTACIÓN POR GEN Y REEVALUACIÓN (12%)
# =============================================================================

# Realiza cruzamiento de un punto entre dos padres y retorna dos descendientes.
def cruzamiento_un_punto(padre_x, padre_y):
    n = len(padre_x)

    if len(padre_y) != n:
        raise ValueError("Los padres deben tener la misma longitud.")

    if n < 2:
        raise ValueError("La longitud del cromosoma debe ser al menos 2 para aplicar cruzamiento.")

    punto_corte = randint(1, n - 1)

    descendiente_1 = padre_x[:punto_corte] + padre_y[punto_corte:]
    descendiente_2 = padre_y[:punto_corte] + padre_x[punto_corte:]

    return descendiente_1, descendiente_2

# Muta un gen a una acción distinta de la actual, elegida al azar.
def mutar_gen(gen_actual):
    opciones = []
    for accion in A:
        if accion != gen_actual:
            opciones.append(accion)

    return choice(opciones)

# Aplica mutación gen a gen sobre un descendiente, con probabilidad pm por gen.
def mutacion_por_gen(descendiente, pm):
    nuevo = list(descendiente)

    for i in range(len(nuevo)):
        numero_al_azar = random()

        if numero_al_azar < pm:
            nuevo[i] = mutar_gen(nuevo[i])

    return nuevo


# Ejecuta y evalúa un descendiente desde cero, recalculando J(x) y sus componentes.
def reevaluar_descendiente(descendiente, laberinto, posicion_inicial, direccion_inicial, posicion_llegada):
    datos = ejecutar_individuo(descendiente, laberinto, posicion_inicial, direccion_inicial, posicion_llegada)
    
    n = len(descendiente)
    distancia = distancia_manhattan(datos["posicion_final"], posicion_llegada)
    conjunto_tz = llegada_efectiva(datos["trayectoria"], posicion_llegada)
    ultima_llegada = ultima_llegada_efectiva(conjunto_tz)
    
    tau_valor = tau(descendiente, conjunto_tz, ultima_llegada)
    individuo_es_valido = es_valida(conjunto_tz, tau_valor, n)
    
    pq = penalizacion_pausa(descendiente)
    pc = penalizacion_choques(datos["choques"])
    pr = penalizacion_bloques_giros(datos["bloques_giros"])
    pa = penalizacion_post_meta(datos["acciones_en_meta"])
    pprem = penalizacion_detencion_prematura(descendiente, individuo_es_valido)
    pinv = penalizacion_invalidez(individuo_es_valido)
    
    j_valor = funcion_objetivo(distancia, tau_valor, pq, pc, pr, pa, pprem, pinv)

    fit = calcular_fitness(j_valor)
    
    return {
        "cromosoma": descendiente,
        "J": j_valor,
        "fitness": fit,
        "rho": rho(individuo_es_valido, len(conjunto_tz) > 0),
        "distancia": distancia,
        "tau": tau_valor,
        "valido": individuo_es_valido
    }


# =============================================================================
# ETAPA 6: RESULTADOS MÍNIMOS Y GRÁFICAS (5%)
# =============================================================================

# Grafica la evolución del mejor J(x) global por generación en escala logarítmica.
def graficar_mejor_objetivo_log(historial_mejor_j_por_generacion):
    generaciones = list(range(1, len(historial_mejor_j_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_mejor_j_por_generacion, marker="o")
    plt.yscale("log")
    plt.xlabel("Generación")
    plt.ylabel("Mejor J(x) global (escala log)")
    plt.title("Evolución del mejor valor de función objetivo")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)


# Lista los cromosomas únicos que alcanzan el mejor J* encontrado.
def listar_mejores_cromosomas_unicos(poblacion_historica_evaluada, verbose=True):
    if not poblacion_historica_evaluada:
        if verbose:
            print("No hay individuos evaluados.")
        return []

    j_estrella = min(ind["J"] for ind in poblacion_historica_evaluada)

    candidatos = [ind for ind in poblacion_historica_evaluada if ind["J"] == j_estrella]
    unicos = {tuple(ind["cromosoma"]): ind for ind in candidatos}

    if verbose:
        print(f"J* = {j_estrella}")

    mejores = []
    for i, ind in enumerate(unicos.values(), start=1):
        if verbose:
            print(f"{i}) cromosoma={ind['cromosoma']}  pasos(tau)={ind['tau']}")
        mejores.append({"cromosoma": ind["cromosoma"], "J": ind["J"], "pasos": ind["tau"]})

    return mejores


# Reproduce paso a paso la trayectoria de un cromosoma dado, imprimiéndola si se pide.
def trayectoria_auditada(cromosoma_x, laberinto, posicion_inicial, direccion_inicial, verbose=True):
    datos = ejecutar_individuo(cromosoma_x, laberinto, posicion_inicial, direccion_inicial, None)
    trayectoria = datos["trayectoria"]

    fila_inicial, columna_inicial = trayectoria[0]
    if verbose:
        print(f"paso 0: inicio en (X={columna_inicial}, Y={fila_inicial})")

    reporte = [(0, None, columna_inicial, fila_inicial)]

    for paso, (gen, (fila, columna)) in enumerate(zip(cromosoma_x, trayectoria[1:]), start=1):
        if verbose:
            print(f"paso {paso}: gen={gen} -> (X={columna}, Y={fila})")
        reporte.append((paso, gen, columna, fila))

    return reporte


# Grafica la proporción de soluciones válidas por generación.
def graficar_proporcion_validas(historial_proporcion_validas_por_generacion):
    generaciones = list(range(1, len(historial_proporcion_validas_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_proporcion_validas_por_generacion, marker="o")
    plt.ylim(0, 1)
    plt.xlabel("Generación")
    plt.ylabel("Proporción de soluciones válidas")
    plt.title("Proporción de soluciones válidas por generación")
    plt.grid(True, linestyle="--", alpha=0.5)


# =============================================================================
# BUCLE PRINCIPAL DEL ALGORITMO GENÉTICO
# =============================================================================

# Ejecuta el algoritmo genético completo: inicialización, evolución por generaciones,
# selección, cruzamiento, mutación, elitismo y reporte/gráficas finales.
def algoritmo_genetico(ruta_csv, n, pm, N, G, ps, seed, mostrar_graficos=True, verbose=True):
    fijar_semilla(seed)

    laberinto = cargar_laberinto_csv(ruta_csv)
    posicion_inicial, posicion_llegada = validar_laberinto(laberinto)
    direccion_inicial = "S"

    poblacion_actual = poblacion(N, n)
    evaluados_totales = {}

    mejor_global = None
    historial_mejor_j = []
    historial_prop_validas = []

    for generacion in range(G):
        evaluados_generacion = []

        for individuo in poblacion_actual:
            clave = tuple(individuo)

            if clave not in evaluados_totales:
                evaluados_totales[clave] = reevaluar_descendiente(
                    individuo, laberinto, posicion_inicial, direccion_inicial, posicion_llegada
                )

            evaluados_generacion.append(evaluados_totales[clave])

        evaluados_generacion = ordenar_poblacion(evaluados_generacion)
        mejor_de_la_generacion = evaluados_generacion[0]

        clave_mejor_generacion = (mejor_de_la_generacion["rho"], mejor_de_la_generacion["J"])
        clave_mejor_global = (mejor_global["rho"], mejor_global["J"]) if mejor_global else None

        if mejor_global is None or clave_mejor_generacion < clave_mejor_global:
            mejor_global = mejor_de_la_generacion

        historial_mejor_j.append(mejor_global["J"])
        proporcion_validas = sum(1 for ind in evaluados_generacion if ind["valido"]) / N
        historial_prop_validas.append(proporcion_validas)

        cromosomas_ordenados = [ind["cromosoma"] for ind in evaluados_generacion]
        probabilidades = probabilidades_normalizadas(N, ps)
        ci = distribucion_acumulada(probabilidades)

        descendientes = []
        while len(descendientes) < N - 1:
            padre_1 = seleccionar_padre(cromosomas_ordenados, ci)
            padre_2 = seleccionar_padre(cromosomas_ordenados, ci)

            hijo_1, hijo_2 = cruzamiento_un_punto(padre_1, padre_2)
            hijo_1 = mutacion_por_gen(hijo_1, pm)
            hijo_2 = mutacion_por_gen(hijo_2, pm)

            descendientes.append(hijo_1)
            if len(descendientes) < N - 1:
                descendientes.append(hijo_2)

        poblacion_actual = aplicar_elitismo(mejor_global, descendientes)
        assert len(poblacion_actual) == N, "La población debe mantenerse en tamaño N cada generación."

    if verbose:
        print(f"\nMejor cromosoma global: {mejor_global['cromosoma']}")
        print(f"J={mejor_global['J']}  válido={mejor_global['valido']}  "
              f"D={mejor_global['distancia']}  tau={mejor_global['tau']}")

    mejores_unicos = listar_mejores_cromosomas_unicos(
        list(evaluados_totales.values()), verbose=verbose
    )

    if verbose:
        for mejor in mejores_unicos:
            print(f"\nTrayectoria auditada de {mejor['cromosoma']} (X=columna, Y=fila):")
            trayectoria_auditada(mejor["cromosoma"], laberinto, posicion_inicial, direccion_inicial, verbose=verbose)

    if mostrar_graficos:
        graficar_mejor_objetivo_log(historial_mejor_j)
        graficar_proporcion_validas(historial_prop_validas)
        plt.show()

    return {
        "mejor_global": mejor_global,
        "mejores_unicos": mejores_unicos,
        "historial_mejor_j": historial_mejor_j,
        "historial_prop_validas": historial_prop_validas,
        "laberinto": laberinto,
        "posicion_inicial": posicion_inicial,
        "posicion_llegada": posicion_llegada,
        "direccion_inicial": direccion_inicial,
    }


if __name__ == "__main__":
    ruta_csv, n, pm, N, G, ps, seed = leer_parametros()
    algoritmo_genetico(ruta_csv, n, pm, N, G, ps, seed)