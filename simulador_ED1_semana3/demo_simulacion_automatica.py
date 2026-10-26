"""Demostración por terminal del modo automático de ED1.

Ejecutar desde la carpeta del proyecto:
    python demo_simulacion_automatica.py --ciclos 12 --intervalo 0.5

No necesita Flet ni abrir el navegador; ejercita los mismos controladores.
"""
import argparse
import time
from controlador.app_controller import AppController
from logica.simulacion_automatica import SimuladorAutomatico


def main():
    parser = argparse.ArgumentParser(description="Demo de creación/despacho y rutas sin clics")
    parser.add_argument("--ciclos", type=int, default=12, help="Número de ciclos (1-200; por defecto 12)")
    parser.add_argument("--intervalo", type=float, default=0.5, help="Segundos entre ciclos (>= 0)")
    args = parser.parse_args()
    if not 1 <= args.ciclos <= 200 or args.intervalo < 0:
        parser.error("--ciclos debe estar entre 1 y 200; --intervalo no puede ser negativo")

    app = AppController()
    sim = SimuladorAutomatico(app)
    print("\nSIMULACIÓN AUTOMÁTICA ED1 (las operaciones reales pasan por AppController)")
    print("-" * 75)
    try:
        for _ in range(args.ciclos):
            r = sim.paso()
            print(f"[{r.numero:02}] {r.accion:<9} {r.detalle}")
            print(f"     Vehículo: {r.parada} | pendientes: {r.pendientes} | "
                  f"enlaces válidos: {app.rutas.verificar_integridad()}")
            if args.intervalo:
                time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nSimulación pausada por el usuario.")
    m = app.monitor.resumen()
    print("-" * 75)
    print(f"Creados: {sim.creados}; despachados: {sim.despachados}; ciclos: {sim.ciclos}")
    print(f"Operaciones medidas: {m['operaciones']}; "
          f"última operación: {m['ultima_ms']:.3f} ms; "
          f"ops/s: {m['ops_segundo']:.2f}")
    print("Nota: las 4 paradas iniciales también se cuentan entre las operaciones.")


if __name__ == "__main__":
    main()
