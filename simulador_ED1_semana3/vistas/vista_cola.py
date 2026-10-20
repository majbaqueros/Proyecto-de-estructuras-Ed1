import flet as ft
def crear_vista_cola(paquetes: list) -> ft.Row:
    """Crea tarjetas horizontales con código de color por prioridad."""
    colores = {1: ft.Colors.RED_400, 2: ft.Colors.ORANGE_400, 3: ft.Colors.GREEN_400}
    tarjetas = []
    for p in paquetes:
        tarjetas.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"📦 {p.id}", weight="bold", color="white"),
                    ft.Text(f"Destino: {p.destino}", size=11, color="white"),
                    ft.Text(f"Peso: {p.peso}kg", size=11, color="white"),
                ]),
                bgcolor=colores.get(p.prioridad, ft.Colors.GREY),
                padding=10,
                border_radius=8,
                width=140
            )
        )
    return ft.Row(tarjetas, scroll=ft.ScrollMode.AUTO, spacing=10)