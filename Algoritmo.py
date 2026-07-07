from random import choices,choice, randint, random, randrange
from typing import Callable, List, NamedTuple, Tuple
from functools import partial
from time import time
import csv
import matplotlib.pyplot as plt

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

def leer_parametros(ruta_csav, n, pm, N, G, ps, seed):
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

def validar_simbolos(laberinto): pass
def encontrar_salida(laberinto): pass
def encontrar_llegada(laberinto): pass
def validar_muros_perimetrales(laberinto): pass
def validar_zona_despejada(laberinto, posicion): pass
def validar_laberinto(laberinto): pass

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
        raise ValueError("El tamaño de la poblacion debe ser impar y >= 3")
    
    return [cromosoma(n) for _ in range(N)]

def es_transitable(laberinto, pos):
    # OJO: posicion_tentativa es una tupla (fila, columna); compararla con "<=" contra
    # un entero (tamaño) y usarla como índice de una sola fila_laberinto no es compatible
    # con una matriz m x r, y falla en Python 3 al comparar tupla con int.
    fila, columna = pos
    
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])
    
    if fila < 0 or fila >= total_filas:
        return False
    if columna < 0 or columna >= total_columnas:
        return False
    
    return laberinto[fila][columna] != "X"

# la direccion tiene que ser una tupla que supe la posicion actual con cualquiera de los vectores
# individuo = tipo : ["M", "H", "M", "Q"]
# laberinto = tipo matriz
# posicion_inicial = tipo (3,1)
# direccion inicial = tipo "s"

def ejecutar_individuo(individuo, laberinto, posicion_inicial, direccion_inicial, posicion_llegada):
    """Simula el movimiento del individuo y retorna los datos puros para evaluar luego."""
    direccion = direccion_inicial
    posicion = posicion_inicial
    
    trayectoria = [posicion]
    choques = 0
    bloques_giros = []
    contador_giros = 0
    acciones_en_meta = 0

    for gen in individuo:
        pos_anterior = posicion
        
        # Revisamos si hace acciones estando ya en la meta
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
            pass # Q no hace nada

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

def distancia_manhattan(posicion_final, posicion_llegada):
    return abs(posicion_final[0] - posicion_llegada[0]) + abs(posicion_final[1] - posicion_llegada[1])

def llegada_efectiva(trayectoria, posicion_llegada):
    # Tz(x) = { t : p_{t-1} != z  y  p_t == z }
    # trayectoria es la lista de posiciones p_0, p_1, ..., p_n
    # (p_0 es la posición inicial, antes de ejecutar cualquier gen)
    tz = []

    for t in range(1, len(trayectoria)):
        posicion_anterior = trayectoria[t - 1]
        posicion_actual = trayectoria[t]

        if posicion_anterior != posicion_llegada and posicion_actual == posicion_llegada:
            tz.append(t)

    return tz

def ultima_llegada_efectiva(conjunto_tz):
    # ℓ(x) = max(Tz(x)), o None si nunca llegó
    if len(conjunto_tz) == 0:
        return None
    return max(conjunto_tz)

def tau(individuo, conjunto_tz, ultima_llegada):
    n = len(individuo)

    # Si Tz(x) = ∅ (nunca llegó), no hay tau válido
    if len(conjunto_tz) == 0:
        return n + 1

    # La llegada no puede ser en el último gen (debe haber al menos un Q después)
    if ultima_llegada >= n:
        return n + 1

    # Todos los genes después de la última llegada deben ser Q
    genes_despues = individuo[ultima_llegada:]  # ultima_llegada es 1-indexado (t),

    todos_son_q = all(gen == "Q" for gen in genes_despues)

    if todos_son_q:
        return ultima_llegada
    else:
        return n + 1

def es_valida(conjunto_tz, tau_valor, n):
    # Debe determinar si el cromosoma llegó a la meta y se detuvo válidamente (solo Q después).
    return len(conjunto_tz) > 0 and tau_valor <= n

