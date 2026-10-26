from estructuras.lista_circular_doble import ListaDoblementeCircular
from estructuras.colas import PriorityQueue, CircularQueue
from logica.metricas import ejecutar_benchmark


def test_lista_circular_con_punteros_y_eliminacion():
    linked = ListaDoblementeCircular()
    assert linked.validar_enlaces()
    a = linked.insertar_final('A')
    b = linked.insertar_final('B')
    linked.insertar_final('C')
    assert linked.avanzar(a).dato == 'B'
    assert linked.avanzar(linked.cola).dato == 'A'
    assert linked.avanzar(b,-1).dato == 'A'
    assert linked.validar_enlaces()
    assert linked.eliminar('B') is True
    assert linked.validar_enlaces()
    assert len(linked) == 2


def test_cola_prioridad_enlazada_estable():
    q=PriorityQueue()
    q.encolar('Baja', 3)
    q.encolar('Alta-1', 1)
    q.encolar('Alta-2', 1)
    assert q.desencolar()[0]=='Alta-1'
    assert q.desencolar()[0]=='Alta-2'
    assert q.desencolar()[0]=='Baja'
    assert q.desencolar() is None


def test_cola_circular_enlazada():
    q=CircularQueue(2)
    q.encolar('X')
    q.encolar('Y')
    assert q.desencolar()=='X'
    q.encolar('Z')
    assert q.desencolar()=='Y'
    assert q.desencolar()=='Z'


def test_benchmark_no_modifica_datos():
    bench=ejecutar_benchmark(25)
    assert bench.cantidad==25 and bench.append_ms>=0 and bench.buscar_ms>=0
