"""Controlador del juego previo: concentra reglas y persistencia."""
from time import perf_counter
from pipeline.hanoi import JuegoHanoi
from database import DatabaseManager


class HanoiController:
    def __init__(self, monitor=None):
        self._juego = JuegoHanoi(3)
        self._db = DatabaseManager()
        self.monitor = monitor

    @property
    def movimientos(self):
        return self._juego.movimientos

    def _medir(self, metodo, *args):
        inicio = perf_counter()
        resultado = metodo(*args)
        if self.monitor:
            self.monitor.registrar(perf_counter() - inicio)
        return resultado

    def mover_disco(self, origen, destino):
        resultado = self._medir(self._juego.mover_disco, origen, destino)
        if resultado[0]:
            self._db.guardar_estado_hanoi(self._juego.obtener_estado())
        return resultado

    def reiniciar(self):
        self._medir(self._juego.reiniciar)

    def obtener_estado(self):
        return self._juego.obtener_estado()

    def verificar_victoria(self):
        return self._juego.verificar_victoria()