# =============================================================================
# PENALIZACIONES
# =============================================================================

def penalizacion_pausa(individuo):
    # OJO: la pauta define PQ(x) = 10*Qint(x), pero aquí se retorna contador_pausas*30
    # (30 en vez de 10, y usa un contador que se resetea dentro de ejecutar_individuo
    # en vez de contarse directamente sobre la secuencia de genes del cromosoma).
    ultimo_activo = -1
    for k, gen in enumerate(individuo):
        if gen != "Q":
            ultimo_activo = k
            
    if ultimo_activo == -1:
        return 0
        
    pausas_interiores = sum(1 for k in range(ultimo_activo) if individuo[k] == "Q")
    return pausas_interiores * 10


def penalizacion_choques(contador_choques):
    # Debe calcular PC(x) = 30 * C(x).
    # (Se deja como stub: la versión anterior "contador_choques =+ 30" no acumula
    # correctamente -es asignación, no incremento- y no multiplica por 30 por choque).
    return contador_choques * 30


def f_bloque(b):
    # Debe calcular f(b): 0 si b<=1, 10 si b=2, 30 si b=3, 120*(b-3) si b>=4.
    if b <= 1: return 0
    if b == 2: return 10
    if b == 3: return 30
    return 120 * (b - 3)

def penalizacion_bloques_giros(lista_bloques_giros):
    return sum(f_bloque(b) for b in lista_bloques_giros)

def penalizacion_post_meta(acciones_activas_post_meta):
    return acciones_activas_post_meta * 100

def penalizacion_detencion_prematura(individuo, individuo_es_valido):
    if individuo_es_valido: return 0
    
    ultimo_activo = -1
    for k, gen in enumerate(individuo):
        if gen != "Q":
            ultimo_activo = k
            
    q_prematuras = len(individuo) - (ultimo_activo + 1)
    return q_prematuras * 10

def penalizacion_invalidez(individuo_es_valido):
    return 0 if individuo_es_valido else 10000

def funcion_objetivo(distancia, tau_valor, pq, pc, pr, pa, pprem, pinv):
    return distancia + tau_valor + pq + pc + pr + pa + pprem + pinv

def calcular_fitness(j_valor):
    return -j_valor

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
    
    denominador = 1 - (1 - ps)**N
    
    for i in range(1, N +1):
        pi = (ps * (1 - ps)**(i - 1)) / denominador
        probabilidades.append(pi)
    
    return probabilidades

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
    u = random()
    
    for i in range(len(distribucion_acumulada_ci)):
        if u <= distribucion_acumulada_ci[i]:
            return poblacion_ordenada[i]
    
    return poblacion_ordenada[-1]

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
    n = len(padre_x)

    if len(padre_y) != n:
        raise ValueError("Los padres deben tener la misma longitud.")

    if n < 2:
        raise ValueError("La longitud del cromosoma debe ser al menos 2 para aplicar cruzamiento.")

    punto_corte = randint(1, n - 1)

    descendiente_1 = padre_x[:punto_corte] + padre_y[punto_corte:]
    descendiente_2 = padre_y[:punto_corte] + padre_x[punto_corte:]

    return descendiente_1, descendiente_2

def mutar_gen(gen_actual):
    # Tomo todas las acciones posibles: H, A, M, Q
    # Le quito la acción actual, para no repetirla
    # Elijo una al azar entre las que quedan
    opciones = []
    for accion in A:
        if accion != gen_actual:
            opciones.append(accion)

    return choice(opciones)

def mutacion_por_gen(descendiente, pm):
    # Copio el cromosoma para no modificar el original
    nuevo = list(descendiente)

    # Recorro cada gen, uno por uno
    for i in range(len(nuevo)):
        # Tiro un número al azar entre 0 y 1
        numero_al_azar = random()

        # Si el número es menor que pm, ese gen muta
        if numero_al_azar < pm:
            nuevo[i] = mutar_gen(nuevo[i])

    return nuevo


