"""Controlador MVC para la lista didáctica (sin Flet)."""
from time import perf_counter
from estructuras.lista_doblemente import DoublyLinkedList
from estructuras.pila import UndoRedoManager
from database import DatabaseManager


class EstructurasController:
    def __init__(self, monitor=None, db=None):
        self._lista = DoublyLinkedList()
        self._historial = UndoRedoManager()
        self._db = db if db is not None else DatabaseManager()
        self.monitor = monitor

    def _medir(self, operacion, *args):
        inicio = perf_counter()
        resultado = operacion(*args)
        if self.monitor:
            self.monitor.registrar(perf_counter() - inicio)
        return resultado

    def insertar(self, valor, extremo):
        valor = str(valor).strip()
        if not valor:
            raise ValueError("Ingresa un valor")
        if extremo not in ("inicio", "final"):
            raise ValueError("Extremo no válido")
        self._medir(self._lista.insertar_inicio if extremo == "inicio" else self._lista.insertar_final, valor)
        self._historial.ejecutar_accion(extremo, valor)
        self._db.guardar_accion_lista(extremo, valor)

    def eliminar(self, valor):
        valor = str(valor).strip()
        if not valor:
            return False
        eliminado = self._medir(self._lista.eliminar, valor)
        if eliminado:
            self._historial.undo_stack.limpiar()
            self._historial.redo_stack.limpiar()
            self._db.guardar_accion_lista("eliminar", valor)
        return eliminado

    def deshacer(self):
        accion = self._historial.deshacer()
        if accion:
            tipo, _ = accion
            self._medir(self._lista.eliminar_inicio if tipo == "inicio" else self._lista.eliminar_final)
        return accion

    def rehacer(self):
        accion = self._historial.rehacer()
        if accion:
            tipo, valor = accion
            self._medir(self._lista.insertar_inicio if tipo == "inicio" else self._lista.insertar_final, valor)
        return accion

    def estado(self):
        return {
            "elementos": [str(dato) for dato in self._lista],
            "cabeza": self._lista.cabeza.dato if self._lista.cabeza else None,
            "cola": self._lista.cola.dato if self._lista.cola else None,
            "tamano": len(self._lista),
            "integridad": self._lista.validar_enlaces(),
            "undo": self._historial.puede_deshacer(),
            "redo": self._historial.puede_rehacer(),
        }
