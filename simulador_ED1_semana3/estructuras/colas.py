"""Colas enlazadas; no dependen de list de Python para almacenar sus nodos."""
from estructuras.lista_doblemente import Nodo


class PriorityQueue:
    """Menor número = mayor prioridad (1=Alta, 2=Media, 3=Baja).

    La inserción ordenada es O(n); desencolar es O(1).
    En prioridades iguales se conserva el orden de llegada.
    """

    def __init__(self):
        self.cabeza = None
        self._tamaño = 0

    def encolar(self, dato, prioridad):
        nuevo = Nodo((dato, prioridad))
        if not self.cabeza or prioridad < self.cabeza.dato[1]:
            nuevo.next = self.cabeza
            self.cabeza = nuevo
        else:
            actual = self.cabeza
            while actual.next and actual.next.dato[1] <= prioridad:
                actual = actual.next
            nuevo.next = actual.next
            actual.next = nuevo
        self._tamaño += 1

    def desencolar(self):
        if not self.cabeza:
            return None
        dato = self.cabeza.dato
        self.cabeza = self.cabeza.next
        self._tamaño -= 1
        return dato

    def eliminar_dato(self, dato):
        """Retira el primer elemento con identidad de objeto igual (para undo). O(n)."""
        anterior = None
        actual = self.cabeza
        while actual:
            if actual.dato[0] is dato:
                if anterior:
                    anterior.next = actual.next
                else:
                    self.cabeza = actual.next
                self._tamaño -= 1
                return True
            anterior, actual = actual, actual.next
        return False


class NodoCola:
    __slots__ = ("dato", "next")

    def __init__(self, dato):
        self.dato = dato
        self.next = None


class CircularQueue:
    """Cola FIFO de capacidad finita enlazada circularmente. O(1) en ambos extremos."""

    def __init__(self, capacidad):
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser positiva")
        self.capacidad = capacidad
        self.frente = None
        self.final = None
        self._tamaño = 0

    def encolar(self, dato):
        if self._tamaño == self.capacidad:
            raise OverflowError("Cola llena")
        nuevo = NodoCola(dato)
        if self.frente is None:
            self.frente = self.final = nuevo
            nuevo.next = nuevo
        else:
            nuevo.next = self.frente
            self.final.next = nuevo
            self.final = nuevo
        self._tamaño += 1

    def desencolar(self):
        if self._tamaño == 0:
            return None
        dato = self.frente.dato
        if self._tamaño == 1:
            self.frente = self.final = None
        else:
            self.frente = self.frente.next
            self.final.next = self.frente
        self._tamaño -= 1
        return dato
