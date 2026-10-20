"""Controlador MVC para pila de llamadas, sin dependencias de GUI."""
from time import perf_counter
from estructuras.pila import Stack
from database import DatabaseManager


class CallStackController:
    def __init__(self, monitor=None, db=None):
        self._pila = Stack()
        self._db = db if db is not None else DatabaseManager()
        self.monitor = monitor

    def _medir(self, operacion, *args):
        inicio = perf_counter()
        valor = operacion(*args)
        if self.monitor:
            self.monitor.registrar(perf_counter() - inicio)
        return valor

    def llamar(self, funcion):
        funcion = str(funcion).strip()
        if not funcion:
            raise ValueError("Nombre de función obligatorio")
        self._medir(self._pila.push, funcion)
        self._db.guardar_llamada(funcion)

    def retornar(self):
        return self._medir(self._pila.pop)

    def estado(self):
        valores = []
        actual = self._pila.tope
        while actual is not None:
            valores.append(actual.dato)
            actual = actual.siguiente
        return valores  # DTO para la vista, no estructura subyacente.
