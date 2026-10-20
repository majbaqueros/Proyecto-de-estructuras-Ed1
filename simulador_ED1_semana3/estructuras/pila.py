class NodoPila:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None
class Stack:
    def __init__(self):
        self.tope = None
        self._tamaño = 0
    def tamaño(self):
            return self._tamaño
    def push(self, dato):
        nuevo = NodoPila(dato)
        nuevo.siguiente = self.tope
        self.tope = nuevo
        self._tamaño += 1
    def pop(self):
        if not self.tope: return None
        dato = self.tope.dato
        self.tope = self.tope.siguiente
        self._tamaño -= 1
        return dato
    def esta_vacia(self):
        return self.tope is None
    def peek(self):
        return self.tope.dato if self.tope else None
    def limpiar(self):
        """Vacía la pila por completo."""
        self.tope = None
        self._tamaño = 0
# UndoRedoManager
class UndoRedoManager:
    def __init__(self):
        self.undo_stack = Stack()
        self.redo_stack = Stack()
    def ejecutar(self, accion):
        self.undo_stack.push(accion)
        self.redo_stack.limpiar() # Al hacer nueva acción, se borra el redo
    def deshacer(self):
        accion = self.undo_stack.pop()
        if accion:
            self.redo_stack.push(accion)
            return f"Deshecho: {accion}"
        return "Nada que deshacer"
    def rehacer(self):
        accion = self.redo_stack.pop()
        if accion:
            self.undo_stack.push(accion)
            return f"Rehecho: {accion}"
        return "Nada que rehacer"
class UndoRedoManager:
    def __init__(self):
        self.undo_stack = Stack()
        self.redo_stack = Stack()
    def ejecutar_accion(self, accion, valor):
        """Guarda la acción en la pila de Undo."""
        # Guardamos una tupla: (tipo_accion, valor)
        self.undo_stack.push((accion, valor))
        # Si hacemos una nueva acción, borramos el historial de Redo
        self.redo_stack.limpiar() 
    def deshacer(self):
        """Saca la última acción de Undo y la mueve a Redo."""
        accion = self.undo_stack.pop()
        if accion:
            self.redo_stack.push(accion)
            return accion
        return None
    def rehacer(self):
        """Saca la última acción de Redo y la mueve a Undo."""
        accion = self.redo_stack.pop()
        if accion:
            self.undo_stack.push(accion)
            return accion
        return None
    def puede_deshacer(self):
        return not self.undo_stack.esta_vacia()
    def puede_rehacer(self):
        return not self.redo_stack.esta_vacia()