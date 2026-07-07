from random import choices, choice, randint, random, randrange, seed as fijar_semilla
from typing import Callable, List, NamedTuple, Tuple
from functools import partial
from time import time
import csv
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

def leer_parametros():
    # Lee externamente ruta del CSV, n, pm, N, G, ps y seed usando argparse.
    # Los valores quedan definidos aca (como default), no repartidos ni
    # fijados rigidamente en la logica principal (__main__). Si se pasan
    # por linea de comandos, estos defaults se sobrescriben.
    parser = argparse.ArgumentParser(
        description="Algoritmo genetico para la resolucion de laberintos (INFO-1159)"
    )
    parser.add_argument("--csv", type=str, default="laberinto_valido.csv",
                         help="Ruta del archivo CSV del laberinto")
    parser.add_argument("--n", type=int, default=15,
                         help="Longitud del cromosoma")
    parser.add_argument("--pm", type=float, default=0.15,
                         help="Probabilidad de mutacion por gen")
    parser.add_argument("--N", type=int, default=21,
                         help="Numero de cromosomas por generacion (debe ser impar)")
    parser.add_argument("--G", type=int, default=300,
                         help="Numero total de generaciones")
    parser.add_argument("--ps", type=float, default=0.3,
                         help="Presion selectiva (ranking geometrico)")
    parser.add_argument("--seed", type=int, default=7,
                         help="Semilla aleatoria para reproducibilidad")

    argumentos = parser.parse_args()

    return (
        argumentos.csv,
        argumentos.n,
        argumentos.pm,
        argumentos.N,
        argumentos.G,
        argumentos.ps,
        argumentos.seed,
    )

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
    simbolos_validos = {"0","1","2","X"}
    
    for i, fila in enumerate(laberinto):
        for j, celda in enumerate(fila):
            if celda not in simbolos_validos:
                raise ValueError(f"Simbolo invalido '{celda}' en la posicion ({i},{j})")

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

def validar_muros_perimetrales(laberinto):
    total_filas = len(laberinto)
    total_columnas = len(laberinto[0])
 
    for i in range(total_filas):
        for j in range(total_columnas):
            en_el_perimetro = i == 0 or i == total_filas - 1 or j == 0 or j == total_columnas - 1
            
            if en_el_perimetro and laberinto[i][j] != "X":
                raise ValueError(f"El perimetro debe ser todo muro; falla en la posicion ({i},{j}).")

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
 
    # Salida en la primera fila interior (fila 2 en indexacion 1 -> fila 1 en indexacion 0).
    if posicion_salida[0] != 1:
        raise ValueError("La salida debe estar en la primera fila interior válida (fila 2, indexacion 1).")
 
    # Llegada en la ultima fila interior (fila m-1 en indexacion 1 -> fila m-2 en indexacion 0).
    if posicion_llegada[0] != total_filas - 2:
        raise ValueError("La llegada debe estar en la última fila interior válida (fila m-1, indexacion 1).")
 
    validar_zona_despejada(laberinto, posicion_salida)
    validar_zona_despejada(laberinto, posicion_llegada)
 
    return posicion_salida, posicion_llegada

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
    generaciones = list(range(1, len(historial_mejor_j_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_mejor_j_por_generacion, marker="o")
    plt.yscale("log")
    plt.xlabel("Generación")
    plt.ylabel("Mejor J(x) global (escala log)")
    plt.title("Evolución del mejor valor de función objetivo")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    # No se llama a plt.show() aca: se muestran todas las figuras juntas
    # al final, en algoritmo_genetico(), para que ambas queden visibles
    # al mismo tiempo en vez de bloquear una ventana a la vez.


def listar_mejores_cromosomas_unicos(poblacion_historica_evaluada):
    if not poblacion_historica_evaluada:
        print("No hay individuos evaluados.")
        return []

    j_estrella = min(ind["J"] for ind in poblacion_historica_evaluada)

    candidatos = [ind for ind in poblacion_historica_evaluada if ind["J"] == j_estrella]
    unicos = {tuple(ind["cromosoma"]): ind for ind in candidatos}

    print(f"J* = {j_estrella}")
    mejores = []
    for i, ind in enumerate(unicos.values(), start=1):
        print(f"{i}) cromosoma={ind['cromosoma']}  pasos(tau)={ind['tau']}")
        mejores.append({"cromosoma": ind["cromosoma"], "J": ind["J"], "pasos": ind["tau"]})

    return mejores


def trayectoria_auditada(cromosoma_x, laberinto, posicion_inicial, direccion_inicial):
    datos = ejecutar_individuo(cromosoma_x, laberinto, posicion_inicial, direccion_inicial, None)
    trayectoria = datos["trayectoria"]

    fila_inicial, columna_inicial = trayectoria[0]
    print(f"paso 0: inicio en (X={columna_inicial}, Y={fila_inicial})")

    reporte = [(0, None, columna_inicial, fila_inicial)]

    for paso, (gen, (fila, columna)) in enumerate(zip(cromosoma_x, trayectoria[1:]), start=1):
        print(f"paso {paso}: gen={gen} -> (X={columna}, Y={fila})")
        reporte.append((paso, gen, columna, fila))

    return reporte


def graficar_proporcion_validas(historial_proporcion_validas_por_generacion):
    generaciones = list(range(1, len(historial_proporcion_validas_por_generacion) + 1))

    plt.figure()
    plt.plot(generaciones, historial_proporcion_validas_por_generacion, marker="o")
    plt.ylim(0, 1)
    plt.xlabel("Generación")
    plt.ylabel("Proporción de soluciones válidas")
    plt.title("Proporción de soluciones válidas por generación")
    plt.grid(True, linestyle="--", alpha=0.5)
    # Idem: no se llama a plt.show() aca; se muestran ambas figuras juntas
    # al final del algoritmo.


# =============================================================================
# BUCLE PRINCIPAL DEL ALGORITMO GENÉTICO
# =============================================================================

def algoritmo_genetico(ruta_csv, n, pm, N, G, ps, seed):
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

    print(f"\nMejor cromosoma global: {mejor_global['cromosoma']}")
    print(f"J={mejor_global['J']}  válido={mejor_global['valido']}  "
          f"D={mejor_global['distancia']}  tau={mejor_global['tau']}")

    mejores_unicos = listar_mejores_cromosomas_unicos(list(evaluados_totales.values()))

    for mejor in mejores_unicos:
        print(f"\nTrayectoria auditada de {mejor['cromosoma']} (X=columna, Y=fila):")
        trayectoria_auditada(mejor["cromosoma"], laberinto, posicion_inicial, direccion_inicial)

    graficar_mejor_objetivo_log(historial_mejor_j)
    graficar_proporcion_validas(historial_prop_validas)
    # Un solo plt.show() al final: como ambas figuras ya fueron creadas
    # (plt.figure() en cada funcion), esto las muestra a las dos juntas
    # en vez de bloquear la ejecucion mostrando una a la vez.
    plt.show()

    return {
        "mejor_global": mejor_global,
        "mejores_unicos": mejores_unicos,
        "historial_mejor_j": historial_mejor_j,
        "historial_prop_validas": historial_prop_validas,
    }


if __name__ == "__main__":
    ruta_csv, n, pm, N, G, ps, seed = leer_parametros()
    algoritmo_genetico(ruta_csv, n, pm, N, G, ps, seed)