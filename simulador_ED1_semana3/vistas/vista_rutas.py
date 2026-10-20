"""Recorrido de vehículos animado, sin manipular punteros en la capa Flet."""
import asyncio
import flet as ft
def crear_tab_rutas(page: ft.Page, controller) -> ft.Container:
    rutas = controller.rutas
    reproduciendo = False
    campo = ft.TextField(label="Nueva parada", hint_text="Ej. Zona Oeste", expand=True)
    lbl = ft.Text("Cada flecha representa un puntero; el último enlaza con el primero.")
    actual = ft.Text(weight=ft.FontWeight.BOLD, size=18)
    enlazado = ft.Text(size=12, color=ft.Colors.BLUE_GREY_700)
    dibujo = ft.AnimatedSwitcher(
        content=ft.Container(content=ft.Text("Cargando recorrido...")),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=350,
        reverse_duration=200,
    )
    boton_play = ft.Button("▶ Recorrer una vuelta", icon=ft.Icons.PLAY_ARROW)
    boton_stop = ft.Button("■ Pausar", icon=ft.Icons.STOP, disabled=True)
    def dibujar():
        paradas = rutas.estado()
        tarjetas = []
        for i, parada in enumerate(paradas):
            tarjetas.append(ft.Container(
                content=ft.Column([
                    ft.Text(f"{parada['indice']:02}", size=12, color=ft.Colors.WHITE if parada['activa'] else ft.Colors.BLUE_GREY_700),
                    ft.Text("🚚 " + parada['nombre'] if parada['activa'] else "📍 " + parada['nombre'],
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if parada['activa'] else ft.Colors.BLUE_GREY_900),
                    ft.Text("VEHÍCULO AQUÍ" if parada['activa'] else "Punto de reparto",
                            size=11, color=ft.Colors.WHITE if parada['activa'] else ft.Colors.BLUE_GREY_600),
                ], tight=True, spacing=3),
                bgcolor=ft.Colors.BLUE_700 if parada['activa'] else ft.Colors.BLUE_GREY_100,
                border_radius=12, padding=14, width=188, animate=250,
            ))
            if i < len(paradas) - 1:
                tarjetas.append(ft.Text("⟷", size=23))
        dibujo.content = ft.Column([
            ft.Row(tarjetas, scroll=ft.ScrollMode.AUTO, spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("↖  cola.prev / cabeza.prev  ⇄  cola.next → cabeza  ↗" if paradas else "Ruta vacía",
                    size=12, color=ft.Colors.BLUE_600),
        ])
        actual.value = f"Vehículo {rutas.vehiculo} · parada actual: {rutas.actual or '—'}"
        enlazado.value = f"{rutas.cantidad} parada(s) · Punteros: {'CORRECTOS ✓' if rutas.verificar_integridad() else 'ERROR ✕'}"
        page.update()
    def agregar(e):
        try:
            rutas.agregar_parada(campo.value)
            lbl.value = "Parada agregada a la cola de la ruta (O(1))."
            campo.value = ""
        except ValueError as ex:
            lbl.value = str(ex)
        dibujar()
    def quitar(e):
        nombre = campo.value.strip()
        if not nombre:
            lbl.value = "Escribe el nombre exacto de la parada a eliminar."
        else:
            lbl.value = "Parada eliminada (búsqueda O(n))." if rutas.quitar_parada(nombre) else "No se encontró esa parada."
            campo.value = ""
        dibujar()
    def paso(direccion):
        if reproduciendo:
            return
        if direccion > 0:
            rutas.siguiente()
        else:
            rutas.anterior()
        dibujar()
    async def recorrer():
        nonlocal reproduciendo
        try:
            for _ in range(rutas.cantidad):
                if not reproduciendo:
                    break
                rutas.siguiente()
                dibujar()
                await asyncio.sleep(0.85)
        finally:
            reproduciendo = False
            boton_play.disabled = False
            boton_stop.disabled = True
            if rutas.cantidad:
                lbl.value = "Recorrido detenido. Puedes avanzar o retroceder manualmente."
            page.update()
    def iniciar(e):
        nonlocal reproduciendo
        if reproduciendo or rutas.cantidad == 0:
            lbl.value = "No hay paradas disponibles." if rutas.cantidad == 0 else lbl.value
            page.update()
            return
        reproduciendo = True
        boton_play.disabled = True
        boton_stop.disabled = False
        page.update()
        page.run_task(recorrer)
    def detener(e):
        nonlocal reproduciendo
        reproduciendo = False
        boton_stop.disabled = True
        page.update()
    boton_play.on_click = iniciar
    boton_stop.on_click = detener
    dibujar()  # Estado inicial también sirve para escritorio, web y móvil.
    return ft.Container(
        padding=16,
        content=ft.Column([
            ft.Text("🚚 Recorrido circular de vehículos", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Lista doblemente enlazada circular: se puede avanzar, retroceder y repetir indefinidamente."),
            ft.ResponsiveRow([
                ft.Container(content=campo, col={"xs": 12, "md": 6}),
                ft.Container(content=ft.Row([
                    ft.Button("+ Agregar", on_click=agregar, icon=ft.Icons.ADD),
                    ft.Button("− Quitar", on_click=quitar, icon=ft.Icons.REMOVE),
                ], wrap=True), col={"xs": 12, "md": 6}),
            ]),
            ft.Row([
                ft.Button("← Anterior", on_click=lambda e: paso(-1)),
                ft.Button("Siguiente →", on_click=lambda e: paso(1)),
                boton_play, boton_stop,
            ], wrap=True, spacing=8),
            lbl, actual, enlazado,
            ft.Divider(), dibujo,
            ft.Text("Modelo: cada nodo guarda dato, prev y next; cola.next = cabeza y cabeza.prev = cola.",
                    size=12, italic=True),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
    )