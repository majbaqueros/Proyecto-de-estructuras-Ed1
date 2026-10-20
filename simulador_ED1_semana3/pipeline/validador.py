from estructuras.pila import Stack

def validar_parentesis(cadena: str) -> bool:
    pila = Stack()
    pares = {')': '(', ']': '[', '}': '{'}
    
    for char in cadena:
        if char in "([{":
            pila.push(char)
        elif char in ")]}":
            if pila.esta_vacia() or pila.pop() != pares[char]:
                return False
    return pila.esta_vacia()

def evaluar_postfija(expresion: str) -> float:
    pila = Stack()
    tokens = expresion.split()
    
    for token in tokens:
        if token in "+-*/":
            b = pila.pop()
            a = pila.pop()
            if token == '+': pila.push(a + b)
            elif token == '-': pila.push(a - b)
            elif token == '*': pila.push(a * b)
            elif token == '/': pila.push(a / b)
        else:
            pila.push(float(token))
    
    return pila.pop()