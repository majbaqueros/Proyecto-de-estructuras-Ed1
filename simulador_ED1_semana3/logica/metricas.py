"""Instrumentación de rendimiento en el lado Python, separada de Flet."""
from collections import deque
from dataclasses import dataclass
from sys import getsizeof
from time import perf_counter, monotonic
from estructuras.lista_doblemente import DoublyLinkedList, Nodo
from estructuras.lista_circular_doble import NodoCircular, ListaDoblementeCircular
from estructuras.pila import NodoPila
from estructuras.colas import NodoCola


class MonitorRendimiento:
    def __init__(self, ventana_s=5.0):
        self.ventana_s = ventana_s
        self._instantes = deque()
        self.operaciones = 0
        self.ultima_duracion_ms = 0.0
        self.duracion_acumulada_ms = 0.0

    def registrar(self, duracion_s):
        ahora = monotonic()
        self._instantes.append(ahora)
        self.operaciones += 1
        self.ultima_duracion_ms = duracion_s * 1000
        self.duracion_acumulada_ms += self.ultima_duracion_ms
        self._depurar(ahora)

    def _depurar(self, ahora):
        limite = ahora - self.ventana_s
        while self._instantes and self._instantes[0] < limite:
            self._instantes.popleft()

    def ops_por_segundo(self):
        ahora = monotonic()
        self._depurar(ahora)
        # Promedio de la ventana completa para evitar infinitos al arrancar.
        return len(self._instantes) / self.ventana_s

    def resumen(self):
        return {
            "operaciones": self.operaciones,
            "ops_segundo": self.ops_por_segundo(),
            "ultima_ms": self.ultima_duracion_ms,
            "promedio_ms": self.duracion_acumulada_ms / self.operaciones if self.operaciones else 0,
        }


def estimar_memoria_nodos(cantidad=100):
    """Estimación CPython: objetos nodo+datos de ejemplo; no mide memoria de Flutter ni heap total."""
    cantidad = max(0, int(cantidad))
    # No se usa como almacenamiento de la estructura, sólo se contabiliza un nodo prototipo.
    ejemplos = {
        "Doble": Nodo(0),
        "Circular doble": NodoCircular(0),
        "Pila": NodoPila(0),
        "Cola circular": NodoCola(0),
    }
    resultados = {}
    for nombre, nodo in ejemplos.items():
        tamaño = getsizeof(nodo) + getsizeof(nodo.dato)
        resultados[nombre] = {"bytes_nodo": tamaño, "bytes_total": tamaño * cantidad}
    return resultados


@dataclass(frozen=True)
class ResultadoBenchmark:
    cantidad: int
    append_ms: float
    buscar_ms: float
    ratio: float


def ejecutar_benchmark(cantidad=2000):
    """Compara N inserciones O(1) vs N búsquedas O(n), sin modificar datos del usuario.

    Se mide el tiempo total: cada búsqueda recorre una lista de N nodos.
    El resultado no es una prueba matemática de complejidad y varía por máquina.
    """
    cantidad = max(10, min(int(cantidad), 10000))
    estructura = DoublyLinkedList()
    inicio = perf_counter()
    for i in range(cantidad):
        estructura.insertar_final(i)
    append_ms = (perf_counter() - inicio) * 1000
    inicio = perf_counter()
    for _ in range(cantidad):
        estructura.eliminar(-1)  # ausencia: búsqueda completa O(n)
    buscar_ms = (perf_counter() - inicio) * 1000
    return ResultadoBenchmark(cantidad, append_ms, buscar_ms, buscar_ms / max(append_ms, 1e-9))
