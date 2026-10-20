import pytest
from estructuras.lista_doblemente import DoublyLinkedList
from estructuras.pila import Stack
from pipeline.validador import validar_parentesis

def test_lista_vacia():
    lista = DoublyLinkedList()
    assert lista.eliminar(5) == False

def test_pila_limites():
    pila = Stack()
    assert pila.pop() is None
    pila.push(1)
    assert pila.pop() == 1
    assert pila.esta_vacia() == True

def test_validador():
    assert validar_parentesis("({[]})") == True
    assert validar_parentesis("({[})") == False
    assert validar_parentesis("") == True