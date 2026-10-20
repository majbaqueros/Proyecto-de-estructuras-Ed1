import flet as ft
def crear_vista_pila(elementos: list) -> ft.Column:
    """Crea una vista vertical de bloques apilados (Pila)."""
    bloques = []
    for i, elem in enumerate(reversed(elementos)):  # Tope arriba
        bloques.append(
            ft.Container(
                content=ft.Text(str(elem), color="white", weight="bold"),
                bgcolor=ft.Colors.BLUE_600 if i == 0 else ft.Colors.BLUE_300,
                padding=10,
                border_radius=5,
                width=200,
                alignment=ft.Alignment(0, 0)
            )
        )
    return ft.Column(bloques, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)