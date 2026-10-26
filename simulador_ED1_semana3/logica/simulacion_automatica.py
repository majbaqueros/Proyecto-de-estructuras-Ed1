"""Simulación de carga, ruta circular y entregas reales al llegar al destino.

Las colas y listas enlazadas siguen siendo las estructuras manuales originales.
Cada ciclo puede crear un pequeño lote y mueve el vehículo exactamente un nodo.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoCiclo:
    numero: int
    accion: str
    detalle: str
    parada: str | None
    pendientes: int
    creados: int
    despachados: int
    entregas: tuple = ()


class SimuladorAutomatico:
    """Carga hasta dos paquetes si la cola está vacía y conduce hasta entregarlos.

    Si existen paquetes registrados manualmente, respeta esos pendientes y
    NO agrega otros hasta que todos hayan llegado a sus destinos.
    """

    _prioridades = (3, 1, 2, 1, 3, 2)
    _pesos = (2.0, 5.5, 1.5, 4.0)

    def __init__(self, controller):
        self.controller = controller
        self.ciclos = 0
        self.creados = 0
        self.despachados = 0

    def paso(self):
        paradas = self.controller.rutas.estado()
        if not paradas:
            self.ciclos += 1
            return ResultadoCiclo(self.ciclos, "SIN RUTAS", "Agrega una parada antes de simular",
                                  None, len(self.controller.listar_paquetes()),
                                  self.creados, self.despachados)

        registros = []
        if not self.controller.listar_paquetes():
            # Destinos reales tomados de la lista circular, desde la parada actual.
            indice_actual = next((i for i, p in enumerate(paradas) if p["activa"]), -1)
            for salto in (1, 2):
                destino = paradas[(indice_actual + salto) % len(paradas)]["nombre"]
                prioridad = self._prioridades[self.creados % len(self._prioridades)]
                peso = self._pesos[self.creados % len(self._pesos)]
                paquete = self.controller.crear_paquete(destino, peso, prioridad)
                # crear_paquete devuelve True: el código se obtiene de la numeración real.
                self.creados += 1
                registros.append(f"PKG-{self.controller.contador_id:03d} → {destino}")

        parada, entregados = self.controller.avanzar_y_entregar()
        self.despachados += len(entregados)
        self.ciclos += 1
        partes = []
        if registros:
            partes.append("Creados: " + ", ".join(registros))
        if entregados:
            partes.append("Entregados aquí: " + ", ".join(p.id for p in entregados))
        else:
            partes.append("Sin entregas en esta parada")
        accion = "ENTREGA" if entregados else "RECORRIDO"
        if registros:
            accion = "CARGA + " + accion
        return ResultadoCiclo(
            numero=self.ciclos,
            accion=accion,
            detalle=" | ".join(partes),
            parada=parada,
            pendientes=len(self.controller.listar_paquetes()),
            creados=self.creados,
            despachados=self.despachados,
            entregas=entregados,
        )
