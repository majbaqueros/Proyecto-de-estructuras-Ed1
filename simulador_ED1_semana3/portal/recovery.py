"""Restablecimiento con OTP hash HMAC almacenado, caducidad y controles SQL persistentes."""
import os
import hmac
import hashlib
import logging
import secrets
from datetime import timedelta, timezone
from sqlalchemy import select, func
from .db import session, utcnow, Usuario, PasswordReset, EventoAuditoria, LoginThrottle
from .security import normalize_email, hash_password

LOG = logging.getLogger(__name__)
MESSAGE = "Si la dirección pertenece a una cuenta, recibirás un código de recuperación."


def _key():
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        if os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("AUTH_SECRET debe tener 32 caracteres o más")
        # Fallback explícitamente restringido a desarrollo; cambia al reiniciar si faltaba env.
        return "ed1-development-secret-not-for-production-2026"
    return secret


def _digest(uid, code):
    return hmac.new(_key().encode(), f"{uid}:{code}".encode(), hashlib.sha256).hexdigest()


def deliver_code(to, code):
    """No registrar el código salvo en desarrollo local con EMAIL_BACKEND=console."""
    mode = os.getenv("EMAIL_BACKEND", "console" if not (os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production") else "").lower().strip()
    if mode == "console" and not (os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production"):
        print(f"[SOLO DESARROLLO] Código de recuperación para {to}: {code}")
        return
    subject = "ED1: código para restablecer tu contraseña"
    message = f"Tu código ED1 es {code}. Caduca en 10 minutos. Si no lo solicitaste, ignora este correo."
    if mode == "resend":
        import httpx
        key = os.environ.get("RESEND_API_KEY", "")
        sender = os.environ.get("MAIL_FROM", "")
        if not (key and sender):
            raise RuntimeError("Configura RESEND_API_KEY y MAIL_FROM")
        response = httpx.post("https://api.resend.com/emails", timeout=10,
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                              json={"from": sender, "to": [to], "subject": subject, "text": message})
        response.raise_for_status()
        return
    if mode == "gmail_smtp" and not os.getenv("VERCEL"):
        from email.message import EmailMessage
        import smtplib
        account = os.environ.get("GMAIL_USER", "")
        password = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not (account and password):
            raise RuntimeError("Faltan GMAIL_USER y GMAIL_APP_PASSWORD")
        mail = EmailMessage()
        mail["From"] = account
        mail["To"] = to
        mail["Subject"] = subject
        mail.set_content(message)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(account, password)
            smtp.send_message(mail)
        return
    raise RuntimeError("Configura EMAIL_BACKEND=resend en producción; consola o gmail_smtp solo en local")


def email_configured():
    """Valida configuración antes de buscar usuarios (no filtra existencia de cuentas)."""
    mode = os.getenv("EMAIL_BACKEND", "console" if not (os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production") else "").lower().strip()
    if mode == "resend":
        return bool(os.getenv("RESEND_API_KEY") and os.getenv("MAIL_FROM"))
    if mode == "gmail_smtp" and not os.getenv("VERCEL"):
        return bool(os.getenv("GMAIL_USER") and os.getenv("GMAIL_APP_PASSWORD"))
    if mode == "console" and not (os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production"):
        return True
    return False


def request_reset(email):
    """No revela si el email existe; limitar por usuario usando PostgreSQL."""
    email = normalize_email(email)
    now = utcnow()
    try:
        return _request_reset_transaction(email, now)
    except Exception:
        LOG.exception("No se pudo enviar o registrar un correo de recuperación")
        return MESSAGE  # No revelar si existe la cuenta


def _request_reset_transaction(email, now):
    with session() as db, db.begin():
        user = db.scalar(select(Usuario).where(Usuario.email == email, Usuario.activo.is_(True)))
        if not user:
            return MESSAGE
        records = db.scalars(select(PasswordReset).where(
            PasswordReset.usuario_id == user.id,
            PasswordReset.creado >= now - timedelta(hours=1)).order_by(PasswordReset.creado.desc())).all()
        if len(records) >= 3 or (records and (now - _aware(records[0].creado)).total_seconds() < 60):
            return MESSAGE
        code = f"{secrets.randbelow(1000000):06d}"
        token = PasswordReset(usuario_id=user.id, codigo_hash=_digest(user.id, code),
                              creado=now, expira=now + timedelta(minutes=10))
        db.add(token)
        # Solo persiste el código si se entregó sin error. No exponer detalles al cliente.
        deliver_code(user.email, code)
        db.add(EventoAuditoria(organizacion_id=user.organizacion_id, usuario_id=user.id,
                              actor_email=user.email, accion="SOLICITAR_RECUPERACION", entidad="usuario",
                              entidad_id=user.id, detalles={"canal":"email"}))
    return MESSAGE


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def confirm_reset(email, code, new_password):
    email = normalize_email(email)
    code = str(code or "").strip()
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        raise ValueError("Código inválido o caducado")
    # Validar la nueva contraseña fuera de la transacción; puede costar tiempo Argon2.
    hashed = hash_password(new_password)
    with session() as db, db.begin():
        user = db.scalar(select(Usuario).where(Usuario.email == email, Usuario.activo.is_(True)))
        if not user:
            raise ValueError("Código inválido o caducado")
        token = db.scalar(select(PasswordReset).where(
            PasswordReset.usuario_id == user.id,
            PasswordReset.utilizado.is_(False)).order_by(PasswordReset.id.desc()).with_for_update())
        if not token or _aware(token.expira) <= utcnow() or token.intentos >= 5:
            raise ValueError("Código inválido o caducado")
        token.intentos += 1
        if not hmac.compare_digest(token.codigo_hash, _digest(user.id, code)):
            # No lanzar dentro de transacción: debe persistir el intento fallido.
            valid = False
        else:
            valid = True
            user.password_hash = hashed
            # Liberar bloqueo anterior tras comprobar la propiedad del correo.
            throttle = db.get(LoginThrottle, hashlib.sha256(email.encode()).hexdigest())
            if throttle:
                db.delete(throttle)
            token.utilizado = True
            # Invalida todos los demás códigos activos.
            pending = db.scalars(select(PasswordReset).where(
                PasswordReset.usuario_id == user.id, PasswordReset.id != token.id,
                PasswordReset.utilizado.is_(False))).all()
            for old in pending:
                old.utilizado = True
            db.add(EventoAuditoria(organizacion_id=user.organizacion_id, usuario_id=user.id,
                                  actor_email=user.email, accion="RESTABLECER_PASSWORD", entidad="usuario",
                                  entidad_id=user.id, detalles={"canal":"email"}))
    if not valid:
        raise ValueError("Código inválido o caducado")
    return "Contraseña actualizada. Inicia sesión nuevamente."
