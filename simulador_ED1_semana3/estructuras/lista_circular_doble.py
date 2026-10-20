class NodoCircular:
    __slots__ = ("dato", "next", "prev")
    def __init__(self, dato):
        self.dato = dato
        self.next = self
        self.prev = self
class ListaDoblementeCircular:
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._tamaño = 0
    def __len__(self):
        return self._tamaño
    def insertar_final(self, dato):
        nuevo = NodoCircular(dato)
        if self.cabeza is None:
            self.cabeza = self.cola = nuevo
        else:
            nuevo.prev = self.cola
            nuevo.next = self.cabeza
            self.cola.next = nuevo
            self.cabeza.prev = nuevo
            self.cola = nuevo
        self._tamaño += 1
        return nuevo
    def insertar_inicio(self, dato):
        nuevo = NodoCircular(dato)
        if self.cabeza is None:
            self.cabeza = self.cola = nuevo
        else:
            nuevo.next = self.cabeza
            nuevo.prev = self.cola
            self.cabeza.prev = nuevo
            self.cola.next = nuevo
            self.cabeza = nuevo
        self._tamaño += 1
        return nuevo
    def buscar(self, dato):
        actual = self.cabeza
        for _ in range(self._tamaño):
            if actual.dato == dato:
                return actual
            actual = actual.next
        return None
    def eliminar(self, dato):
        nodo = self.buscar(dato)
        if nodo is None:
            return False
        if self._tamaño == 1:
            self.cabeza = self.cola = None
        else:
            nodo.prev.next = nodo.next
            nodo.next.prev = nodo.prev
            if nodo is self.cabeza:
                self.cabeza = nodo.next
            if nodo is self.cola:
                self.cola = nodo.prev
        self._tamaño -= 1
        nodo.next = nodo.prev = None
        return True
    def avanzar(self, nodo=None, direccion=1):
        """Da exactamente un paso O(1); desde None comienza por la cabeza/cola."""
        if self.cabeza is None:
            return None
        if nodo is None:
            return self.cabeza if direccion >= 0 else self.cola
        return nodo.next if direccion >= 0 else nodo.prev
    def __iter__(self):
        actual = self.cabeza
        for _ in range(self._tamaño):
            yield actual.dato
            actual = actual.next
    def validar_enlaces(self):
        if self._tamaño == 0:
            return self.cabeza is None and self.cola is None
        if not self.cabeza or not self.cola:
            return False
        if self.cabeza.prev is not self.cola or self.cola.next is not self.cabeza:
            return False
        actual = self.cabeza
        for _ in range(self._tamaño):
            if actual.next is None or actual.prev is None:
                return False
            if actual.next.prev is not actual or actual.prev.next is not actual:
                return False
            actual = actual.next
        return actual is self.cabeza