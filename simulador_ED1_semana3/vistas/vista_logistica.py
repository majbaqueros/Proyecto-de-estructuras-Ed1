"""Logística MVC con demostración manual y simulación automática pausada/continua."""
import asyncio
import flet as ft
from controlador.app_controller import AppController
from logica.simulacion_automatica import SimuladorAutomatico
from vistas.vista_cola import crear_vista_cola


def crear_tab_logistica(page: ft.Page, controller: AppController, on_rutas_actualizadas=None,
                       devolver_actualizar=False):
    """Muestra la cola real de prioridad; el modo auto usa AppController."""
    txt_destino = ft.TextField(label="Destino", width=200)
    txt_peso = ft.TextField(label="Peso (kg)", width=120)
    dd_prioridad = ft.Dropdown(
        label="Prioridad", width=150, value="1",
        options=[
            ft.dropdown.Option("1", "Alta"),
            ft.dropdown.Option("2", "Media"),
            ft.dropdown.Option("3", "Baja"),
        ],
    )
    lbl_mensaje = ft.Text("", color=ft.Colors.BLUE_700)
    destinos_disponibles = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_700)
    contenedor_cola = ft.Column()

    def actualizar_vistas():
        paquetes = controller.listar_paquetes()
        contenedor_cola.controls = [crear_vista_cola(paquetes)]
        destinos_disponibles.value = ("Destinos habilitados: " +
                                     ", ".join(parada["nombre"] for parada in controller.rutas.estado()))
        page.update()

    def registrar_paquete(e):
        if not txt_destino.value or not txt_peso.value:
            lbl_mensaje.value = "Escribe un destino y un peso para registrar."
            page.update()
            return
        try:
            controller.crear_paquete(txt_destino.value, txt_peso.value, dd_prioridad.value)
        except ValueError as error:
            lbl_mensaje.value = f"❌ {error}"
            page.update()
            return
        lbl_mensaje.value = f"✅ Paquete a {controller.rutas.destino_canonico(txt_destino.value)} registrado. Se entregará al llegar el vehículo."
        txt_destino.value = ""
        txt_peso.value = ""
        actualizar_vistas()

    def despachar(e):
        paquete = controller.despachar()
        lbl_mensaje.value = (f"✅ {paquete.id} entregado en {controller.rutas.actual}." if paquete
                             else f"No hay paquetes para entregar en {controller.rutas.actual or 'ninguna parada'}. "
                                  "Avanza el vehículo para repartir en otra zona.")
        actualizar_vistas()

    def deshacer(e):
        accion = controller.deshacer()
        lbl_mensaje.value = (f"↩️ Acción deshecha: {accion[0]}" if accion
                             else "❌ Nada que deshacer.")
        actualizar_vistas()

    # --- Semana 3: eventos autónomos, sin introducir otra cola ni otros punteros. ---
    sim = SimuladorAutomatico(controller)
    activo = False
    version = 0  # Evita que dos bucles queden activos al pausar y reiniciar.
    intervalo = ft.Dropdown(
        label="Intervalo entre ciclos", width=185, value="1.5",
        options=[ft.dropdown.Option("1.0", "1 segundo"),
                 ft.dropdown.Option("1.5", "1,5 segundos"),
                 ft.dropdown.Option("3.0", "3 segundos")],
    )
    estado_auto = ft.Text("Estado: detenido", color=ft.Colors.BLUE_GREY_700)
    estadisticas_auto = ft.Text("0 creados · 0 despachados · 0 ciclos")
    ultimo_auto = ft.Text("Presiona Iniciar o Ejecutar un ciclo.")
    historial_auto = ft.Column(spacing=4)
    boton_iniciar = ft.Button("▶ Iniciar simulación", icon=ft.Icons.PLAY_ARROW)
    boton_pausar = ft.Button("⏸ Pausar", icon=ft.Icons.PAUSE, disabled=True)
    boton_un_paso = ft.Button("⚡ Un ciclo", icon=ft.Icons.SKIP_NEXT)

    def ejecutar_paso():
        resultado = sim.paso()
        estadisticas_auto.value = (
            f"{resultado.creados} creados · {resultado.despachados} despachados · "
            f"{resultado.numero} ciclos · {resultado.pendientes} pendientes"
        )
        ultimo_auto.value = f"{resultado.accion}: {resultado.detalle} | Vehículo: {resultado.parada or '—'}"
        historial_auto.controls.insert(0, ft.Text(
            f"#{resultado.numero:02d} · {resultado.accion} · {resultado.detalle}", size=12,
        ))
        # Es un historial VISUAL acotado, no la estructura que guarda paquetes.
        del historial_auto.controls[7:]
        actualizar_vistas()
        if on_rutas_actualizadas is not None:
            on_rutas_actualizadas()

    def un_paso(e):
        if activo or controller.recorrido_manual_activo:
            if controller.recorrido_manual_activo:
                estado_auto.value = "Espera a que termine o pausa la vuelta de Rutas."
                page.update()
            return
        ejecutar_paso()

    def iniciar(e):
        nonlocal activo, version
        if activo:
            return
        if controller.recorrido_manual_activo:
            estado_auto.value = "Detén primero el recorrido manual desde Rutas."
            page.update()
            return
        activo = True
        controller.simulacion_activa = True
        version += 1
        turno = version
        estado_auto.value = "Estado: ejecución automática activa"
        boton_iniciar.disabled = True
        boton_pausar.disabled = False
        boton_un_paso.disabled = True
        page.update()

        async def bucle():
            nonlocal activo
            try:
                while activo and turno == version:
                    ejecutar_paso()
                    await asyncio.sleep(float(intervalo.value or "1.5"))
            except (RuntimeError, AssertionError):
                # Vista/página cerrada; no se siguen enviando actualizaciones.
                pass
            finally:
                if turno == version:
                    activo = False
                    controller.simulacion_activa = False
                    estado_auto.value = "Estado: detenido"
                    boton_iniciar.disabled = False
                    boton_pausar.disabled = True
                    boton_un_paso.disabled = False
                    try:
                        page.update()
                    except (RuntimeError, AssertionError):
                        pass

        page.run_task(bucle)

    def pausar(e):
        nonlocal activo, version
        activo = False
        controller.simulacion_activa = False
        version += 1
        estado_auto.value = "Estado: pausado (puedes continuar cuando quieras)"
        boton_iniciar.disabled = False
        boton_pausar.disabled = True
        boton_un_paso.disabled = False
        page.update()

    boton_iniciar.on_click = iniciar
    boton_pausar.on_click = pausar
    boton_un_paso.on_click = un_paso

    contenido = ft.Container(
        content=ft.Column([
            ft.Text("🚚 Sistema de Logística", size=20, weight="bold"),
            ft.Text("Solo se registran paquetes para paradas existentes. Se entregan cuando el vehículo llega a su destino.", italic=True, size=12),
            destinos_disponibles,
            ft.Row([txt_destino, txt_peso, dd_prioridad], wrap=True),
            ft.Row([
                ft.Button("Registrar Paquete", on_click=registrar_paquete),
                ft.Button("Entregar en parada actual", on_click=despachar),
                ft.Button("↩️ Deshacer", on_click=deshacer),
            ], wrap=True),
            lbl_mensaje,
            ft.Divider(),
            ft.Text("🤖 Modo de simulación automática", size=19, weight="bold"),
            ft.Text("Carga dos paquetes con destinos de la ruta cuando no hay pendientes; "
                    "avanza una parada por ciclo y entrega solo al llegar a la zona. "
                    "La prioridad decide el orden de entrega entre paquetes de la misma zona.", size=12),
            ft.Row([intervalo, boton_iniciar, boton_pausar, boton_un_paso], wrap=True),
            estado_auto, estadisticas_auto, ultimo_auto,
            ft.Text("Eventos recientes", weight=ft.FontWeight.BOLD),
            historial_auto,
            ft.Divider(),
            ft.Text("📋 Cola de Prioridad", size=18, weight="bold"),
            contenedor_cola,
        ], scroll=ft.ScrollMode.AUTO),
        padding=20,
    )
    actualizar_vistas()
    return (contenido, actualizar_vistas) if devolver_actualizar else contenido
