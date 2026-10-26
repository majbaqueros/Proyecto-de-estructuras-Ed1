"""Tests de generación, entrega por coincidencia y seguridad de la lista circular."""
from controlador.app_controller import AppController
from logica.simulacion_automatica import SimuladorAutomatico


def test_simulacion_entrega_solo_cuando_llega_a_la_zona():
    app = AppController()
    inicial = app.monitor.operaciones
    sim = SimuladorAutomatico(app)
    resultados = [sim.paso() for _ in range(4)]
    assert [r.parada for r in resultados] == [
        "Zona Norte", "Zona Este", "Zona Sur", "Centro de distribución"
    ]
    assert [r.pendientes for r in resultados] == [1, 0, 1, 0]
    assert [r.entregas[0].destino for r in resultados] == [
        "Zona Norte", "Zona Este", "Zona Sur", "Centro de distribución"
    ]
    assert (sim.creados, sim.despachados, sim.ciclos) == (4, 4, 4)
    assert app.rutas.verificar_integridad()
    assert app.monitor.operaciones > inicial


def test_simulacion_respeta_paquetes_manuales_sin_crear_otros():
    app = AppController()
    app.crear_paquete("Zona Sur", 2, 1)
    sim = SimuladorAutomatico(app)
    assert sim.paso().parada == "Zona Norte"
    assert app.listar_paquetes()[0].destino == "Zona Sur"
    assert sim.creados == 0 and sim.despachados == 0
    sim.paso()  # Zona Este
    resultado = sim.paso()  # Zona Sur: ahora sí entrega.
    assert [p.destino for p in resultado.entregas] == ["Zona Sur"]
    assert sim.creados == 0 and sim.despachados == 1


def test_simulacion_sin_rutas_no_crea_paquetes():
    app = AppController()
    for parada in [x["nombre"] for x in app.rutas.estado()]:
        assert app.rutas.quitar_parada(parada)
    resultado = SimuladorAutomatico(app).paso()
    assert resultado.accion == "SIN RUTAS"
    assert not app.listar_paquetes()


def test_simulacion_sigue_con_cola_modificada_sin_perder_punteros():
    app = AppController()
    sim = SimuladorAutomatico(app)
    for _ in range(10):
        resultado = sim.paso()
        assert resultado.pendientes >= 0
        assert app.rutas.verificar_integridad()
    assert sim.ciclos == 10
    assert sim.creados > 0 and sim.despachados > 0
