# ED1 — Plataforma logística web (Vercel y localhost)

Aplicación **FastAPI + HTML/CSS/JavaScript + PostgreSQL externo**. Se ha sustituido el servidor web Flet de la versión anterior porque Vercel ejecuta FastAPI como función web y necesita una instancia `app`. La **lógica Python original** de lista doblemente enlazada circular, cola de prioridad, métricas y reglas por organización se conserva.

## Incluye

- **Administrador:** gestiona ubicaciones; crea recepcionistas; consulta bitácora; ve pedidos, aprueba o rechaza; ejecuta rutas, entregas y métricas.
- **Recepcionista:** ve pedidos de su organización; aprueba y asigna prioridad; avanza los vehículos para entregar los paquetes cuya zona coincide. No tiene acceso a la bitácora ni modifica ubicaciones.
- **Cliente:** se registra con código de organización, inicia sesión, elige **solo destinos disponibles**, solicita envíos y ve sus pedidos.
- **Inicio de sesión seguro:** hash de contraseña Argon2; cookies firmadas HttpOnly (8 h), CSRF para modificaciones, aislamiento por organización en cada consulta y bloqueos de intentos de login guardados en la BD.
- **Olvidé mi contraseña:** solicitud de código de 6 dígitos por correo, válido **10 minutos**, máximo **5 intentos** de confirmación, 1 solicitud/minuto y 3/hora por cuenta; códigos guardados como HMAC, nunca texto plano; al cambiar contraseña se invalidan las sesiones previas.
- **Bitácora:** registros por organización, visibles solo para su administrador. Guarda accesos, solicitudes, decisiones, cambios de paradas, entregas, ejecuciones de benchmark y recuperaciones de contraseña (sin revelar el código).
- **Sin simulación automática de paquetes ni Torres de Hanói.** Permanece el botón **Recorrer una vuelta** para una demostración manual de ruta.

## Estructura del proyecto

```text
main.py                # import de FastAPI app (resuelve FASTAPI_ENTRYPOINT_NOT_FOUND)
app.py                 # API HTTP, sesiones, cookies, permisos y rutas
public/index.html      # interfaz compatible con Chrome, Edge y celular
public/client.js       # interacciones web contra la API
public/style.css       # estilos responsivos
portal/db.py           # tablas SQLAlchemy para PostgreSQL/SQLite local
portal/services.py     # permisos, logística, bitácora, rutas y colas
portal/recovery.py     # códigos de recuperación y envío de correo
portal/security.py     # Argon2, normalización de emails/destinos
estructuras/           # nodos, listas enlazadas, cola de prioridad
logica/metricas.py     # memoria y benchmark O(1) frente a O(n)
crear_admin.py         # alta inicial con clave introducida sin eco
start_local.bat        # acceso local en Windows
requirements.txt       # dependencias del servidor
.env.example           # plantilla de variables (NO subas .env)
tests/                 # pruebas automáticas
```

## A. Ejecutar en localhost — Windows y VS Code

