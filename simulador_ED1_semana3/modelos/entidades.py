from dataclasses import dataclass, field
from datetime import datetime
@dataclass
class Paquete:
    id: str
    destino: str
    peso: float
    prioridad: int  # 1=Alta, 2=Media, 3=Baja
    fecha_ingreso: datetime = field(default_factory=datetime.now)
@dataclass
class Vehiculo:
    placa: str
    capacidad_max: float
    disponible: bool = True
@dataclass
class Ruta:
    origen: str
    destino: str
    distancia_km: float
    tiempo_estimado_hrs: float
@dataclass
class Almacen:
    nombre: str
    ubicacion: str
    capacidad_max: int
    paquetes_almacenados: list = field(default_factory=list)