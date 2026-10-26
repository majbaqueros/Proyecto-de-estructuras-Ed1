# Guía de práctica en terminal — Semana 3 de ED1

Este material acompaña el simulador Flet y permite demostrar su lógica desde la terminal sin iniciar la interfaz web. **No necesita Docker.**

## 1. Entrar en la carpeta del proyecto

En PowerShell (desde la carpeta exterior del ZIP):

```powershell
cd .\simulador_ED1_semana3
dir main.py
dir demo_terminal_semana3.py
```

Si `dir main.py` no muestra el archivo, primero debes entrar en la carpeta que lo contiene.

## 2. Ver el programa gráfico

```powershell
flet run --web --port 8001 main.py
```

Abre `http://127.0.0.1:8001/`. Detén el servidor con `Ctrl + C`. Las rutas y el panel de métricas se mantienen en memoria durante la sesión; las paradas agregadas **no** se guardan automáticamente en SQLite.

## 3. Ejecutar todas las demostraciones sin interfaz

En **otra terminal**, en la misma carpeta de `main.py`:

```powershell
python demo_terminal_semana3.py
```

El script utiliza **las clases reales** del proyecto (sin Flet). Se verán cinco ejemplos:

1. Insertar tres paradas y comprobar `cola.next is cabeza`, `cabeza.prev is cola` y `validar_enlaces()`; se usa una lista de prueba para mostrar que un enlace roto produce `False`.
2. Recorrer `Centro -> Norte -> Este -> Centro`, retroceder y eliminar un nodo; verificar integridad después de eliminar.
3. Rechazar una parada vacía y paquetes con destino vacío, peso negativo o prioridad fuera del rango 1–3; despachar el de mayor prioridad.
4. Insertar y eliminar nodos de una **lista doble**; registrar las acciones en `registro_demo_semana3.sqlite` mediante `EstructurasController` y `DatabaseManager`.
5. Mostrar operaciones registradas, tasa por segundo, estimación de memoria y benchmark O(1)/O(n).

## 4. Comprobar el historial guardado

Después de ejecutar el ejemplo 4:

```powershell
python -c "import sqlite3; c=sqlite3.connect('registro_demo_semana3.sqlite'); print(c.execute('SELECT id, accion, valor, fecha FROM historial_lista ORDER BY id DESC LIMIT 5').fetchall()); c.close()"
```

El archivo `registro_demo_semana3.sqlite` se crea al ejecutar el script. Conserva el historial de las ejecuciones, de modo que al repetirlo se añaden nuevas filas. Es independiente de `proyecto_ed1.db` (base de datos que usa la vista Estructuras cuando corre el simulador normal). **Rutas y métricas no se guardan en esa base de datos.**

Para consultar el historial de la aplicación normal desde la misma carpeta:

```powershell
python -c "import sqlite3; c=sqlite3.connect('proyecto_ed1.db'); print(c.execute('SELECT accion, valor, fecha FROM historial_lista ORDER BY id DESC LIMIT 5').fetchall()); c.close()"
```

## 5. Ejecutar pruebas automatizadas

```powershell
python -m pip install pytest
python -m pytest -q
```

En la versión comprobada: `14 passed`. Los resultados confirman los casos cubiertos por las pruebas, **no** una cobertura del 100%.

## 6. Qué debo responder al docente

**¿Qué es un nodo?** Objeto que almacena `dato` y dos referencias (`next`, `prev`) a otros nodos.

**¿Qué asegura la circularidad?** Para lista no vacía, `cola.next is cabeza` y `cabeza.prev is cola`. Además, para cada nodo se cumple `nodo.next.prev is nodo` y `nodo.prev.next is nodo`.

**¿Cómo se validan esas referencias?** `validar_enlaces()` recorre los nodos y comprueba esas invariantes. Es O(n) porque revisa todos los nodos; en la pantalla aparece `Punteros: CORRECTOS` cuando retorna `True`.

**¿Qué se registra al agregar una parada?** Se crea un nodo con el nombre y se conecta a la lista circular **en memoria**; también se registra el tiempo de esa operación en `MonitorRendimiento`. **No se guarda en SQLite** desde `RutasController`.

**¿Qué se registra en SQLite?** En `EstructurasController`, las llamadas a `insertar()` y las eliminaciones exitosas ejecutan `guardar_accion_lista()` y escriben en la tabla `historial_lista` las columnas `accion`, `valor` y `fecha`. `deshacer()` / `rehacer()` modifican el estado en memoria, pero **no añaden una fila propia en esa tabla**.

**¿Qué validaciones hay?** Paradas vacías se rechazan con `ValueError`; los paquetes exigen destino no vacío, peso positivo y prioridad 1, 2 o 3. `verificar_integridad()` confirma los punteros.

**¿Qué significa O(1)?** Avanzar al nodo `next` o `prev` tarda tiempo constante porque ya existe la referencia. Insertar al final con puntero a cola también es O(1).

**¿Qué significa O(n)?** Buscar/eliminar una parada por su nombre puede requerir recorrer todos los nodos; comprobar *todos* los enlaces también es O(n).

**¿Qué mide el benchmark?** El tiempo total de N inserciones al final y N búsquedas de un valor inexistente. Las cantidades de trabajo no tienen la misma complejidad por operación; los milisegundos reales cambian según el computador.

**¿Qué hace Flet?** Construye la interfaz y enlaza los clics con los controladores Python. La terminal inicia el servidor y Chrome abre `127.0.0.1:8001`; la interfaz y la lógica comparten el mismo proceso Python local.

**¿Docker es obligatorio?** No. Se usa opcionalmente para despliegue; no es necesario para las demostraciones, las pruebas ni la ejecución web local.
