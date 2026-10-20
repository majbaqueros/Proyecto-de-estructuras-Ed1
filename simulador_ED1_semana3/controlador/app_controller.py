from time import perf_counter
from logica.logistic_engine import LogisticEngine
from logica.metricas import MonitorRendimiento
from modelos.entidades import Paquete
from controlador.rutas_controller import RutasController
class AppController:
    def __init__(self):
        self.engine = LogisticEngine()
        self.contador_id = 0
        self.monitor = MonitorRendimiento()
        self.rutas = RutasController(self.monitor)
        self.rutas.cargar_demostracion()

    def _medir(self, operacion, *args):
        inicio = perf_counter()
        resultado = operacion(*args)
        self.monitor.registrar(perf_counter() - inicio)
        return resultado
    def crear_paquete(self, destino, peso, prioridad):
        destino = destino.strip()
        if not destino:
            raise ValueError("El destino es obligatorio")
        try:
            peso = float(peso)
            prioridad = int(prioridad)
        except (TypeError, ValueError):
            raise ValueError("Peso y prioridad deben ser números válidos") from None
        if peso <= 0 or prioridad not in (1, 2, 3):
            raise ValueError("El peso debe ser mayor a cero y la prioridad debe ser 1, 2 o 3")
        self.contador_id += 1
        paquete = Paquete(id=f"PKG-{self.contador_id:03d}", destino=destino,
                          peso=peso, prioridad=prioridad)
        return self._medir(self.engine.registrar_paquete, paquete)
    def despachar(self):
        return self._medir(self.engine.despachar_siguiente)
    def deshacer(self):
        return self._medir(self.engine.deshacer_ultima_accion)
    def listar_paquetes(self):
        return self.engine.obtener_estado_paquetes()