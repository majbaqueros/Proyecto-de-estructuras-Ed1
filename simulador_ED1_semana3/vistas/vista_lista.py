import flet as ft
def crear_vista_lista(elementos: list) -> ft.Row:
    """Crea nodos con flechas bidireccionales."""
    nodos = []
    for i, elem in enumerate(elementos):
        nodos.append(ft.Container(
            content=ft.Text(str(elem), weight="bold"),
            bgcolor=ft.Colors.PURPLE_300,
            padding=10,
            border_radius=20,
            width=60,
            alignment=ft.Alignment(0, 0)
        ))
        if i < len(elementos) - 1:
            nodos.append(ft.Text("↔", size=20, color="gray"))
    return ft.Row(nodos, scroll=ft.ScrollMode.AUTO, spacing=5)