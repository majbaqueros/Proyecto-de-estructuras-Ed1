# Guion de exposición (8 diapositivas / ~6 minutos)

1. **Portada**: ED1 · Semana 3 · Simulador de logística multiplataforma. Mostrar objetivo y tecnologías Python, Flet, SQLite.
2. **Problema y objetivo**: secuenciar paradas de reparto y paquetes prioritarios; hacer visible la memoria con punteros.
3. **MVC**: mostrar estructura de carpetas y responsabilidad de Modelo / Controlador / Vista. Las vistas no tocan enlaces de rutas.
4. **Lista doblemente circular**: `cabeza.prev = cola`, `cola.next = cabeza`; recorrer ambas direcciones y borrar nodos sin romper la estructura.
5. **Demostración en vivo**: agregar parada, avanzar, retroceder, animar vuelta completa y comprobar integridad.
6. **Métricas**: ventana 5 s ops/s, `perf_counter`, estimación CPython, benchmark N inserciones O(1) / N búsquedas O(n); indicar limitaciones.
7. **Multiplataforma**: UI responsiva, barra inferior en móvil, web por WebSockets, EXE Windows x64 y APK vía Flet Build.
8. **Pruebas y cierre**: pruebas unitarias, próximos pasos de despliegue real y mensaje final: modelos manuales + interacción + verificabilidad.

Preguntas esperables: ¿por qué circular? Para volver al origen con `next` sin `None`. ¿Por qué O(1)? Porque el enlace ya está localizado; buscar por valor sigue siendo O(n). ¿Por qué no construir EXE Linux→Windows? Porque `flet build windows` sólo funciona en Windows.
