import flet as ft
from controlador.callstack_controller import CallStackController
from vistas.vista_pila import crear_vista_pila


def crear_tab_call_stack(page: ft.Page, monitor=None) -> ft.Container:
    llamadas = CallStackController(monitor)
    campo = ft.TextField(label="Nombre de la función", width=205)
    lbl = ft.Text("Pila de llamadas vacía", italic=True)
    dibujo = ft.Container()

    def actualizar():
        elementos = llamadas.estado()
        lbl.value = "Tope → " + " → ".join(elementos) if elementos else "Pila de llamadas vacía"
        dibujo.content = crear_vista_pila(list(reversed(elementos)))
        page.update()

    def llamar(e):
        if campo.value and campo.value.strip():
            llamadas.llamar(campo.value)
            campo.value = ""
            actualizar()

    def retornar(e):
        llamadas.retornar()
        actualizar()

    contenido = ft.Container(content=ft.Column([
        ft.Text("📞 Bitácora de llamadas (Call Stack)", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([campo,
                ft.Button("Llamar función", on_click=llamar),
                ft.Button("Retornar (Pop)", on_click=retornar)], wrap=True),
        lbl, dibujo,
    ], scroll=ft.ScrollMode.AUTO), padding=16)
    actualizar()
    return contenido
