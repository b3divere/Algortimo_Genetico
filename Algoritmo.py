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

# ---------------------------------------------------------------------------
# Lectura y Paramatros del laberinto
# ---------------------------------------------------------------------------

laberinto = []
with open("laberinto_valido.csv", "r", encoding="utf-8") as archivo:
    lector = csv.reader(archivo, delimiter=",")

    for fila in lector:
        laberinto.append(fila)

# ---------------------------------------------------------------------------
# 2. Representación del individuo y ejecución del cromosoma
# ---------------------------------------------------------------------------

def cromosoma(longitud):
    # H gira 90◦ en sentido horario
    #A gira 90◦ en sentido antihorario
    # M avanza un cuadro en la dirección hacia la cual está mirando
    # Q permanece quieto y conserva posición y dirección
    return  choices(A, k=longitud)

def poblacion(N, n):
    if N % 2 == 0 or  N < 3:
        print("El tamaño de la poblacion debe ser impar y >= 3")
    else:
        return [cromosoma(n) for _ in range(N)]
        
def es_transitable(posicion_tentativa, tamaño, fila_laberinto):
    result = None
    if posicion_tentativa <= tamaño and fila_laberinto[posicion_tentativa] != "x":
        result = True
    else:
        result = False
    return result


def penalizacion_pausa(contador_pausas):
        return contador_pausas * 30
        
        

def penalizacion_choques(contador_choques):
    contador_choques =+ 30
    return contador_choques
    

    

def es_valida():
    pass

def llegada_efectiva():
    pass


# la direccion tiene que ser una tupla que supe la posicion actual con cualquiera de los vectores
#individuo = tipo : ["M", "H", "M", "Q"]
#laberinto = tipo matriz
#posicion_inicial = tipo (3,1)
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
    contador_choques =  0
    penalizacionP = 0
    antihorario = ["N", "O", "S", "E"]
    horario = ["N", "E", "S", "O"]
    
    
    
    #for paso, movimiento in enumerate(individuo, start=1):
    for movimiento in individuo:
        
        if movimiento == "M":
            vector_direccion= VECTORES[direccion]
            posicion_tentativa = (posicion[0] + vector_direccion[0] , posicion[1] + vector_direccion[1] )
            
            if es_transitable(posicion_tentativa, tamaño_laberinto, fila_laberinto):
                posicion = posicion_tentativa
                
                contador_pausas = 0
                if contador_giros > 0:
                    bloques_giros.append(contador_giros)
                contador_giros = 0
            else:
                    contador_choques +=1
   
        
            
        elif movimiento == "A": 
            indice = antihorario.index(direccion)
            nuevo_indice = (indice + 1) % len(antihorario)
            direccion = antihorario[nuevo_indice]
            contador_giros +=1
            
            
        elif movimiento == "H":
            indice = horario.index(direccion)
            nuevo_indice = (indice + 1) % len(horario)
            direccion = horario[nuevo_indice]
            contador_giros +=1

        elif movimiento == "Q": 
            if contador_pausas > 1:
                penalizacionQ = penalizacion_pausa(contador_pausas)
            else:
                if es_valida():
                    contador_pausas += 2
            pass      
    
    if contador_giros > 0:
        bloques_giros.append(contador_giros)
        
    
    return direccion, posicion, contador_choques
        


def inicio(laberinto, poblacion, movimiento, direccion_inicial):
    pass
        
    
    
                

                
            
    

