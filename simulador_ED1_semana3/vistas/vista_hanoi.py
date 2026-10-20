import flet as ft
from controlador.hanoi_controller import HanoiController
def crear_tab_hanoi(page: ft.Page, monitor=None) -> ft.Container:
    """Pestaña con el juego de Torres de Hanói."""
    juego = HanoiController(monitor)
    lbl_mensaje_hanoi = ft.Text("", color="blue", weight="bold")
    lbl_movimientos = ft.Text("Movimientos: 0")
    torre_a_visual = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    torre_b_visual = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    torre_c_visual = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    def dibujar_discos(torre: str, contenedor: ft.Column):
        contenedor.controls.clear()
        estado = juego.obtener_estado()
        discos = estado[torre]
        for disco in reversed(discos):
            ancho = disco * 30
            color = (ft.Colors.BLUE_400 if disco == 1
                     else (ft.Colors.GREEN_400 if disco == 2 else ft.Colors.RED_400))
            contenedor.controls.append(
                ft.Container(
                    width=ancho,
                    height=20,
                    bgcolor=color,
                    border_radius=5,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(str(disco), color="white", size=12, weight="bold"),
                )
            )
        contenedor.controls.append(ft.Container(width=100, height=5, bgcolor="black"))
    def actualizar_tablero():
        dibujar_discos("A", torre_a_visual)
        dibujar_discos("B", torre_b_visual)
        dibujar_discos("C", torre_c_visual)
        lbl_movimientos.value = f"Movimientos: {juego.movimientos}"
        if juego.verificar_victoria():
            lbl_mensaje_hanoi.value = "🏆 ¡FELICIDADES! Has ganado."
            lbl_mensaje_hanoi.color = "green"
        page.update()
    dropdown_origen = ft.Dropdown(
        label="Origen", width=100,
        options=[ft.dropdown.Option("A"), ft.dropdown.Option("B"), ft.dropdown.Option("C")],
        value="A"
    )
    dropdown_destino = ft.Dropdown(
        label="Destino", width=100,
        options=[ft.dropdown.Option("A"), ft.dropdown.Option("B"), ft.dropdown.Option("C")],
        value="C"
    )
    def mover_disco_click(e):
        origen = dropdown_origen.value
        destino = dropdown_destino.value
        if origen == destino:
            lbl_mensaje_hanoi.value = "❌ Origen y destino deben ser diferentes."
            lbl_mensaje_hanoi.color = "red"
            page.update()
            return
        exito, mensaje = juego.mover_disco(origen, destino)
        lbl_mensaje_hanoi.value = mensaje
        lbl_mensaje_hanoi.color = "green" if exito else "red"
        actualizar_tablero()
    def reiniciar_hanoi(e):
        juego.reiniciar()
        lbl_mensaje_hanoi.value = "Juego reiniciado."
        lbl_mensaje_hanoi.color = "blue"
        actualizar_tablero()
    btn_mover = ft.Button("Mover Disco", on_click=mover_disco_click)
    btn_reiniciar = ft.Button(
        "Reiniciar", on_click=reiniciar_hanoi,
        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_200)
    )
    tablero_hanoi = ft.Row(
        [
            ft.Column([ft.Text("Torre A", weight="bold"), torre_a_visual],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("Torre B", weight="bold"), torre_b_visual],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("Torre C", weight="bold"), torre_c_visual],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
        wrap=True,
    )
    contenido = ft.Container(
        content=ft.Column([
            ft.Text("🗼 Torres de Hanói (Reto con Pilas)", size=20, weight="bold"),
            ft.Text("Mueve todos los discos de la Torre A a la C.", italic=True, size=12),
            ft.Row([dropdown_origen, dropdown_destino, btn_mover, btn_reiniciar], wrap=True),
            lbl_movimientos,
            lbl_mensaje_hanoi,
            tablero_hanoi,
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )
    # Inicializamos el tablero
    actualizar_tablero()
    return contenido