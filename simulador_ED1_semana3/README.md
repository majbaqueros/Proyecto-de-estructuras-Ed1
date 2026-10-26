# ED1 — Plataforma logística multiusuario (Web)

Reorganización del proyecto de las tres semanas: **Python + Flet (sitio dinámico) + PostgreSQL + Render**. Los usuarios entran mediante navegador web. El sistema no requiere instalar VS Code, PostgreSQL o Docker en el equipo del cliente.

## Funcionalidades

| Rol | Acciones |
|---|---|
| Administrador | Inicia sesión; gestiona ubicaciones de su organización; crea recepcionistas; obtiene código de registro de clientes; consulta los pedidos de su organización; aprueba o rechaza solicitudes; ejecuta rutas y benchmark; ve la bitácora privada. |
| Recepcionista | Inicia sesión; consulta los pedidos de su organización; aprueba/rechaza solicitudes y asigna prioridad; recorre rutas y realiza entregas al llegar a cada zona; consulta métricas. **No accede a la bitácora ni cambia ubicaciones.** |
| Cliente | Se registra usando el **código de organización** que le entrega el administrador, inicia sesión, consulta las ubicaciones habilitadas, solicita paquetes y ve **únicamente sus propios pedidos**. |

### Estado de un paquete

`solicitado` (cliente) → `aprobado` (recepcionista/admin) → `entregado` (cuando el vehículo llega a su destino). El recepcionista puede `rechazar` una solicitud pendiente.

- El cliente **no puede elegir un destino ajeno** ni elevar la prioridad. La prioridad solo la asigna recepción/admin al aprobar, 1=alta, 2=media, 3=baja.
- El administrador controla la lista de rutas; los nombres se normalizan para evitar duplicados como `La Paz` y `la paz`.
- La ruta se reconstruye como **lista doblemente enlazada circular**, a partir de las ubicaciones persistentes en PostgreSQL, y el reparto de paquetes aprobados se decide mediante una **cola de prioridad enlazada**. El pedido solo se marca como `entregado` en la zona de destino.
- Todos los cambios relevantes (altas, accesos, solicitudes, aprobaciones, rechazos, rutas, entregas y ejecución de benchmark) generan eventos en la **bitácora**, consultable únicamente por administradores de la organización.
- No se incluyen la simulación automática ni Torres de Hanói.

## Estructura

```text
main.py                 Interfaz Flet, inicio de sesión y paneles según rol
portal/db.py            Modelos SQLAlchemy de PostgreSQL: organizaciones, usuarios,
                        paradas, paquetes y bitácora
portal/security.py      Hash Argon2 de contraseñas y normalización
portal/services.py      Reglas, validaciones, permisos, aislamiento entre organizaciones,
                        rutas y registro de auditoría
estructuras/            Listas, cola enlazada priorizada y pilas construidas manualmente
logica/metricas.py      Benchmark O(1) frente a O(n) y cálculo de memoria
start_render.py         Adapta el PORT de Render al servidor Flet
render.yaml             Blueprint de Render (Web Service + PostgreSQL)
tests/test_portal.py    Pruebas de roles, restricciones, entregas y multiempresa
```

## Ejecutar en desarrollo local (solo quien desarrolla)

Es posible probar sin instalar PostgreSQL **solo en desarrollo**: si falta `DATABASE_URL`, el proyecto utiliza SQLite local `ed1_desarrollo.sqlite3`. **Render no acepta ese fallback: exige PostgreSQL**.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Crear administrador inicial desde Python (evita guardar contraseñas reales en el código):

```powershell
.\.venv\Scripts\python.exe crear_admin.py
```

Luego iniciar:

```powershell
.\.venv\Scripts\flet.exe run --web --port 8001 main.py
```

Entrar en `http://127.0.0.1:8001` con el correo y contraseña definidos en el paso anterior. En **Cuenta**, el administrador verá el código de registro para los clientes.

Pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Publicar en Render

Lee **`docs/DESPLIEGUE_RENDER.md`**. El archivo `render.yaml` crea el servicio web y PostgreSQL. Los usuarios solo necesitarán la dirección `https://<tu-servicio>.onrender.com` que Render asigne **después** del despliegue: este paquete no está publicado aún.

## Limitaciones importantes antes de ponerlo en producción

- Es un **MVP educativo**, no un sistema de producción auditado. El inicio de sesión es por sesión Flet; al recargar/reabrir podría solicitar iniciar sesión nuevamente. No incluye verificación de correo, recuperación de contraseña, segundo factor, políticas de retención de datos ni confirmación de recepción por destinatario.
- La limitación de intentos de login es local al proceso. Si se usan varios workers o instancias debe trasladarse a un almacenamiento compartido (Redis). No existe un WAF configurado.
- Las tablas se crean con `Base.metadata.create_all()`. Para upgrades de producción se requieren **migraciones Alembic**, respaldos, monitoreo y procedimientos de restauración.
- La bitácora no tiene pantalla para modificar/borrar eventos, pero **no es una bitácora criptográficamente inmutable** frente a un administrador de la base de datos.
- Solo se validaron las reglas de negocio con **SQLite de prueba**; no se validó conexión real a PostgreSQL ni la interfaz Flet en el servidor Render en este entorno. Comprobar ambas antes de invitar usuarios reales.
- Este diseño es por organización (tenant): administradores diferentes no comparten datos, y los clientes ven sus propios pedidos.
