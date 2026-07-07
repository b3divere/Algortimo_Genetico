from random import choices, randint, random, randrange
from typing import Callable, List, NamedTuple, Tuple
from functools import partial
from time import time
import csv

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
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

def leer_parametros():
    # Debe leer externamente ruta del CSV, n, pm, N, G, ps y seed (sin hardcodear).
    pass

# =============================================================================
# ETAPA 1: LECTURA, PARÁMETROS Y VALIDACIÓN DEL LABERINTO (5%)
# =============================================================================

def cargar_laberinto_csv(ruta_csv):
    # Lee el CSV recibido por parámetro (ruta_csv) y retorna la matriz del laberinto.
    # (Misma lógica del borrador anterior, pero usando el parámetro ruta_csv en vez
    # de un nombre de archivo fijo a nivel de módulo, para no depender de una ruta
    # rígida como exige la pauta).
    laberinto = []

    with open(ruta_csv, "r", encoding="utf-8") as archivo:
        lector = csv.reader(archivo, delimiter=",")

        for fila in lector:
            laberinto.append(fila)

    return laberinto

def validar_simbolos(laberinto):
    # Debe validar que cada celda contenga solo "0", "1", "2" o "X".
    pass


def encontrar_salida(laberinto):
    # Debe ubicar la única celda "1" y validar que esté en la primera fila interior.
    pass


def encontrar_llegada(laberinto):
    # Debe ubicar la única celda "2" y validar que esté en la última fila interior.
    pass


def validar_muros_perimetrales(laberinto):
    # Debe validar que todo el borde externo del laberinto sea muro "X".
    pass


def validar_zona_despejada(laberinto, posicion):
    # Debe validar que el vecindario de Moore interior de la posición no tenga muros.
    pass


def validar_laberinto(laberinto):
    # Debe orquestar todas las validaciones del laberinto (símbolos, muros, salida/llegada, zonas despejadas).
    pass


# =============================================================================
# ETAPA 2: REPRESENTACIÓN DEL INDIVIDUO Y EJECUCIÓN DEL CROMOSOMA (5%)
# =============================================================================

def cromosoma(longitud):
    # H gira 90◦ en sentido horario
    # A gira 90◦ en sentido antihorario
    # M avanza un cuadro en la dirección hacia la cual está mirando
    # Q permanece quieto y conserva posición y dirección

    return choices(A, k=longitud)

def poblacion(N, n):
    if N % 2 == 0 or N < 3:
        print("El tamaño de la poblacion debe ser impar y >= 3")
    else:
        return [cromosoma(n) for _ in range(N)]

def es_transitable(posicion_tentativa, tamaño, fila_laberinto):
    # OJO: posicion_tentativa es una tupla (fila, columna); compararla con "<=" contra
    # un entero (tamaño) y usarla como índice de una sola fila_laberinto no es compatible
    # con una matriz m x r, y falla en Python 3 al comparar tupla con int.
    result = None
    if posicion_tentativa <= tamaño and fila_laberinto[posicion_tentativa] != "x":
        result = True
    else:
        result = False
    return result

def fitness(individuo, datos_simulacion, pos_meta):
    n = len(individuo)

    pos_final = datos_simulacion["posicion_final"]
    distancia_D = abs(pos_final[0] - pos_meta[0]) + abs(pos_final[1] - pos_meta[1])

    es_valido = False
    tiempo_llegada = n + 1
    
    if datos_simulacion["pasos_en_meta"]:
        primer_paso_meta = datos_simulacion["pasos_en_meta"][0]
        tiempo_llegada = primer_paso_meta
        
        genes_despues_de_llegar = individuo[primer_paso_meta:]
        if all(gen == "Q" for gen in genes_despues_de_llegar):
            es_valido = True

    # --------------------------------------------------
    # Penalizaciones
    # --------------------------------------------------
    # Castogo por choques
    PC = 30 * datos_simulacion["choques"]
    
    # Castigo por acciones en meta
    PA = 100 * datos_simulacion["acciones_en_meta"]
    
    # Camino invalido
    P_inv = 0 if es_valido else 10000
    
    # --------------------------------------------------
    # Calculo de J y Fitness
    # --------------------------------------------------
    J = distancia_D + tiempo_llegada + PC + PA + P_inv
    
    fitness = -J
    
    return {
        "fitness": fitness,
        "J": J,
        "valido": es_valido,
        "distancia_manhattan": distancia_D,
        "tiempo_llegada": tiempo_llegada
    }

# la direccion tiene que ser una tupla que supe la posicion actual con cualquiera de los vectores
# individuo = tipo : ["M", "H", "M", "Q"]
# laberinto = tipo matriz
# posicion_inicial = tipo (3,1)
# direccion inicial = tipo "s"

