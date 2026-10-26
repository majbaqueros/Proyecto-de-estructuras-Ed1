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
        self.rutas.validar_quitar_parada = self._validar_quitar_parada
        self.total_entregados = 0
        self.ultima_entrega = None
        self.simulacion_activa = False
        self.recorrido_manual_activo = False

    def _validar_quitar_parada(self, nombre):
        if any(p.destino == nombre for p in self.listar_paquetes()):
            raise ValueError(
                f"No puedes eliminar '{nombre}': hay paquetes pendientes para esa parada."
            )

    def _medir(self, operacion, *args):
        inicio = perf_counter()
        resultado = operacion(*args)
        self.monitor.registrar(perf_counter() - inicio)
        return resultado

    def crear_paquete(self, destino, peso, prioridad):
        destino = destino.strip()
        if not destino:
            raise ValueError("El destino es obligatorio")
        destino_valido = self.rutas.destino_canonico(destino)
        if destino_valido is None:
            disponibles = ", ".join(parada["nombre"] for parada in self.rutas.estado())
            raise ValueError(
                f"Destino '{destino}' no registrado en Rutas. "
                f"Paradas válidas: {disponibles or '(ninguna)'}"
            )
        try:
            peso = float(peso)
            prioridad = int(prioridad)
        except (TypeError, ValueError):
            raise ValueError("Peso y prioridad deben ser números válidos") from None
        if peso <= 0 or prioridad not in (1, 2, 3):
            raise ValueError("El peso debe ser mayor a cero y la prioridad debe ser 1, 2 o 3")
        self.contador_id += 1
        paquete = Paquete(id=f"PKG-{self.contador_id:03d}", destino=destino_valido,
                          peso=peso, prioridad=prioridad)
        return self._medir(self.engine.registrar_paquete, paquete)

    def despachar(self):
        """El botón manual también respeta la ubicación actual del vehículo."""
        paquete = self._medir(self.engine.despachar_en_destino, self.rutas.actual)
        if paquete is not None:
            self._contar_entrega(paquete)
        return paquete

    def _contar_entrega(self, paquete):
        self.total_entregados += 1
        self.ultima_entrega = paquete

    def avanzar_y_entregar(self, direccion=1):
        """Mueve el vehículo; al llegar entrega todos los paquetes de esa zona.

        La selección entre paquetes coincidentes respeta la cola de prioridad.
        Retorna (nombre_de_parada, tupla_de_paquetes_entregados).
        """
        parada = self.rutas.siguiente() if direccion >= 0 else self.rutas.anterior()
        entregados = []  # Solo salida temporal, NO almacena la cola subyacente.
        while parada is not None:
            paquete = self._medir(self.engine.despachar_en_destino, parada)
            if paquete is None:
                break
            self._contar_entrega(paquete)
            entregados.append(paquete)
        return parada, tuple(entregados)

    def deshacer(self):
        return self._medir(self.engine.deshacer_ultima_accion)

    def listar_paquetes(self):
        return self.engine.obtener_estado_paquetes()
