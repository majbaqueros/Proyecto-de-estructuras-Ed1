# Publicación sin Docker: GitHub + Render + PostgreSQL

## 1. Preparación

1. Crear repositorio **privado** en GitHub (puedes subir los archivos con la interfaz web, sin VS Code). El archivo `render.yaml` debe quedar en la **raíz** del repositorio, junto a `main.py`.
2. No subir `.env`, contraseñas, archivos `.sqlite3`, ni `__pycache__`. Mantener `.gitignore`.
3. En Render, acceder a **Blueprints → New Blueprint Instance**, conectar el repositorio, elegir el Blueprint basado en `render.yaml`.
4. Al crear el Blueprint, proporcionar los valores secretos solicitados (nunca guardarlos en GitHub):
   - `ADMIN_BOOTSTRAP_ORG`: nombre de la organización principal, por ejemplo `Empresa Central`.
   - `ADMIN_BOOTSTRAP_EMAIL`: correo del primer administrador.
   - `ADMIN_BOOTSTRAP_PASSWORD`: contraseña larga y única (mínimo 12 caracteres).
   - Render genera `FLET_SECRET_KEY` y suministra `DATABASE_URL` a partir de PostgreSQL.
5. Comprobar que PostgreSQL y el servicio web comienzan correctamente en **Deploy Logs**. Al iniciarse el servicio, `portal/db.py` crea las tablas y el primer administrador una sola vez.
6. **Después del primer inicio exitoso**, eliminar `ADMIN_BOOTSTRAP_PASSWORD` del entorno del servicio y desplegar nuevamente (la cuenta permanece guardada en PostgreSQL). Nunca publicar estas variables en el repositorio.
7. Abrir la URL HTTPS asignada por Render (`https://<nombre-del-servicio>.onrender.com`) e iniciar sesión como administrador.
8. Crear ubicaciones en **Rutas**, obtener en **Cuenta** el código de organización, crear recepcionistas en **Usuarios** y compartir el código únicamente con los clientes autorizados.

## 2. Configuración exacta

`render.yaml` define:

- **Web Service Python**. `buildCommand: pip install -r requirements.txt`; `startCommand: python start_render.py`.
- **PostgreSQL** persistente, `DATABASE_URL` inyectado automáticamente; no Docker.
- Servicio web con host `0.0.0.0` y el `PORT` proporcionado por Render (transferido a `FLET_SERVER_PORT`).
- Flet ejecutado en **modo web dinámico**: el código Python y las contraseñas procesadas permanecen en el servidor, no en el navegador.

Para probar con un PostgreSQL administrado externamente usa la URL `postgresql://usuario:contraseña@host:5432/base` en `DATABASE_URL`; el código la adapta a `psycopg`. Para desarrollo local sin `DATABASE_URL` se utiliza SQLite, pero **nunca en Render**.

## 3. Importante sobre planes y datos

El Blueprint utiliza planes **pagos de nivel inicial**: instancia web `0.5c-512mb` y PostgreSQL `0.1c-256mb`. Revisa precios vigentes antes de crear los servicios. Si usas un plan de PostgreSQL gratuito solo para mostrar el proyecto, recuerda que **Render elimina las bases gratuitas cuando expiran (30 días de vida + período de gracia)** y no incluye backups. No lo uses para conservar pedidos reales.

## 4. Flujo por rol

1. **Administrador** ingresa con cuenta provisionada, crea destinos y recepcionistas, ve la bitácora.
2. **Cliente** elige Registrarme y aporta nombre, correo, contraseña y código de organización. Solo se muestran destinos creados por ese administrador.
3. **Cliente** solicita un paquete; queda `solicitado`.
4. **Recepcionista** revisa solicitudes y aprueba con prioridad 1/2/3 o rechaza.
5. **Recepcionista o administrador** entra en Rutas y recorre una vuelta. Solo al llegar a un destino coincidente se actualiza a `entregado`.
6. **Administrador** consulta la bitácora para rastrear quién hizo cada operación.

## 5. Pruebas finales tras desplegar

- Registrar dos organizaciones separadas (para la segunda, usar temporalmente un nuevo conjunto de valores `ADMIN_BOOTSTRAP_*` en el mismo servicio y redesplegar; retirar la contraseña del entorno después). Verificar aislamiento de destinos y pedidos.
- Desde cuenta de cliente intentar entrar a Bitácora (no debe existir ni acceder a su servicio).
- Ingresar cliente con código de empresa A e intentar enviar a destino exclusivo de B (imposible desde UI y rechazado por servicio).
- Aprobar pedido, recorrer hasta el destino y verificar marca `entregado`.
- Cerrar sesión, volver a entrar y comprobar que la información continúa, ahora persistida en PostgreSQL.
- Verificar que HTTPS funcione, revisar uso de memoria y configurar copias de seguridad y alertas.

## 6. Pendientes para uso real

Recuperación de contraseñas y verificación de correo, bloqueo compartido ante ataques, migraciones versionadas, backups externos, política legal de tratamiento de datos, monitoreo y alertas, autenticación robusta con sesiones persistentes, registro de IP/usuario-agente si se requiere auditoría forense. Estas funcionalidades no están implementadas.

## Referencias oficiales

- Render Web Services: https://render.com/docs/web-services
- Render Blueprint: https://render.com/docs/blueprint-spec
- Render Free limitations: https://render.com/docs/free
- Flet dynamic website: https://flet.dev/docs/publish/web/dynamic-website/
- Flet environment variables: https://flet.dev/docs/reference/environment-variables/