def reevaluar_descendiente(descendiente, laberinto, posicion_inicial, direccion_inicial, posicion_llegada):
    # Debe llamar a ejecutar_individuo() para obtener la trayectoria desde cero,
    # y luego usar las funciones de Etapa 3 sobre ese resultado para recalcular J(x) y ϕ(x).
    # (No debe reimplementar la simulación del laberinto aquí).
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

def graficar_mejor_objetivo_log(historial_mejor_j_por_generacion):
    # historial_mejor_j_por_generacion: lista con el mejor J(x) global conocido
    # hasta cada generación (un valor por generación, ya monótono no creciente
    # gracias al elitismo).
    generaciones = list(range(1, len(historial_mejor_j_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_mejor_j_por_generacion, marker="o")
    plt.yscale("log")
    plt.xlabel("Generación")
    plt.ylabel("Mejor J(x) global (escala log)")
    plt.title("Evolución del mejor valor de función objetivo")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.show()


def listar_mejores_cromosomas_unicos(poblacion_historica_evaluada):
    if not poblacion_historica_evaluada:
        print("No hay individuos evaluados.")
        return []

    j_estrella = min(ind["J"] for ind in poblacion_historica_evaluada)

    # Nos quedamos solo con los individuos que empatan en J*, y usamos un dict
    # (indexado por el cromosoma como tupla) para eliminar duplicados: si el mismo
    # cromosoma aparece varias veces, solo queda una entrada.
    candidatos = [ind for ind in poblacion_historica_evaluada if ind["J"] == j_estrella]
    unicos = {tuple(ind["cromosoma"]): ind for ind in candidatos}

    print(f"J* = {j_estrella}")
    mejores = []
    for i, ind in enumerate(unicos.values(), start=1):
        print(f"{i}) cromosoma={ind['cromosoma']}  pasos(tau)={ind['tau']}")
        mejores.append({"cromosoma": ind["cromosoma"], "J": ind["J"], "pasos": ind["tau"]})

    return mejores


def trayectoria_auditada(cromosoma_x, laberinto, posicion_inicial, direccion_inicial):
    # Reutiliza ejecutar_individuo() para obtener la trayectoria; posicion_llegada=None
    # porque aqui solo interesan las posiciones recorridas, no las penalidades de meta.
    datos = ejecutar_individuo(cromosoma_x, laberinto, posicion_inicial, direccion_inicial, None)
    trayectoria = datos["trayectoria"]

    # trayectoria[0] es la posicion inicial, antes de ejecutar cualquier gen.
    fila_inicial, columna_inicial = trayectoria[0]
    print(f"paso 0: inicio en (X={columna_inicial}, Y={fila_inicial})")

    reporte = [(0, None, columna_inicial, fila_inicial)]

    # cromosoma_x[k] es el gen que produjo trayectoria[k + 1], por eso emparejamos
    # los genes con la trayectoria "corrida" un paso (trayectoria[1:]).
    for paso, (gen, (fila, columna)) in enumerate(zip(cromosoma_x, trayectoria[1:]), start=1):
        print(f"paso {paso}: gen={gen} -> (X={columna}, Y={fila})")
        reporte.append((paso, gen, columna, fila))

    return reporte


def graficar_proporcion_validas(historial_proporcion_validas_por_generacion):
    # historial_proporcion_validas_por_generacion: lista con la fracción
    # (entre 0 y 1) de cromosomas válidos en cada generación.
    generaciones = list(range(1, len(historial_proporcion_validas_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_proporcion_validas_por_generacion, marker="o")
    plt.ylim(0, 1)
    plt.xlabel("Generación")
    plt.ylabel("Proporción de soluciones válidas")
    plt.title("Proporción de soluciones válidas por generación")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()


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