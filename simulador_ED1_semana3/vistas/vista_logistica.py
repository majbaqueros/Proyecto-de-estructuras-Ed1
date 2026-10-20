import flet as ft
from controlador.app_controller import AppController
from vistas.vista_cola import crear_vista_cola
def crear_tab_logistica(page: ft.Page, controller: AppController) -> ft.Container:
    """Pestaña con el sistema de logística MVC (paquetes)."""
    txt_destino = ft.TextField(label="Destino", width=200)
    txt_peso = ft.TextField(label="Peso (kg)", width=120)
    dd_prioridad = ft.Dropdown(
        label="Prioridad", width=150, value="1",
        options=[
            ft.dropdown.Option("1", "Alta"),
            ft.dropdown.Option("2", "Media"),
            ft.dropdown.Option("3", "Baja"),
        ]
    )
    lbl_mensaje = ft.Text("", color="blue")
    contenedor_cola = ft.Column()
    def actualizar_vistas():
        paquetes = controller.listar_paquetes()
        contenedor_cola.controls = [crear_vista_cola(paquetes)]
        page.update()
    def registrar_paquete(e):
        if txt_destino.value and txt_peso.value:
            try:
                controller.crear_paquete(txt_destino.value, txt_peso.value, dd_prioridad.value)
            except ValueError as error:
                lbl_mensaje.value = f"❌ {error}"
                page.update()
                return
            lbl_mensaje.value = f"✅ Paquete a {txt_destino.value} registrado."
            txt_destino.value = ""
            txt_peso.value = ""
            actualizar_vistas()
    def despachar(e):
        paquete = controller.despachar()
        if paquete:
            lbl_mensaje.value = f"🚚 Paquete {paquete.id} despachado."
        else:
            lbl_mensaje.value = "❌ No hay paquetes pendientes."
        actualizar_vistas()
    def deshacer(e):
        accion = controller.deshacer()
        if accion:
            lbl_mensaje.value = f"↩️ Acción deshecha: {accion[0]}"
        else:
            lbl_mensaje.value = "❌ Nada que deshacer."
        actualizar_vistas()
    contenido = ft.Container(
        content=ft.Column([
            ft.Text("🚚 Sistema de Logística", size=20, weight="bold"),
            ft.Text("Registra paquetes y despáchalos según su prioridad.", italic=True, size=12),
            ft.Row([txt_destino, txt_peso, dd_prioridad], wrap=True),
            ft.Row([
                ft.Button("Registrar Paquete", on_click=registrar_paquete),
                ft.Button("Despachar Siguiente", on_click=despachar),
                ft.Button("↩️ Deshacer", on_click=deshacer),
            ], wrap=True),
            lbl_mensaje,
            ft.Divider(),
            ft.Text("📋 Cola de Prioridad", size=18, weight="bold"),
            contenedor_cola,
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )
    return contenido