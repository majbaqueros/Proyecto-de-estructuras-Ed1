"""Panel de métricas: muestra eventos instrumentados y benchmark aislado."""
import flet as ft
from logica.metricas import estimar_memoria_nodos, ejecutar_benchmark


def crear_tab_metricas(page: ft.Page, controller) -> ft.Container:
    monitor = controller.monitor
    ops = ft.Text("0", size=29, weight=ft.FontWeight.BOLD)
    velocidad = ft.Text("0.00", size=29, weight=ft.FontWeight.BOLD)
    ultima = ft.Text("0.000", size=29, weight=ft.FontWeight.BOLD)
    promedio = ft.Text("0.000", size=29, weight=ft.FontWeight.BOLD)
    comparacion = ft.Text("Ejecuta el benchmark para obtener tiempos medidos.")
    campo_n = ft.TextField(label="Número de operaciones (10–10000)", value="2000", width=250)
    fila_memoria = ft.Column(spacing=6)
    indicador = ft.Text("Operaciones/s = eventos registrados en los últimos 5 segundos / 5.", size=12)

    def tarjeta(titulo, valor, unidad):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=13, color=ft.Colors.BLUE_GREY_600),
                valor,
                ft.Text(unidad, size=11, color=ft.Colors.BLUE_GREY_500),
            ], spacing=3),
            padding=16, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=12,
            col={"xs": 6, "md": 3},
        )

    def actualizar(_=None):
        datos = monitor.resumen()
        ops.value = str(datos["operaciones"])
        velocidad.value = f'{datos["ops_segundo"]:.2f}'
        ultima.value = f'{datos["ultima_ms"]:.3f}'
        promedio.value = f'{datos["promedio_ms"]:.3f}'
        cantidad = controller.rutas.cantidad + len(controller.listar_paquetes())
        memoria = estimar_memoria_nodos(cantidad)
        fila_memoria.controls = [
            ft.Row([ft.Text(f"{nombre}", width=140),
                    ft.Text(f"≈ {datos_nodo['bytes_nodo']} bytes/nodo", width=180),
                    ft.Text(f"≈ {datos_nodo['bytes_total']} bytes para {cantidad} nodos")], wrap=True)
            for nombre, datos_nodo in memoria.items()
        ]
        page.update()

    def benchmark(e):
        try:
            resultado = ejecutar_benchmark(int(campo_n.value))
            comparacion.value = (
                f"Para {resultado.cantidad} operaciones: insertar al final O(1) ≈ {resultado.append_ms:.2f} ms; "
                f"buscar ausente O(n) ≈ {resultado.buscar_ms:.2f} ms. "
                f"Búsqueda / inserción ≈ {resultado.ratio:.1f}x."
            )
        except (ValueError, TypeError):
            comparacion.value = "Ingresa un entero entre 10 y 10000."
        page.update()

    contenido = ft.Container(padding=16, content=ft.Column([
        ft.Text("📊 Rendimiento en tiempo real", size=22, weight=ft.FontWeight.BOLD),
        ft.Text("Medición del modelo Python; cada sesión conserva sus propios contadores."),
        ft.ResponsiveRow([
            tarjeta("Operaciones totales", ops, "registro del controlador"),
            tarjeta("Operaciones por segundo", velocidad, "ventana móvil de 5 s"),
            tarjeta("Última operación", ultima, "milisegundos"),
            tarjeta("Latencia media", promedio, "milisegundos"),
        ], spacing=10, run_spacing=10),
        indicador, ft.Button("Actualizar ahora", icon=ft.Icons.REFRESH, on_click=actualizar),
        ft.Divider(),
        ft.Text("Memoria aproximada por nodo", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("sys.getsizeof(nodo) + sys.getsizeof(dato) en CPython. Es una aproximación; "
                "no incluye referencias compartidas, asignador, web ni renderizado Flutter.", size=12),
        fila_memoria,
        ft.Divider(),
        ft.Text("Comparativa empírica: O(1) vs O(n)", size=18, weight=ft.FontWeight.BOLD),
        ft.Row([campo_n, ft.Button("Ejecutar benchmark", on_click=benchmark, icon=ft.Icons.SPEED)], wrap=True),
        comparacion,
        ft.Text("Se insertan N nodos en una lista doble (O(1) por inserción) y se realizan N "
                "búsquedas de un valor ausente en esa lista (O(n) por búsqueda). "
                "Los tiempos reales dependen del dispositivo; el orden teórico no.", size=12, italic=True),
    ], scroll=ft.ScrollMode.AUTO, expand=True))
    actualizar()
    return contenido, actualizar
