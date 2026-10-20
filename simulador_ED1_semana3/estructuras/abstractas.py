from abc import ABC, abstractmethod
class ColeccionAbstracta(ABC):
    @abstractmethod
    def esta_vacia(self) -> bool: pass
    @abstractmethod
    def tamaño(self) -> int: pass
    @abstractmethod
    def limpiar(self): pass