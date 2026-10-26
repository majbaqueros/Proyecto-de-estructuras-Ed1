"""ED1 Portal multiusuario: Flet web + PostgreSQL, sesiones aisladas por conexión.

No se comparte controlador ni usuario entre las páginas Flet conectadas.
"""
import asyncio
import os
from time import perf_counter
import flet as ft
from portal import services as svc
from portal.db import configure_db
from logica.metricas import MonitorRendimiento, ejecutar_benchmark, estimar_memoria_nodos

configure_db()
# Bootstrap opcional solo para primera instalación: variables protegidas de Render.
if all(os.environ.get(k) for k in ("ADMIN_BOOTSTRAP_ORG", "ADMIN_BOOTSTRAP_EMAIL", "ADMIN_BOOTSTRAP_PASSWORD")):
    svc.bootstrap_admin(os.environ["ADMIN_BOOTSTRAP_ORG"], os.environ["ADMIN_BOOTSTRAP_EMAIL"],
                        os.environ["ADMIN_BOOTSTRAP_PASSWORD"])


async def main(page: ft.Page):
    page.title = "ED1 · Plataforma logística"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 14
    page.scroll = ft.ScrollMode.AUTO
    user = None  # SOLO de esta sesión Flet. Cada cliente tiene un main() independiente.
    selected = "Paquetes"
    notice = ""
    registration = False
    moving = False
    monitor = MonitorRendimiento()
    benchmark_result = ""
    desktop_nav = None

    def is_staff():
        return user is not None and user["rol"] in ("admin", "recepcionista")

    def tabs():
        if not user:
            return []
        return (["Paquetes", "Rutas", "Métricas"] if is_staff() else ["Mis pedidos"]) + (
            ["Usuarios", "Bitácora"] if user["rol"] == "admin" else []) + ["Cuenta"]

    def title(value, size=20):
        return ft.Text(value, weight=ft.FontWeight.BOLD, size=size, color=ft.Colors.BLUE_800)

    def small(value):
        return ft.Text(value, size=12, color=ft.Colors.BLUE_GREY_700)

    def panel(*controls):
        return ft.Container(content=ft.Column(list(controls), spacing=12),
                            padding=16, bgcolor=ft.Colors.BLUE_GREY_50,
                            border_radius=12)

    def button(label, action, icon=None, disabled=False):
        return ft.Button(label, icon=icon, on_click=action, disabled=disabled)

    def notify(message):
        nonlocal notice
        notice = str(message)

    def invoke(action, success="Operación completada"):
        """Todas las operaciones de datos pasan por services, que verifica permisos y tenant."""
        inicio = perf_counter()
        try:
            result = action()
            monitor.registrar(perf_counter() - inicio)
            notify(success if not isinstance(result, str) else result)
            redraw()
            return result
        except (ValueError, PermissionError, RuntimeError) as ex:
            notify("❌ " + str(ex))
            redraw()
            return None
        except Exception:
            notify("Error inesperado. Revisa los registros del servidor.")
            redraw()
            return None

    def login_screen():
        email = ft.TextField(label="Correo electrónico", width=360, keyboard_type=ft.KeyboardType.EMAIL)
        password = ft.TextField(label="Contraseña", width=360, password=True, can_reveal_password=True)
        name = ft.TextField(label="Nombre completo", width=360)
        join_code = ft.TextField(label="Código de organización", width=360)
        data = [title("Acceso a la plataforma", 25),
                small("Cada usuario accede únicamente a los datos autorizados para su organización."),
                email, password]
        if registration:
            data.extend([name, join_code])

        def submit(_):
            nonlocal user, selected, registration, notice
            try:
                if registration:
                    user = svc.sign_up_client(join_code.value, name.value, email.value, password.value)
                else:
                    user = svc.login(email.value, password.value)
                selected = "Paquetes" if user["rol"] != "cliente" else "Mis pedidos"
                registration = False
                notice = "Sesión iniciada correctamente"
            except (ValueError, PermissionError) as ex:
                notice = "❌ " + str(ex)
            redraw()

        def toggle(_):
            nonlocal registration, notice
            registration = not registration
            notice = ""
            redraw()

        data.extend([button("Crear cuenta de cliente" if registration else "Iniciar sesión", submit,
                            ft.Icons.PERSON_ADD if registration else ft.Icons.LOGIN),
                     button("Ya tengo cuenta" if registration else "Registrarme como cliente", toggle),
                     small("Los administradores se crean durante la instalación; solo un administrador puede dar acceso a recepcionistas."),
                     small("Los clientes requieren el código compartido por su administrador.")])
        return ft.Container(content=ft.Column(data, spacing=13), padding=20, width=440,
                            bgcolor=ft.Colors.BLUE_GREY_50, border_radius=16)

    def packages_screen():
        routes = svc.list_routes(user["id"])
        orders = svc.list_orders(user["id"])
        items = [title("Mis solicitudes" if user["rol"] == "cliente" else "Pedidos de la organización"),
                 small("Los clientes solo ven sus propios pedidos. Recepción y administración ven los de su organización.")]
        if user["rol"] == "cliente":
            if routes:
                dest = ft.Dropdown(label="Destino habilitado", width=290,
                                   value=str(routes[0]["id"]),
                                   options=[ft.dropdown.Option(str(r["id"]), r["nombre"]) for r in routes])
                weight = ft.TextField(label="Peso (kg)", value="1", width=135)
                recipient = ft.TextField(label="Destinatario (opcional)", width=270)

                def create(_):
                    invoke(lambda: svc.create_request(user["id"], dest.value, weight.value, recipient.value),
                           "✅ Solicitud registrada; espera aprobación de recepción")

                items.extend([panel(title("Pedir envío", 17),
                                    ft.ResponsiveRow([ft.Container(content=dest,col={"xs":12,"md":5}),
                                                      ft.Container(content=weight,col={"xs":12,"md":3}),
                                                      ft.Container(content=recipient,col={"xs":12,"md":4})]),
                                    button("Solicitar paquete", create, ft.Icons.ADD_BOX))])
            else:
                items.append(ft.Text("Todavía no hay ubicaciones habilitadas por tu administrador."))
        else:
            items.append(small("Aprobar solicita la asignación a la cola priorizada; la entrega se realiza cuando el vehículo llega a la parada."))
        rows = []
        for order in orders:
            textline = (f"#{order['id']} · {order['destino']} · {order['peso']:g} kg · "
                        f"{order['estado'].upper()} · prioridad {order['prioridad']}")
            controls = [ft.Text(textline, weight=ft.FontWeight.W_500)]
            if is_staff() and order["estado"] == "solicitado":
                choice = ft.Dropdown(label="Prioridad", width=140, value="3",
                                     options=[ft.dropdown.Option("1", "Alta"),
                                              ft.dropdown.Option("2", "Media"),
                                              ft.dropdown.Option("3", "Baja")])
                controls.append(ft.Row([
                    choice,
                    button("Aprobar", lambda e, oid=order["id"], ch=choice:
                           invoke(lambda: svc.set_order_status(user["id"], oid, "aprobar", ch.value),
                                  "Paquete aprobado y listo para reparto"), ft.Icons.CHECK),
                    button("Rechazar", lambda e, oid=order["id"]:
                           invoke(lambda: svc.set_order_status(user["id"], oid, "rechazar"),
                                  "Solicitud rechazada"), ft.Icons.CLOSE),
                ], wrap=True))
            rows.append(panel(*controls))
        items.append(title(f"Historial de pedidos ({len(orders)})", 17))
        items.extend(rows if rows else [ft.Text("No hay pedidos registrados todavía.")])
        return ft.Column(items, spacing=13)

    def routes_screen():
        nonlocal moving
        routes = svc.list_routes(user["id"])
        current = svc.current_location(user["id"])
        items = [title("Recorrido circular de vehículos"),
                 small("El recorrido usa una lista doblemente enlazada circular (prev / next). "
                       "Cada paso entrega únicamente los paquetes aprobados para la parada alcanzada."),
                 ft.Text(f"🚚 Vehículo V-001 · Ubicación actual: {current}", size=16, weight=ft.FontWeight.BOLD)]
        cards = [ft.Container(content=ft.Column([
                        ft.Text(f"{i+1:02d} · {r['nombre']}", color=ft.Colors.WHITE if r['nombre']==current else None),
                        small("Vehículo aquí" if r["nombre"] == current else "Parada autorizada")], spacing=4),
                        bgcolor=ft.Colors.BLUE_500 if r["nombre"] == current else ft.Colors.BLUE_GREY_100,
                        border_radius=12, padding=14, width=195)
                 for i,r in enumerate(routes)]
        items.append(ft.Row(cards or [ft.Text("No hay paradas registradas")], scroll=ft.ScrollMode.AUTO))

        def one_step(direction):
            result = invoke(lambda: svc.advance_and_deliver(user["id"], direction), "Ruta actualizada")
            if result:
                notify(f"🚚 {result['ubicacion']} · {len(result['entregados'])} entregas: {result['entregados']}")
                redraw()

        async def loop_once():
            nonlocal moving
            try:
                for _ in range(len(routes)):
                    if not moving or user is None:
                        break
                    result = svc.advance_and_deliver(user["id"])
                    notify(f"🚚 {result['ubicacion']} · paquetes entregados: {result['entregados']}")
                    if selected == "Rutas":
                        redraw()
                    await asyncio.sleep(0.9)
            except Exception as ex:
                notify("Recorrido interrumpido: " + str(ex))
            finally:
                moving = False
                if user and selected == "Rutas":
                    redraw()

        def play(_):
            nonlocal moving
            if not moving and routes:
                moving = True
                page.run_task(loop_once)
                redraw()

        def pause(_):
            nonlocal moving
            moving = False
            redraw()

        items.append(ft.Row([
            button("← Anterior", lambda e: one_step(-1), ft.Icons.ARROW_BACK, disabled=moving),
            button("Siguiente →", lambda e: one_step(1), ft.Icons.ARROW_FORWARD, disabled=moving),
            button("Recorrer una vuelta", play, ft.Icons.PLAY_ARROW, disabled=moving or not routes),
            button("Pausar", pause, ft.Icons.PAUSE, disabled=not moving),
        ], wrap=True))
        if user["rol"] == "admin":
            field = ft.TextField(label="Nueva ubicación disponible", width=280)
            items.extend([ft.Divider(), title("Administrar ubicaciones", 17),
                          ft.Row([field, button("Agregar parada", lambda e:
                                  invoke(lambda: svc.add_route(user["id"], field.value),
                                         "Ubicación agregada"), ft.Icons.ADD)], wrap=True)])
            for r in routes:
                items.append(ft.Row([ft.Text(r["nombre"], width=200),
                                     button("Eliminar (si no tiene pedidos)", lambda e, rid=r["id"]:
                                            invoke(lambda: svc.delete_route(user["id"], rid),
                                                   "Ubicación eliminada"), ft.Icons.DELETE)], wrap=True))
        return ft.Column(items, spacing=14)

    def metrics_screen():
        summary = monitor.resumen()
        count = len(svc.list_routes(user["id"])) + len(svc.list_orders(user["id"]))
        mem = estimar_memoria_nodos(count)
        num = ft.TextField(label="Cantidad de nodos", value="1000", width=190)

        def run_benchmark(_):
            nonlocal benchmark_result
            try:
                r = ejecutar_benchmark(int(num.value))
                svc.record_benchmark(user["id"], r.cantidad, r.ratio)
                benchmark_result = (f"{r.cantidad} operaciones: inserciones O(1) = {r.append_ms:.2f} ms; "
                                    f"búsquedas O(n) = {r.buscar_ms:.2f} ms; relación {r.ratio:.1f}x")
            except (TypeError, ValueError):
                benchmark_result = "Cantidad incorrecta"
            redraw()

        return ft.Column([
            title("Métricas y benchmark de estructuras ED1"),
            small("La medición es de esta sesión; el benchmark no modifica la base de datos."),
            panel(ft.Text(f"Operaciones de esta sesión: {summary['operaciones']}"),
                  ft.Text(f"Operaciones/s (5 s): {summary['ops_segundo']:.2f}"),
                  ft.Text(f"Latencia promedio: {summary['promedio_ms']:.3f} ms")),
            panel(title("Benchmark O(1) frente a O(n)", 17),
                  ft.Row([num, button("Ejecutar benchmark", run_benchmark, ft.Icons.SPEED)], wrap=True),
                  ft.Text(benchmark_result or "Ejecuta una prueba para comparar inserciones y búsquedas"),
                  small("Se realizan N inserciones de costo O(1) y N búsquedas ausentes de costo O(n). "
                        "No se prueba la complejidad con un único tiempo.")),
            panel(title("Memoria aproximada", 17),
                  *[ft.Text(f"{k}: ~{v['bytes_nodo']} B/nodo · ~{v['bytes_total']} B para {count} nodos")
                    for k,v in mem.items()],
                  small("Estimación de CPython; no incluye toda la memoria de Flet ni PostgreSQL.")),
        ], spacing=14)

    def users_screen():
        name = ft.TextField(label="Nombre del recepcionista", width=240)
        email = ft.TextField(label="Correo", width=260)
        password = ft.TextField(label="Contraseña inicial (12+ caracteres)", width=250,
                                password=True, can_reveal_password=True)
        people = svc.list_users(user["id"])
        return ft.Column([
            title("Gestión de usuarios"),
            small("Solo un administrador puede dar de alta recepcionistas. Los clientes se registran con el código de organización."),
            panel(name, email, password,
                  button("Crear recepcionista", lambda e:
                         invoke(lambda: svc.create_receptionist(user["id"], name.value,
                                                                email.value, password.value),
                                "Recepcionista creado"), ft.Icons.PERSON_ADD)),
            title(f"Usuarios de mi organización ({len(people)})", 17),
            *[ft.Text(f"{u['nombre']} · {u['email']} · {u['rol']}") for u in people]
        ], spacing=14)

    def audit_screen():
        logs = svc.audit(user["id"])
        return ft.Column([
            title("Bitácora privada del administrador"),
            small("Registro de ingresos, solicitudes, aprobaciones, rechazos, rutas, entregas y cambios de usuarios."),
            button("Actualizar bitácora", lambda e: redraw(), ft.Icons.REFRESH),
            *[panel(ft.Text(f"#{row['id']} · {row['fecha']} · {row['accion']}", weight=ft.FontWeight.BOLD),
                    small(f"Actor: {row['usuario']} | {row['entidad']} #{row['entidad_id'] or '—'}"),
                    small(f"Detalles: {row['detalles']}")) for row in logs]
        ], spacing=8)

    def account_screen():
        org = svc.organization(user["id"])
        lines = [title("Mi cuenta"), ft.Text(f"Nombre: {user['nombre']}"),
                 ft.Text(f"Correo: {user['email']}"), ft.Text(f"Rol: {user['rol']}"),
                 ft.Text(f"Organización: {org['nombre']}")]
        if user["rol"] == "admin":
            lines.append(panel(title("Código privado de alta de clientes", 17),
                               ft.Text(org["codigo"], selectable=True),
                               small("Comparte este código únicamente con los clientes autorizados a solicitar paquetes en tu organización.")))
        lines.append(button("Cerrar sesión", signout, ft.Icons.LOGOUT))
        return ft.Column(lines, spacing=14)

    def show(tab):
        nonlocal selected, moving
        selected = tab
        if tab != "Rutas":
            moving = False
        redraw()

    def signout(_):
        nonlocal user, selected, notice, moving
        moving = False
        if user:
            try:
                svc.logout(user["id"])
            except (PermissionError, RuntimeError):
                pass
        user = None
        selected = "Paquetes"
        notice = "Sesión cerrada"
        redraw()

    def update_responsive(_=None):
        width = page.width or 900
        narrow = width < 720
        if desktop_nav is not None:
            desktop_nav.visible = not narrow
        if not user:
            page.navigation_bar = None
            return
        if narrow:
            opts = tabs()
            page.navigation_bar = ft.NavigationBar(
                destinations=[ft.NavigationBarDestination(icon=ft.Icons.CIRCLE_OUTLINED, label=name)
                              for name in opts],
                selected_index=opts.index(selected) if selected in opts else 0,
                on_change=lambda e: show(opts[e.control.selected_index]))
        else:
            page.navigation_bar = None

    def redraw():
        nonlocal desktop_nav
        page.controls.clear()
        if not user:
            page.navigation_bar = None
            content = login_screen()
            header = [title("ED1 · Plataforma logística", 27)]
        else:
            opts = tabs()
            if selected not in opts:
                show(opts[0]); return
            desktop_nav = ft.Row([button(name, lambda e, name=name: show(name),
                                     disabled=selected == name) for name in opts] +
                             [button("Salir", signout, ft.Icons.LOGOUT)], wrap=True)
            header = [title("🚚 ED1 · Plataforma logística", 25),
                      small(f"{user['nombre']} · {user['rol']} · datos aislados por organización"),
                      desktop_nav]
            try:
                if selected in ("Paquetes", "Mis pedidos"):
                    content = packages_screen()
                elif selected == "Rutas":
                    content = routes_screen()
                elif selected == "Métricas":
                    content = metrics_screen()
                elif selected == "Usuarios":
                    content = users_screen()
                elif selected == "Bitácora":
                    content = audit_screen()
                else:
                    content = account_screen()
            except (PermissionError, ValueError) as e:
                content = ft.Text("Error de acceso: " + str(e))
        components = (header + ([ft.Text(notice, color=ft.Colors.BLUE_700)] if notice else [])
                      + [ft.Divider(), content])
        page.add(ft.SafeArea(content=ft.Column(components, spacing=12, scroll=ft.ScrollMode.AUTO,
                                            expand=True), expand=True))
        update_responsive()
        page.update()

    def resized(_):
        update_responsive()
        page.update()

    page.on_resize = resized
    redraw()


if __name__ == "__main__":
    ft.run(main)
