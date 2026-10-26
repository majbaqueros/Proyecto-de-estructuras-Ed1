"""Validaciones pedidas: no registrar destinos ajenos y entregar al llegar."""
import pytest
from controlador.app_controller import AppController
from estructuras.colas import PriorityQueue


def test_rechaza_destino_inexistente_sin_consumir_id():
    app = AppController()
    with pytest.raises(ValueError, match="no registrado en Rutas"):
        app.crear_paquete("SantaCruz", 5, 1)
    assert app.contador_id == 0
    assert app.listar_paquetes() == []


def test_admite_destino_existente_sin_distinguir_mayusculas_acentos():
    app = AppController()
    app.rutas.agregar_parada("La Paz")
    app.crear_paquete("  la  PAZ ", 2, 1)
    assert app.listar_paquetes()[0].destino == "La Paz"
    app.crear_paquete(" ZONA  NORTE ", 2, 1)
    assert app.listar_paquetes()[1].destino == "Zona Norte"


def test_entrega_automaticamente_en_zona_y_no_antes():
    app = AppController()
    app.crear_paquete("Zona Sur", 1, 1)
    app.crear_paquete("Zona Norte", 1, 3)
    assert app.despachar() is None  # Centro no tiene paquetes.
    _, entregados = app.avanzar_y_entregar()  # Norte
    assert [p.destino for p in entregados] == ["Zona Norte"]
    assert [p.destino for p in app.listar_paquetes()] == ["Zona Sur"]
    _, entregados = app.avanzar_y_entregar()  # Este
    assert entregados == ()
    parada, entregados = app.avanzar_y_entregar()  # Sur
    assert parada == "Zona Sur"
    assert [p.destino for p in entregados] == ["Zona Sur"]
    assert app.total_entregados == 2
    assert app.listar_paquetes() == []


def test_dos_paquetes_misma_zona_se_entregan_en_orden_de_prioridad():
    app = AppController()
    app.crear_paquete("Zona Norte", 1, 3)
    app.crear_paquete("Zona Norte", 1, 1)
    app.crear_paquete("Zona Norte", 1, 2)
    app.crear_paquete("Zona Sur", 1, 1)
    parada, entregados = app.avanzar_y_entregar()
    assert parada == "Zona Norte"
    assert [p.prioridad for p in entregados] == [1, 2, 3]
    assert [p.destino for p in app.listar_paquetes()] == ["Zona Sur"]


def test_no_se_puede_quitar_parada_con_entregas_pendientes():
    app = AppController()
    app.crear_paquete("Zona Norte", 1, 2)
    with pytest.raises(ValueError, match="paquetes pendientes"):
        app.rutas.quitar_parada("zona norte")
    assert app.rutas.verificar_integridad()
    app.avanzar_y_entregar()
    assert app.rutas.quitar_parada("Zona Norte")
    assert app.rutas.verificar_integridad()


def test_no_permite_rutas_duplicadas_con_distinta_escritura():
    app = AppController()
    with pytest.raises(ValueError, match="Ya existe"):
        app.rutas.agregar_parada("  zona norte  ")
    assert app.rutas.cantidad == 4


def test_cola_desencolar_si_preserva_prioridad_y_restantes():
    cola = PriorityQueue()
    for valor, prioridad in [("sur", 1), ("norte", 3), ("norte-alta", 1), ("este", 2)]:
        cola.encolar(valor, prioridad)
    assert cola.desencolar_si(lambda valor: valor.startswith("norte")) == ("norte-alta", 1)
    assert cola.desencolar_si(lambda valor: valor.startswith("norte")) == ("norte", 3)
    assert cola.desencolar_si(lambda valor: valor == "no existe") is None
    assert cola.desencolar() == ("sur", 1)
    assert cola.desencolar() == ("este", 2)
    assert cola.desencolar() is None
