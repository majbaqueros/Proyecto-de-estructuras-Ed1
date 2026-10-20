import asyncio
import flet as ft
from controlador.app_controller import AppController
from vistas.vista_estructuras import crear_tab_estructuras
from vistas.vista_logistica import crear_tab_logistica
from vistas.vista_rutas import crear_tab_rutas
from vistas.vista_metricas import crear_tab_metricas
from vistas.vista_extras import crear_tab_extras
async def main(page: ft.Page):
    page.title = "ED1 · Simulador de Estructuras y Logística"
    page.padding = 12
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    controller = AppController()
    vista_metricas, refrescar_metricas = crear_tab_metricas(page, controller)
    vistas = [
        crear_tab_estructuras(page, controller.monitor),
        crear_tab_logistica(page, controller),
        crear_tab_rutas(page, controller),
        vista_metricas,
        crear_tab_extras(page, controller.monitor),
    ]
    nombres = ["Estructuras", "Logística", "Rutas", "Métricas", "Extras"]
    iconos = [ft.Icons.ACCOUNT_TREE, ft.Icons.LOCAL_SHIPPING,
              ft.Icons.ROUTE, ft.Icons.QUERY_STATS, ft.Icons.APPS]
    seleccionado = 0
    espacio = ft.Container(content=vistas[0], expand=True)
    cabecera = ft.Column([
        ft.Text("ED1 · Simulador logístico", size=25, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        ft.Text("Estructuras enlazadas y algoritmos en Python · Semanas 1, 2 y 3", size=12),
    ], spacing=2)
    def seleccionar(indice):
        nonlocal seleccionado
        seleccionado = indice
        espacio.content = vistas[indice]
        if indice == 3:
            refrescar_metricas()
        if page.navigation_bar is not None:
            page.navigation_bar.selected_index = indice
        for pos, boton in enumerate(botones_desktop):
            boton.disabled = (indice == pos)
        page.update()
    botones_desktop = [
        ft.Button(nombre, icon=icono, on_click=lambda e, i=i: seleccionar(i),
                  disabled=i == 0)
        for i, (nombre, icono) in enumerate(zip(nombres, iconos))
    ]
    nav_desktop = ft.Row(botones_desktop, wrap=True, spacing=8)
    # NavigationBar de Flet se ubica como barra inferior nativa en pantallas táctiles.
    def nueva_barra():
        return ft.NavigationBar(
            destinations=[ft.NavigationBarDestination(icon=icono, label=nombre)
                          for icono, nombre in zip(iconos, nombres)],
            selected_index=seleccionado,
            on_change=lambda e: seleccionar(e.control.selected_index),
        )
    def ajustar_layout(e=None):
        ancho = page.width or 900
        movil = ancho < 720
        nav_desktop.visible = not movil
        # Sólo una navegación activa para no desperdiciar altura en teléfono.
        if movil and page.navigation_bar is None:
            page.navigation_bar = nueva_barra()
        elif not movil and page.navigation_bar is not None:
            page.navigation_bar = None
        cabecera.controls[0].size = 19 if movil else 25
        page.update()
    page.add(ft.SafeArea(content=ft.Column([
        cabecera, nav_desktop, ft.Divider(), espacio,
    ], expand=True), expand=True))
    page.on_resize = ajustar_layout
    ajustar_layout()
    # La tasa de operaciones decae realmente con el tiempo incluso si el usuario no pulsa nada.
    async def pulsaciones_metricas():
        while True:
            await asyncio.sleep(1)
            try:
                if seleccionado == 3:
                    refrescar_metricas()
            except (RuntimeError, AssertionError):
                break  # sesión Flet cerrada
    page.run_task(pulsaciones_metricas)
if __name__ == "__main__":
    ft.run(main)