Debes abrir en VS Code **la carpeta interior que contiene `main.py`**, no su carpeta superior. En PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe crear_admin.py
.\.venv\Scripts\python.exe main.py
```

Abre **http://127.0.0.1:8001/**. Si usas Python 3.12, cambia `-3.11` por `-3.12`. También puedes ejecutar `start_local.bat` (instala dependencias antes, ejecuta el servidor; el primer administrador se crea con `crear_admin.py`).

**Por defecto, en local se utiliza SQLite** (`ed1_desarrollo.sqlite3`) sin necesitar PostgreSQL ni Docker. Es un modo de desarrollo, no sustituto de la base persistente para producción. Si quieres probar PostgreSQL local, configura `DATABASE_URL` en `.env` con su cadena de conexión.

### Recuperación de contraseña en localhost

Sin configurar un servicio de correo, **el código de prueba aparece solo en la terminal** (modo `EMAIL_BACKEND=console`), nunca en la respuesta web. Sirve para probar el flujo sin usar Gmail. Para **enviar un email real a Gmail**:

- Usa `EMAIL_BACKEND=resend`, `RESEND_API_KEY` y `MAIL_FROM` con remitente de un **dominio verificado**; o
- Exclusivamente en local, puedes usar `EMAIL_BACKEND=gmail_smtp`, `GMAIL_USER=cuenta@gmail.com`, `GMAIL_APP_PASSWORD` (contraseña de aplicación de Google; no tu contraseña normal). Evita SMTP de Gmail en Vercel.

Para cargar automáticamente un archivo `.env` local, copia `.env.example` a `.env` y edita los valores. NO publiques ese archivo.

## B. Publicar en Vercel (sin instalar nada en los teléfonos)

1. Sube el contenido de **esta carpeta `ED1_Plataforma_Web/`** a un repositorio GitHub. Debe incluir `main.py`, `app.py`, `requirements.txt`, `pyproject.toml`, `public/`, `portal/` y `estructuras/`.
2. En Vercel > **Add New → Project**, importa el repositorio.
3. Si lo subiste como subcarpeta, ajusta **Root Directory: `ED1_Plataforma_Web`**. Si los archivos están en la raíz del repo, deja Root Directory vacío. Selecciona FastAPI como Framework.
4. Crea una **base PostgreSQL externa persistente** (por ejemplo, Neon o Supabase). Vercel por sí solo no suministra una base PostgreSQL persistente con los archivos del repo. Pon la cadena de conexión en `DATABASE_URL` (con SSL conforme indique el proveedor).
5. En **Settings → Environment Variables** configura:

| Variable | Obligatoria | Valor / explicación |
|---|---|---|
| `DATABASE_URL` | Sí | URL de PostgreSQL externo, incluida autenticación y SSL |
| `AUTH_SECRET` | Sí | Clave aleatoria de mínimo 32 caracteres; generar con `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ENVIRONMENT` | Sí | `production` |
| `EMAIL_BACKEND` | Sí | `resend` |
| `RESEND_API_KEY` | Sí para recuperación | API Key de Resend |
| `MAIL_FROM` | Sí para recuperación | Remitente verificado, por ejemplo `ED1 <cuentas@tu-dominio.com>` |
| `ADMIN_BOOTSTRAP_ORG` | Solo primera instalación | Nombre de empresa |
| `ADMIN_BOOTSTRAP_EMAIL` | Solo primera instalación | Correo inicial admin |
| `ADMIN_BOOTSTRAP_PASSWORD` | Solo primera instalación | Contraseña inicial admin (12+ caracteres) |

6. Pulsa **Deploy**. La variable `app` en `main.py` es una instancia de FastAPI; desaparece el error `FASTAPI_ENTRYPOINT_NOT_FOUND` que producía el antiguo archivo Flet.
7. Abre la URL asignada por Vercel. Comprueba `https://tu-dominio.vercel.app/api/health` (debe responder `database: conectada`), inicia sesión como administrador y crea destinos. Luego registra un cliente y prueba el correo de recuperación usando una dirección Gmail real.
8. **Después de crear el admin**, elimina las tres variables `ADMIN_BOOTSTRAP_*` del proyecto y vuelve a desplegar. Nunca incluyas contraseñas reales en los archivos Git.

**Importante:** Cualquier cambio en las variables de Vercel requiere **Redeploy** para afectar a la siguiente versión. Si subes únicamente los archivos antiguos, el error original continuará.

### Nota sobre Gmail

Tu usuario puede **recibir el código en su dirección `@gmail.com`** aun cuando el correo se envía mediante Resend. El remitente, en cambio, debe estar autorizado/verificado en Resend. Sin `RESEND_API_KEY` y `MAIL_FROM` reales no es posible hacer llegar correos externos; el ZIP no trae secretos ni una cuenta de Gmail configurada.

## C. Ejecutar pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Incluye pruebas del inicio de sesión HTTP, cookies, CSRF, separación entre empresas, roles, paquete que se entrega solo en su destino, contraseña olvidada, invalidación de sesiones anteriores y estructuras enlazadas.

## Límites de esta entrega

- El código se ha probado con SQLite temporal y el cliente HTTP de FastAPI; **no se ha desplegado desde aquí en tu cuenta Vercel**, enviado correo real ni validado PostgreSQL remoto. Esos tres puntos requieren credenciales/infraestructura que no vienen en el ZIP.
- Para producción real aplica migraciones Alembic, respaldos de PostgreSQL, observabilidad, WAF/rate limits por IP e inspección de seguridad adicional. Las tablas se crean con SQLAlchemy `create_all` y esta entrega es un MVP educativo.
- La bitácora solo la ve la cuenta administradora a través de la API; un operador con privilegios directos sobre la base de datos puede modificar registros. Para auditoría regulada necesitarías registros inmutables externos.
- En local el contador del benchmark vive en el proceso actual; en Vercel se registra el evento en PostgreSQL. El panel de operaciones por segundo calcula eventos de bitácora de los últimos cinco segundos (no los clics de pantalla).