def ejecutar_individuo(
    individuo,
    posicion_actual,
    direccion_actual,
    tamaño_laberinto,
    fila_laberinto
):

    direccion = direccion_actual
    posicion = posicion_actual
    direccion_anterior = None

    bloques_giros = []
    contador_giros = 0
    contador_pausas = 0
    contador_choques = 0
    penalizacionP = 0
    antihorario = ["N", "O", "S", "E"]
    horario = ["N", "E", "S", "O"]

    # for paso, movimiento in enumerate(individuo, start=1):
    for movimiento in individuo:

        if movimiento == "M":
            vector_direccion = VECTORES[direccion]
            posicion_tentativa = (posicion[0] + vector_direccion[0], posicion[1] + vector_direccion[1])

            if es_transitable(posicion_tentativa, tamaño_laberinto, fila_laberinto):
                posicion = posicion_tentativa

                contador_pausas = 0
                if contador_giros > 0:
                    bloques_giros.append(contador_giros)
                contador_giros = 0
            else:
                contador_choques += 1

        elif movimiento == "A":
            indice = antihorario.index(direccion)
            nuevo_indice = (indice + 1) % len(antihorario)
            direccion = antihorario[nuevo_indice]
            contador_giros += 1

        elif movimiento == "H":
            indice = horario.index(direccion)
            nuevo_indice = (indice + 1) % len(horario)
            direccion = horario[nuevo_indice]
            contador_giros += 1

        elif movimiento == "Q":
            # OJO: aquí se está calculando validez/penalidad (es_valida, penalizacion_pausa)
            # DENTRO de la ejecución del cromosoma. Eso mezcla la Etapa 2 (mecánica de
            # movimiento) con la Etapa 3 (validez y penalidades), que la pauta trata por
            # separado; además contador_pausas nunca se usa fuera de esta rama.
            if contador_pausas > 1:
                penalizacionQ = penalizacion_pausa(contador_pausas)
            else:
                if es_valida():
                    contador_pausas += 2
            pass

    if contador_giros > 0:
        bloques_giros.append(contador_giros)

    return direccion, posicion, contador_choques

# =============================================================================
# ETAPA 3: FUNCIÓN OBJETIVO, VALIDEZ Y PENALIDADES (15%)
# =============================================================================

def llegada_efectiva(trayectoria, posicion_llegada):
    # Debe construir Tz(x): pasos en que el individuo entra a la meta desde otra celda.
    pass


def ultima_llegada_efectiva(conjunto_tz):
    # Debe retornar ℓ(x) = max(Tz(x)), o None si Tz(x) es vacío.
    # (Se mantiene separada de llegada_efectiva() a propósito: la pauta pide
    # poder explicar Tz(x) y ℓ(x) como cantidades distintas en la oral, aunque
    # técnicamente ℓ(x) sea solo un max() sobre el resultado de la anterior).
    pass


def tau(individuo, conjunto_tz, ultima_llegada):
    # Debe calcular τ(x): ℓ(x) si hay detención válida tras la última llegada, si no n+1.
    pass


def es_valida(individuo, conjunto_tz, tau_valor, n):
    # Debe determinar si el cromosoma llegó a la meta y se detuvo válidamente (solo Q después).
    pass


def penalizacion_pausa(contador_pausas):
    # OJO: la pauta define PQ(x) = 10*Qint(x), pero aquí se retorna contador_pausas*30
    # (30 en vez de 10, y usa un contador que se resetea dentro de ejecutar_individuo
    # en vez de contarse directamente sobre la secuencia de genes del cromosoma).
    return contador_pausas * 30


def penalizacion_choques(contador_choques):
    # Debe calcular PC(x) = 30 * C(x).
    # (Se deja como stub: la versión anterior "contador_choques =+ 30" no acumula
    # correctamente -es asignación, no incremento- y no multiplica por 30 por choque).
    pass


def f_bloque(b):
    # Debe calcular f(b): 0 si b<=1, 10 si b=2, 30 si b=3, 120*(b-3) si b>=4.
    pass

# =============================================================================
# ETAPA 4: SELECCIÓN POR RANKING GEOMÉTRICO Y ELITISMO (8%)
# =============================================================================

def rho(individuo_es_valido, llego_alguna_vez):
    # Debe calcular ρ(x): 0 si válido, 1 si llegó pero no válido, 2 si nunca llegó.
    if individuo_es_valido:
        return 0
    elif llego_alguna_vez:
        return 1
    else:
        return 2

