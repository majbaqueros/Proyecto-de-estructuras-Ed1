"""Prueba interactiva para demostrar validación y entrega por coincidencia.

Ejecutar: python demo_entregas_por_ruta.py
No requiere Flet ni navegador. No guarda cambios persistentes.
"""
from controlador.app_controller import AppController


def main():
    app = AppController()
    app.rutas.agregar_parada("La Paz")
    app.rutas.agregar_parada("SantaCruz")
    print("=== ED1: ENTREGA DE PAQUETES POR ZONA ===")
    print("Paradas:", ", ".join(p["nombre"] for p in app.rutas.estado()))
    print()
    try:
        app.crear_paquete("Tarija", 2, 1)
    except ValueError as ex:
        print("[RECHAZADO] Tarija:", ex)
    print()

    for destino, peso, prioridad in [
        ("la paz", 2.0, 1), ("Zona Norte", 3.0, 3),
        ("santacruz", 1.0, 2),
    ]:
        app.crear_paquete(destino, peso, prioridad)
        print(f"[REGISTRO] {destino} | {peso:g} kg | prioridad {prioridad}")
    print(f"[EN ESPERA] {len(app.listar_paquetes())} paquetes")
    print("[VALIDACIÓN] punteros:", app.rutas.verificar_integridad())
    print()

    for numero in range(app.rutas.cantidad):
        parada, entregados = app.avanzar_y_entregar()
        texto = ", ".join(f"{p.id} → {p.destino}" for p in entregados) or "Ninguno"
        print(f"[PASO {numero + 1}] Vehículo llegó a {parada}")
        print(f"          Entrega: {texto}; pendientes: {len(app.listar_paquetes())}")
    print()
    print("Entregados:", app.total_entregados)
    print("Pendientes:", len(app.listar_paquetes()))
    print("Integridad de la ruta:", app.rutas.verificar_integridad())


if __name__ == "__main__":
    main()
