"""Controller de recorridos: la vista no accede directamente a prev/next."""
from time import perf_counter
from estructuras.lista_circular_doble import ListaDoblementeCircular
from logica.destinos import clave_destino
from logica.metricas import MonitorRendimiento

class RutasController:
    def __init__(self, monitor=None):
        self._ruta = ListaDoblementeCircular()
        self._actual = None
        self.vehiculo = "V-001"
        self.monitor = monitor or MonitorRendimiento()
        self.validar_quitar_parada = None  # Regla opcional definida por logística.

    def _medir(self, accion, *args):
        inicio = perf_counter()
        resultado = accion(*args)
        self.monitor.registrar(perf_counter() - inicio)
        return resultado

    @property
    def cantidad(self):
        return len(self._ruta)

    def agregar_parada(self, nombre):
        nombre = " ".join(str(nombre).split())
        if not nombre:
            raise ValueError("Ingresa el nombre de una parada")
        if self.destino_canonico(nombre) is not None:
            raise ValueError(f"Ya existe una parada con el nombre '{nombre}'")
        nuevo = self._medir(self._ruta.insertar_final, nombre)
        if self._actual is None:
            self._actual = nuevo
        return nombre

    def quitar_parada(self, nombre):
        canonico = self.destino_canonico(nombre)
        if canonico is None:
            return False
        if self.validar_quitar_parada is not None:
            self.validar_quitar_parada(canonico)

        def quitar():
            objetivo = self._ruta.buscar(canonico)
            if objetivo is None:
                return False
            if self._actual is objetivo:
                self._actual = objetivo.next if self.cantidad > 1 else None
            return self._ruta.eliminar(canonico)
        return self._medir(quitar)

    def destino_canonico(self, nombre):
        """Devuelve el nombre tal cual se registró o None si no hay ruta."""
        clave = clave_destino(nombre)
        if not clave:
            return None
        for parada in self._ruta:
            if clave_destino(parada) == clave:
                return parada
        return None

    def siguiente(self):
        self._actual = self._medir(self._ruta.avanzar, self._actual, 1)
        return self.actual

    def anterior(self):
        self._actual = self._medir(self._ruta.avanzar, self._actual, -1)
        return self.actual

    @property
    def actual(self):
        return self._actual.dato if self._actual else None

    def estado(self):
        """Instantánea para dibujar. Las listas Python son sólo DTO para la UI."""
        return [{"nombre": parada, "activa": parada == self.actual, "indice": i + 1}
                for i, parada in enumerate(self._ruta)]

    def verificar_integridad(self):
        return self._ruta.validar_enlaces()

    def cargar_demostracion(self):
        for parada in ("Centro de distribución", "Zona Norte", "Zona Este", "Zona Sur"):
            self.agregar_parada(parada)
