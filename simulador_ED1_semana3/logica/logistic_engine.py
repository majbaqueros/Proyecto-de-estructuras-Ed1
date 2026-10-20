from estructuras.lista_doblemente import DoublyLinkedList
from estructuras.colas import PriorityQueue, CircularQueue
from estructuras.pila import Stack
from modelos.entidades import Paquete, Vehiculo, Ruta, Almacen
class LogisticEngine:
    """Motor de logística que usa estructuras de datos para gestionar paquetes."""
    def __init__(self):
        self.paquetes_pendientes = PriorityQueue()  # Cola de prioridad
        self.historial_envios = Stack()             # Pila para undo
        self.rutas_disponibles = DoublyLinkedList() # Lista de rutas
        self.vehiculos = CircularQueue(5)           # Cola circular de vehículos
        self.almacen = Almacen("Central", "Ciudad", 100)
    # --- Gestión de Paquetes ---
    def registrar_paquete(self, paquete: Paquete):
        self.paquetes_pendientes.encolar(paquete, paquete.prioridad)
        self.almacen.paquetes_almacenados.append(paquete)
        self.historial_envios.push(("registrar", paquete))
        return True
    def despachar_siguiente(self):
        dato = self.paquetes_pendientes.desencolar()
        if dato:
            # La cola devuelve (paquete, prioridad), desempaquetamos
            paquete, prioridad = dato
            self.historial_envios.push(("despachar", paquete))
            if paquete in self.almacen.paquetes_almacenados:
                self.almacen.paquetes_almacenados.remove(paquete)
            return paquete
        return None
    def deshacer_ultima_accion(self):
        accion = self.historial_envios.pop()
        if accion:
            tipo, paquete = accion
            if tipo == "registrar":
                # Revertimos tanto almacén como cola (sin dejar un paquete fantasma).
                self.paquetes_pendientes.eliminar_dato(paquete)
                if paquete in self.almacen.paquetes_almacenados:
                    self.almacen.paquetes_almacenados.remove(paquete)
            elif tipo == "despachar":
                # Devolvemos el paquete a la cola
                self.paquetes_pendientes.encolar(paquete, paquete.prioridad)
                self.almacen.paquetes_almacenados.append(paquete)
            return accion
        return None
    # --- Gestión de Rutas ---
    def agregar_ruta(self, ruta: Ruta):
        self.rutas_disponibles.insertar_final(ruta)
        return True
    # --- Reportes ---
    def obtener_estado_paquetes(self):
        """Devuelve una lista de paquetes ordenados por prioridad."""
        paquetes = []
        actual = self.paquetes_pendientes.cabeza
        while actual:
            # actual.dato es (paquete, prioridad)
            paquete, prioridad = actual.dato  # <-- DESEMPAQUETAR
            paquetes.append(paquete)
            actual = actual.next
        return paquetes