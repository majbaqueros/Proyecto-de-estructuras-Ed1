"""Presenta los dos módulos de semanas previas con navegación táctil sencilla."""
import flet as ft
from vistas.vista_call_stack import crear_tab_call_stack
from vistas.vista_hanoi import crear_tab_hanoi


def crear_tab_extras(page, monitor=None):
    callstack = crear_tab_call_stack(page, monitor)
    hanoi = crear_tab_hanoi(page, monitor)
    espacio = ft.Container(content=callstack, expand=True)
    def ir(nombre):
        espacio.content = callstack if nombre == "calls" else hanoi
        page.update()
    return ft.Container(content=ft.Column([
        ft.Text("🧩 Laboratorio complementario", size=22, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.Button("Call Stack", on_click=lambda e: ir("calls"), icon=ft.Icons.CALL),
            ft.Button("Torres de Hanói", on_click=lambda e: ir("hanoi"), icon=ft.Icons.GAMES),
        ], wrap=True),
        espacio,
    ], expand=True, scroll=ft.ScrollMode.AUTO))