def ordenar_poblacion(poblacion_evaluada):
    # Debe ordenar la población lexicográficamente por (ρ(x), J(x), D(x), τ(x)).
    poblacion_evaluada.sort(key=lambda ind: (ind["rho"], ind["J"], ind["distancia"], ind["tau"]))
    return poblacion_evaluada

def probabilidades_normalizadas(N, ps):
    # Debe calcular, en un solo paso, los pesos no normalizados wi = ps*(1-ps)^(i-1)
    # y luego normalizarlos: Pi = wi / (1-(1-ps)^N) para cada posición i=1..N.
    # (Se fusiona aquí lo que antes era pesos_ranking_geometrico(): wi nunca se usa
    # ni se reporta por separado, es solo un paso intermedio hacia Pi).
    probabilidades = []
    
    denominador = 1 - 1(1 - ps)**N
    
    for i in range(1, N +1):
        pi = (ps * (1 - ps)**(i - 1)) / denominador
        probabilidades.append(pi)

def distribucion_acumulada(probabilidades):
    # Debe calcular Ci = suma acumulada de P1..Pi.
    ci = []
    suma_actual = 0
    
    for p in probabilidades:
        suma_actual += p
        ci.append(suma_actual)
    return ci

def seleccionar_padre(poblacion_ordenada, distribucion_acumulada_ci):
    # Debe generar u~U(0,1) y elegir el primer cromosoma con u <= Ci.
    u = random.random()
    
    for i in range(len(distribucion_acumulada_ci)):
        if u <= distribucion_acumulada_ci[i]:
            return poblacion_ordenada[i]

def aplicar_elitismo(mejor_global, descendientes):
    # Debe construir P_{t+1} = {x*_t} ∪ Ot, conservando el mejor global.
    nueva_poblacion = [mejor_global["cromosoma"]]
    
    for hijo in descendientes:
        nueva_poblacion.append(hijo)
        
    return nueva_poblacion

# =============================================================================
# ETAPA 5: CRUZAMIENTO, MUTACIÓN POR GEN Y REEVALUACIÓN (12%)
# =============================================================================

def cruzamiento_un_punto(padre_x, padre_y):
    # Debe elegir un punto de corte c y generar dos descendientes combinando ambos padres.
    pass


def mutar_gen(gen_actual):
    # Debe reemplazar el gen actual por una acción distinta tomada de A \ {gen_actual}.
    pass


def mutacion_por_gen(descendiente, pm):
    # Debe mutar cada gen del descendiente con probabilidad pm usando mutar_gen().
    pass


def reevaluar_descendiente(descendiente, laberinto, posicion_inicial, direccion_inicial):
    # Debe llamar a ejecutar_individuo() para obtener la trayectoria desde cero,
    # y luego usar las funciones de Etapa 3 sobre ese resultado para recalcular J(x) y ϕ(x).
    # (No debe reimplementar la simulación del laberinto aquí).
    pass


# =============================================================================
# ETAPA 6: RESULTADOS MÍNIMOS Y GRÁFICAS (5%)
# =============================================================================

def graficar_mejor_objetivo_log(historial_mejor_j_por_generacion):
    # Debe graficar el mejor J(x) global por generación en escala logarítmica.
    pass


def listar_mejores_cromosomas_unicos(poblacion_historica_evaluada):
    # Debe listar los cromosomas únicos que empatan en el mejor J* y sus pasos.
    pass


def trayectoria_auditada(cromosoma_x, laberinto, posicion_inicial, direccion_inicial):
    # Debe llamar a ejecutar_individuo() para obtener la trayectoria y reportarla
    # paso a paso en coordenadas (X, Y): X = columna, Y = fila, según pide la pauta.
    # (No debe reimplementar la simulación del laberinto aquí).
    pass


def graficar_proporcion_validas(historial_proporcion_validas_por_generacion):
    # Debe graficar la proporción de soluciones válidas por generación.
    pass


# =============================================================================
# BUCLE PRINCIPAL DEL ALGORITMO GENÉTICO
# =============================================================================

def algoritmo_genetico(ruta_csv, n, pm, N, G, ps, seed):
    # Debe orquestar todo el ciclo evolutivo: carga, validación, evaluación, selección,
    # cruzamiento, mutación, elitismo y reporte de resultados durante G generaciones.
    # (Punto de entrada único: se elimina inicio(), que era un duplicado de esta función).
    pass


if __name__ == "__main__":
    algoritmo_genetico(
        ruta_csv="laberinto_valido.csv",
        n=None,      # TODO: definir según parámetros de la actividad
        pm=None,
        N=None,
        G=None,
        ps=None,
        seed=None
    )