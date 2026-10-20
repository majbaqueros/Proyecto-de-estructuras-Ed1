"""Lista doble clásica (no circular), con operaciones de enlaces explícitos."""
class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.next = None
        self.prev = None


class DoublyLinkedList:
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._tamaño = 0

    def __len__(self):
        return self._tamaño

    def __iter__(self):
        actual = self.cabeza
        while actual:
            yield actual.dato
            actual = actual.next

    def insertar_inicio(self, dato):
        nuevo = Nodo(dato)
        if not self.cabeza:
            self.cabeza = self.cola = nuevo
        else:
            nuevo.next = self.cabeza
            self.cabeza.prev = nuevo
            self.cabeza = nuevo
        self._tamaño += 1

    def insertar_final(self, dato):
        nuevo = Nodo(dato)
        if not self.cola:
            self.cabeza = self.cola = nuevo
        else:
            nuevo.prev = self.cola
            self.cola.next = nuevo
            self.cola = nuevo
        self._tamaño += 1

    def eliminar(self, dato):
        actual = self.cabeza
        while actual:
            if actual.dato == dato:
                if actual.prev:
                    actual.prev.next = actual.next
                else:
                    self.cabeza = actual.next
                if actual.next:
                    actual.next.prev = actual.prev
                else:
                    self.cola = actual.prev
                self._tamaño -= 1
                actual.prev = actual.next = None
                return True
            actual = actual.next
        return False

    def eliminar_inicio(self):
        """Retirar cabeza en O(1), sin búsqueda."""
        if self.cabeza is None:
            return None
        actual = self.cabeza
        self.cabeza = actual.next
        if self.cabeza is None:
            self.cola = None
        else:
            self.cabeza.prev = None
        self._tamaño -= 1
        actual.next = actual.prev = None
        return actual.dato

    def validar_enlaces(self):
        if self._tamaño == 0:
            return self.cabeza is None and self.cola is None
        if self.cabeza.prev is not None or self.cola.next is not None:
            return False
        actual, anterior, cantidad = self.cabeza, None, 0
        while actual and cantidad <= self._tamaño:
            if actual.prev is not anterior:
                return False
            anterior, actual = actual, actual.next
            cantidad += 1
        return cantidad == self._tamaño and anterior is self.cola and actual is None

    def eliminar_final(self):
        """Retirar cola en O(1)."""
        if self.cola is None:
            return None
        actual = self.cola
        self.cola = actual.prev
        if self.cola is None:
            self.cabeza = None
        else:
            self.cola.next = None
        self._tamaño -= 1
        actual.next = actual.prev = None
        return actual.dato
