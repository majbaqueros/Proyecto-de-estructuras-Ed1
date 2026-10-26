import math
import pytest
from estructuras.lista_circular_doble import ListaDoblementeCircular
from estructuras.lista_doblemente import DoublyLinkedList
from estructuras.colas import PriorityQueue, CircularQueue
from controlador.rutas_controller import RutasController
from controlador.app_controller import AppController
from logica.metricas import MonitorRendimiento, estimar_memoria_nodos, ejecutar_benchmark


def test_circular_vacia_un_nodo_y_vuelta_completa():
    ruta = ListaDoblementeCircular()
    assert ruta.validar_enlaces() and ruta.avanzar() is None
    primero = ruta.insertar_final('A')
    assert ruta.cabeza is ruta.cola is primero
    assert primero.prev is primero.next is primero
    assert ruta.avanzar(primero) is primero
    ruta.insertar_final('B')
    ruta.insertar_final('C')
    assert list(ruta) == ['A', 'B', 'C']
    assert ruta.validar_enlaces()
    assert ruta.cola.next is ruta.cabeza and ruta.cabeza.prev is ruta.cola
    ruta.insertar_inicio('Z')
    assert list(ruta) == ['Z', 'A', 'B', 'C'] and ruta.validar_enlaces()
    assert ruta.eliminar('Z') and ruta.validar_enlaces()
    actual = ruta.cabeza
    for _ in range(3):
        actual = ruta.avanzar(actual)
    assert actual is ruta.cabeza
    assert ruta.avanzar(ruta.cabeza, -1) is ruta.cola


@pytest.mark.parametrize('quitar,esperado', [('A',['B','C']), ('B',['A','C']), ('C',['A','B'])])
def test_circular_eliminar_posiciones(quitar, esperado):
    ruta = ListaDoblementeCircular()
    for n in 'ABC':
        ruta.insertar_final(n)
    assert ruta.eliminar(quitar)
    assert list(ruta) == esperado
    assert ruta.validar_enlaces()
    assert not ruta.eliminar(quitar)
    for n in esperado:
        assert ruta.eliminar(n)
    assert ruta.validar_enlaces()


def test_lista_doble_integridad_centro_duplicados_y_extremos():
    lista = DoublyLinkedList()
    for x in ['X','Y','Z']:
        lista.insertar_final(x)
    assert lista.eliminar('Y')
    assert lista.cabeza.next is lista.cola
    assert lista.cola.prev is lista.cabeza
    assert lista.validar_enlaces()
    assert lista.eliminar_inicio() == 'X'
    assert lista.eliminar_final() == 'Z'
    assert lista.validar_enlaces()
    assert lista.eliminar_final() is None


def test_cola_circular_enlazada_limites():
    with pytest.raises(ValueError):
        CircularQueue(0)
    cola = CircularQueue(2)
    assert cola.desencolar() is None
    cola.encolar('A')
    cola.encolar('B')
    assert cola.final.next is cola.frente
    with pytest.raises(OverflowError):
        cola.encolar('C')
    assert cola.desencolar() == 'A'
    cola.encolar('C')
    assert cola.desencolar() == 'B'
    assert cola.desencolar() == 'C'
    assert cola.frente is cola.final is None


def test_prioridad_fifo_y_undo_registro():
    controlador = AppController()
    controlador.crear_paquete('Zona Norte',5,3)
    controlador.crear_paquete('Zona Sur',1,1)
    controlador.crear_paquete('Zona Este',1,1)
    assert [x.destino for x in controlador.listar_paquetes()] == ['Zona Sur','Zona Este','Zona Norte']
    assert controlador.deshacer()[0] == 'registrar'
    assert [x.destino for x in controlador.listar_paquetes()] == ['Zona Sur','Zona Norte']
    assert controlador.despachar() is None  # Vehículo en Centro; no se puede entregar Sur.
    parada, entregados = controlador.avanzar_y_entregar()
    assert parada == 'Zona Norte'
    assert [p.destino for p in entregados] == ['Zona Norte']
    assert controlador.deshacer()[0] == 'despachar'
    assert [x.destino for x in controlador.listar_paquetes()] == ['Zona Sur','Zona Norte']


def test_controlador_rutas_ajusta_actual_al_borrar():
    c = RutasController()
    for nombre in ['A', 'B', 'C']:
        c.agregar_parada(nombre)
    assert c.actual == 'A'
    assert c.siguiente() == 'B'
    assert c.quitar_parada('B')
    assert c.actual == 'C'
    assert c.anterior() == 'A'
    assert c.quitar_parada('A')
    assert c.quitar_parada('C')
    assert c.actual is None and c.verificar_integridad()
    with pytest.raises(ValueError):
        c.agregar_parada('  ')


def test_metricas_y_benchmark():
    monitor = MonitorRendimiento(ventana_s=5)
    monitor.registrar(0.003)
    resumen = monitor.resumen()
    assert resumen['operaciones'] == 1 and math.isclose(resumen['ultima_ms'], 3)
    memoria = estimar_memoria_nodos(10)
    assert all(d['bytes_total'] == 10*d['bytes_nodo'] for d in memoria.values())
    resultado = ejecutar_benchmark(50)
    assert resultado.cantidad == 50
    assert resultado.append_ms > 0 and resultado.buscar_ms > 0


def test_controlador_estructuras_undo_repetidos_y_eliminar(tmp_path):
    from controlador.estructuras_controller import EstructurasController
    from database import DatabaseManager
    db = DatabaseManager(str(tmp_path / 'pruebas.sqlite'))
    c = EstructurasController(db=db)
    c.insertar('A', 'final')
    c.insertar('A', 'inicio')
    c.insertar('B', 'final')
    assert c.estado()['elementos'] == ['A','A','B']
    c.deshacer()
    c.deshacer()
    assert c.estado()['elementos'] == ['A']
    c.rehacer()
    assert c.estado()['elementos'] == ['A', 'A']
    assert c.eliminar('A')
    assert not c.estado()['undo']
    assert c.estado()['integridad']
    db.cerrar()


def test_controlador_callstack(tmp_path):
    from controlador.callstack_controller import CallStackController
    from database import DatabaseManager
    db = DatabaseManager(str(tmp_path / 'calls.sqlite'))
    c = CallStackController(db=db)
    c.llamar('main')
    c.llamar('funcion')
    assert c.estado() == ['funcion','main']
    assert c.retornar() == 'funcion'
    assert c.estado() == ['main']
    db.cerrar()
