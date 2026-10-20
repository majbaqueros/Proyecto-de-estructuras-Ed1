from estructuras.pila import Stack

class JuegoHanoi:
    def __init__(self, num_discos=3):
        self.torres = {
            "A": Stack(),
            "B": Stack(),
            "C": Stack()
        }
        self.num_discos = num_discos
        self.movimientos = 0
        self.reiniciar()

    def reiniciar(self):
        """Limpia las torres y coloca los discos en la Torre A."""
        for t in self.torres.values():
            t.limpiar()
        
        # Insertamos los discos del más grande al más pequeño en la Torre A
        for i in range(self.num_discos, 0, -1):
            self.torres["A"].push(i)
        self.movimientos = 0

    def mover_disco(self, origen: str, destino: str) -> tuple[bool, str]:
        """Intenta mover un disco de una torre a otra. Retorna (éxito, mensaje)."""
        torre_origen = self.torres[origen]
        torre_destino = self.torres[destino]

        if torre_origen.esta_vacia():
            return False, f"❌ La torre {origen} está vacía."

        disco_a_mover = torre_origen.peek()

        # Regla: No se puede poner un disco grande sobre uno pequeño
        if not torre_destino.esta_vacia() and disco_a_mover > torre_destino.peek():
            return False, f"❌ No puedes poner el disco {disco_a_mover} sobre el {torre_destino.peek()}."

        # Si pasa las validaciones, movemos el disco
        torre_origen.pop()
        torre_destino.push(disco_a_mover)
        self.movimientos += 1
        return True, f"✅ Movido disco {disco_a_mover} de {origen} a {destino}"

    def verificar_victoria(self) -> bool:
        """El juego se gana si todos los discos están en la Torre C."""
        return self.torres["C"].tamaño() == self.num_discos

    def obtener_estado(self):
        """Devuelve una representación visual de las torres para la interfaz."""
        estado = {}
        for nombre, torre in self.torres.items():
            discos = []
            actual = torre.tope
            while actual:
                discos.append(actual.dato)
                actual = actual.siguiente
            # Invertimos para mostrar el fondo primero y el tope al final
            estado[nombre] = discos[::-1]
        return estado