"""UI de listas/validador/postfijo. Ningún acceso a punteros aquí."""
import flet as ft
from controlador.estructuras_controller import EstructurasController
from pipeline.validador import validar_parentesis, evaluar_postfija
from vistas.vista_lista import crear_vista_lista


def crear_tab_estructuras(page: ft.Page, monitor=None) -> ft.Container:
    lista = EstructurasController(monitor)
    txt_lista = ft.TextField(label="Valor a insertar / eliminar", width=205)
    lbl_lista = ft.Text("Lista: []")
    lienzo_lista = ft.Column()
    lbl_apuntadores = ft.Text("cabeza: None · cola: None", size=12)
    lbl_mensaje = ft.Text("", size=12)
    btn_deshacer = ft.Button("Deshacer", disabled=True)
    btn_rehacer = ft.Button("Rehacer", disabled=True)

    def actualizar_lista_ui():
        estado = lista.estado()
        lbl_lista.value = "Lista: [" + " <-> ".join(estado['elementos']) + "]"
        lienzo_lista.controls = [crear_vista_lista(estado['elementos'])]
        lbl_apuntadores.value = (
            f"cabeza: {estado['cabeza']} · cola: {estado['cola']} · "
            f"nodos: {estado['tamano']} · integridad: {'✓' if estado['integridad'] else '✕'}"
        )
        btn_deshacer.disabled = not estado['undo']
        btn_rehacer.disabled = not estado['redo']
        page.update()

    def insertar(extremo):
        try:
            lista.insertar(txt_lista.value or "", extremo)
            lbl_mensaje.value = f"Insertado al {extremo}."
            txt_lista.value = ""
        except ValueError as err:
            lbl_mensaje.value = str(err)
        actualizar_lista_ui()

    def eliminar(e):
        ok = lista.eliminar(txt_lista.value or "")
        lbl_mensaje.value = "Eliminado." if ok else "No existe el valor indicado."
        if ok:
            txt_lista.value = ""
        actualizar_lista_ui()

    def deshacer(e):
        lista.deshacer()
        actualizar_lista_ui()

    def rehacer(e):
        lista.rehacer()
        actualizar_lista_ui()

    btn_deshacer.on_click = deshacer
    btn_rehacer.on_click = rehacer
    txt_validador = ft.TextField(label="Expresión matemática/código", width=300)
    lbl_resultado = ft.Text("")

    def validar(e):
        resultado = validar_parentesis(txt_validador.value or "")
        lbl_resultado.value = "✅ Válido" if resultado else "❌ Inválido"
        lbl_resultado.color = "green" if resultado else "red"
        page.update()

    txt_postfija = ft.TextField(label="Expresión Postfija (ej: 3 4 + 5 *)", width=285)
    lbl_postfija = ft.Text("")

    def evaluar(e):
        try:
            lbl_postfija.value = f"Resultado: {evaluar_postfija(txt_postfija.value or '')}"
            lbl_postfija.color = "green"
        except Exception:
            lbl_postfija.value = "❌ Expresión postfija inválida"
            lbl_postfija.color = "red"
        page.update()

    contenido = ft.Container(content=ft.Column([
        ft.Text("🔗 Lista doblemente enlazada", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([
            txt_lista,
            ft.Button("Insertar inicio", on_click=lambda e: insertar("inicio")),
            ft.Button("Insertar final", on_click=lambda e: insertar("final")),
            ft.Button("Eliminar valor", on_click=eliminar),
        ], wrap=True),
        ft.Row([btn_deshacer, btn_rehacer], wrap=True),
        lbl_lista, lbl_apuntadores, lbl_mensaje,
        ft.Text("cabeza →  prev ↔ nodo ↔ next  ← cola", color=ft.Colors.PURPLE_700, size=12),
        lienzo_lista, ft.Divider(),
        ft.Text("🧮 Validador de paréntesis", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([txt_validador, ft.Button("Validar", on_click=validar)], wrap=True),
        lbl_resultado, ft.Divider(),
        ft.Text("🧮 Evaluador postfijo", size=20, weight=ft.FontWeight.BOLD),
        ft.Text("Números separados por espacio y operadores: + - * /", italic=True, size=12),
        ft.Row([txt_postfija, ft.Button("Evaluar", on_click=evaluar)], wrap=True),
        lbl_postfija,
    ], scroll=ft.ScrollMode.AUTO), padding=16)
    actualizar_lista_ui()
    return contenido
