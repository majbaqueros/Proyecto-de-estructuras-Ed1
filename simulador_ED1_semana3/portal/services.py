"""Reglas de negocio multiusuario. Toda consulta privada comprueba tenant y permisos aquí.

La interfaz no recibe nunca una sesión SQLAlchemy ni acceso directo al repositorio.
"""
import secrets
import hashlib
from datetime import timedelta, timezone
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from .db import (session, Organizacion, Usuario, Parada, PaqueteDB, EventoAuditoria, LoginThrottle,
                 utcnow)
from .security import hash_password, check_password, normalize_email, normalize_place
from estructuras.lista_circular_doble import ListaDoblementeCircular
from estructuras.colas import PriorityQueue

ROLES = {"admin", "recepcionista", "cliente"}


def _actor(db, user_id, allowed=None):
    user = db.get(Usuario, user_id)
    if not user or not user.activo:
        raise PermissionError("Cuenta no autorizada")
    if allowed is not None and user.rol not in allowed:
        raise PermissionError("No tienes permisos para realizar esta acción")
    return user


def _log(db, actor, action, subject, subject_id=None, details=None):
    db.add(EventoAuditoria(organizacion_id=actor.organizacion_id, usuario_id=actor.id,
                          actor_email=actor.email, accion=action, entidad=subject,
                          entidad_id=subject_id, detalles=details or {}))


def _public_user(user):
    return dict(id=user.id, nombre=user.nombre, email=user.email,
                rol=user.rol, organizacion_id=user.organizacion_id)


def _route(p):
    return dict(id=p.id, nombre=p.nombre, orden=p.orden)


def _parcel(p, destination):
    return dict(id=p.id, destino_id=p.destino_id, destino=destination,
                solicitante_id=p.solicitante_id, peso=p.peso, prioridad=p.prioridad,
                estado=p.estado, destinatario=p.destinatario, creado=p.creado.isoformat())


def bootstrap_admin(org_name, email, password, admin_name="Administrador"):
    """Para primera instalación; NO crea un segundo admin si ese correo existe."""
    email = normalize_email(email)
    digest = hash_password(password)
    if not org_name.strip() or len(org_name.strip()) > 120:
        raise ValueError("Nombre de organización incorrecto")
    with session() as db, db.begin():
        previous = db.scalar(select(Usuario).where(Usuario.email == email))
        if previous:
            if previous.rol != "admin":
                raise ValueError("El correo ya está registrado con otro rol")
            return None
        org = Organizacion(nombre=org_name.strip(), codigo=secrets.token_urlsafe(12))
        db.add(org)
        db.flush()
        user = Usuario(organizacion_id=org.id, nombre=admin_name[:100], email=email,
                       rol="admin", password_hash=digest)
        db.add(user)
        db.flush()
        _log(db, user, "CREAR_ORGANIZACION", "organizacion", org.id, {"nombre":org.nombre})
        _log(db, user, "CREAR_ADMIN", "usuario", user.id)
        return _public_user(user)


def login(email, password):
    """Límite de intentos persistente en PostgreSQL, válido entre funciones Vercel."""
    normalized = normalize_email(email)
    key = hashlib.sha256(normalized.encode()).hexdigest()
    now = utcnow()
    failed = False
    blocked = False
    result = None
    with session() as db, db.begin():
        throttle = db.scalar(select(LoginThrottle).where(LoginThrottle.key == key).with_for_update())
        if throttle:
            since = throttle.inicio_ventana
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            if now - since >= timedelta(minutes=10):
                throttle.fallos = 0
                throttle.inicio_ventana = now
                throttle.bloqueado_hasta = None
            until = throttle.bloqueado_hasta
            if until and until.tzinfo is None:
                until = until.replace(tzinfo=timezone.utc)
            if until and until > now:
                blocked = True
        if not blocked:
            user = db.scalar(select(Usuario).where(Usuario.email == normalized))
            if not user or not user.activo or not check_password(user.password_hash, password):
                failed = True
                if not throttle:
                    throttle = LoginThrottle(key=key, fallos=0, inicio_ventana=now)
                    db.add(throttle)
                throttle.fallos += 1
                if throttle.fallos >= 5:
                    throttle.bloqueado_hasta = now + timedelta(minutes=10)
                if user:
                    _log(db, user, "LOGIN_FALLIDO", "usuario", user.id)
            else:
                if throttle:
                    db.delete(throttle)
                _log(db, user, "LOGIN_CORRECTO", "usuario", user.id)
                result = _public_user(user)
    if blocked:
        raise ValueError("Demasiados intentos. Vuelve a probar en 10 minutos")
    if failed:
        raise ValueError("Correo o contraseña incorrectos")
    return result

def logout(user_id):
    with session() as db, db.begin():
        user = _actor(db, user_id)
        _log(db, user, "CERRAR_SESION", "usuario", user.id)


def org_join_info(code):
    with session() as db:
        org = db.scalar(select(Organizacion).where(Organizacion.codigo == code.strip()))
        if not org:
            raise ValueError("Código de organización inválido")
        return org.nombre


def sign_up_client(code, name, email, password):
    normalized = normalize_email(email)
    digest = hash_password(password)
    if not (2 <= len(name.strip()) <= 100):
        raise ValueError("Nombre entre 2 y 100 caracteres")
    with session() as db, db.begin():
        org = db.scalar(select(Organizacion).where(Organizacion.codigo == code.strip()))
        if org is None:
            raise ValueError("La organización no existe")
        user = Usuario(organizacion_id=org.id, nombre=name.strip(), email=normalized,
                       password_hash=digest, rol="cliente")
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            raise ValueError("Ese correo ya está registrado") from None
        _log(db, user, "ALTA_CLIENTE", "usuario", user.id)
        return _public_user(user)


def create_receptionist(admin_id, name, email, password):
    normalized = normalize_email(email)
    digest = hash_password(password)
    if not (2 <= len(name.strip()) <= 100):
        raise ValueError("Nombre entre 2 y 100 caracteres")
    with session() as db, db.begin():
        admin = _actor(db, admin_id, {"admin"})
        u = Usuario(organizacion_id=admin.organizacion_id, nombre=name.strip(),
                    email=normalized, password_hash=digest, rol="recepcionista")
        db.add(u)
        try:
            db.flush()
        except IntegrityError:
            raise ValueError("Ese correo ya está registrado") from None
        _log(db, admin, "CREAR_RECEPCIONISTA", "usuario", u.id, {"email": u.email})
        return _public_user(u)


def organization(user_id):
    with session() as db:
        u = _actor(db, user_id)
        org = db.get(Organizacion, u.organizacion_id)
        result = {"id": org.id, "nombre": org.nombre}
        if u.rol == "admin":
            result["codigo"] = org.codigo
        return result


def list_routes(user_id):
    with session() as db:
        u = _actor(db, user_id)
        routes = db.scalars(select(Parada).where(Parada.organizacion_id == u.organizacion_id)
                            .order_by(Parada.orden, Parada.id)).all()
        return [_route(p) for p in routes]


def add_route(admin_id, name):
    name, key = normalize_place(name)
    with session() as db, db.begin():
        admin = _actor(db, admin_id, {"admin"})
        # Bloqueo de tenant para serializar orden/inserciones/recorridos sobre PostgreSQL.
        org = db.scalar(select(Organizacion).where(Organizacion.id == admin.organizacion_id).with_for_update())
        exists = db.scalar(select(Parada.id).where(Parada.organizacion_id == org.id, Parada.clave == key))
        if exists:
            raise ValueError("Ya existe esa ubicación")
        highest = db.scalar(select(func.max(Parada.orden)).where(Parada.organizacion_id == org.id)) or 0
        p = Parada(organizacion_id=org.id, nombre=name, clave=key, orden=highest+1)
        db.add(p)
        db.flush()
        _log(db, admin, "AGREGAR_PARADA", "parada", p.id, {"nombre": p.nombre})
        return _route(p)


def delete_route(admin_id, route_id):
    with session() as db, db.begin():
        admin = _actor(db, admin_id, {"admin"})
        org = db.scalar(select(Organizacion).where(Organizacion.id == admin.organizacion_id).with_for_update())
        p = db.scalar(select(Parada).where(Parada.id == route_id, Parada.organizacion_id == org.id))
        if not p:
            raise ValueError("Parada inexistente")
        # Conservación del historial de entregas: no borrar rutas con pedidos asociados.
        has_package = db.scalar(select(PaqueteDB.id).where(PaqueteDB.organizacion_id == org.id,
                                                          PaqueteDB.destino_id == p.id).limit(1))
        if has_package:
            raise ValueError("No se puede eliminar una ubicación con pedidos registrados, incluso entregados")
        if org.parada_actual_id == p.id:
            org.parada_actual_id = None
        _log(db, admin, "ELIMINAR_PARADA", "parada", p.id, {"nombre": p.nombre})
        db.delete(p)


def create_request(client_id, route_id, weight, recipient=""):
    try:
        weight = float(weight)
    except (ValueError, TypeError):
        raise ValueError("Peso inválido") from None
    if not (0 < weight <= 10000):
        raise ValueError("Peso entre 0 y 10000 kg")
    recipient = (recipient or "").strip()
    if len(recipient) > 120:
        raise ValueError("Nombre del destinatario demasiado largo")
    with session() as db, db.begin():
        client = _actor(db, client_id, {"cliente"})
        route = db.scalar(select(Parada).where(Parada.id == int(route_id),
                                              Parada.organizacion_id == client.organizacion_id))
        if not route:
            raise ValueError("Destino no habilitado por este administrador")
        p = PaqueteDB(organizacion_id=client.organizacion_id, solicitante_id=client.id,
                      destino_id=route.id, peso=weight, destinatario=recipient, prioridad=3,
                      estado="solicitado")
        db.add(p)
        db.flush()
        _log(db, client, "SOLICITAR_PAQUETE", "paquete", p.id,
             {"destino":route.nombre, "peso":weight})
        return p.id


def list_orders(user_id):
    with session() as db:
        u = _actor(db, user_id)
        stmt = select(PaqueteDB, Parada.nombre).join(Parada, Parada.id == PaqueteDB.destino_id).where(
            PaqueteDB.organizacion_id == u.organizacion_id, Parada.organizacion_id == u.organizacion_id)
        if u.rol == "cliente":
            stmt = stmt.where(PaqueteDB.solicitante_id == u.id)
        stmt = stmt.order_by(PaqueteDB.id.desc())
        return [_parcel(p, dest) for p, dest in db.execute(stmt).all()]


def set_order_status(staff_id, package_id, action, priority=3):
    if action not in ("aprobar", "rechazar"):
        raise ValueError("Acción desconocida")
    if action == "aprobar":
        priority = int(priority)
        if priority not in (1, 2, 3):
            raise ValueError("Prioridad debe ser 1, 2 o 3")
    with session() as db, db.begin():
        staff = _actor(db, staff_id, {"admin", "recepcionista"})
        p = db.scalar(select(PaqueteDB).where(PaqueteDB.id == package_id,
                                              PaqueteDB.organizacion_id == staff.organizacion_id)
                      .with_for_update())
        if p is None:
            raise ValueError("Pedido no encontrado")
        if p.estado != "solicitado":
            raise ValueError("Este pedido ya fue procesado")
        if action == "aprobar":
            p.estado = "aprobado"
            p.prioridad = priority
            p.aprobado = utcnow()
        else:
            p.estado = "rechazado"
        _log(db, staff, "APROBAR_PAQUETE" if action == "aprobar" else "RECHAZAR_PAQUETE",
             "paquete", p.id, {"prioridad":p.prioridad})
        return p.estado


def current_location(user_id):
    with session() as db:
        u = _actor(db, user_id)
        org = db.get(Organizacion, u.organizacion_id)
        p = db.get(Parada, org.parada_actual_id) if org.parada_actual_id else None
        return p.nombre if p and p.organizacion_id == u.organizacion_id else "Sin recorrido"


def advance_and_deliver(staff_id, direction=1):
    if direction not in (-1, 1):
        raise ValueError("Dirección inválida")
    with session() as db, db.begin():
        staff = _actor(db, staff_id, {"admin", "recepcionista"})
        org = db.scalar(select(Organizacion).where(Organizacion.id == staff.organizacion_id).with_for_update())
        routes = db.scalars(select(Parada).where(Parada.organizacion_id == org.id)
                            .order_by(Parada.orden, Parada.id)).all()
        if not routes:
            raise ValueError("El administrador debe crear ubicaciones")
        linked = ListaDoblementeCircular()
        for p in routes:
            linked.insertar_final(p.id)
        if not linked.validar_enlaces():
            raise RuntimeError("Los punteros de la ruta son inconsistentes")
        current = linked.buscar(org.parada_actual_id) if org.parada_actual_id else None
        next_node = linked.avanzar(current, direction)
        arrived_id = next_node.dato
        org.parada_actual_id = arrived_id
        arrived = next(p for p in routes if p.id == arrived_id)
        # Fuente autoritativa SQL: cola enlazada temporal para elegir paquetes elegibles.
        approved = db.scalars(select(PaqueteDB).where(PaqueteDB.organizacion_id == org.id,
                                                     PaqueteDB.estado == "aprobado")
                              .order_by(PaqueteDB.id).with_for_update()).all()
        q = PriorityQueue()
        for p in approved:
            q.encolar(p, p.prioridad)
        delivered = []
        while True:
            elem = q.desencolar_si(lambda p: p.destino_id == arrived_id)
            if elem is None:
                break
            parcel, _ = elem
            parcel.estado = "entregado"
            parcel.entregado = utcnow()
            delivered.append(parcel.id)
            _log(db, staff, "ENTREGAR_PAQUETE", "paquete", parcel.id,
                 {"parada":arrived.nombre, "prioridad": parcel.prioridad})
        _log(db, staff, "AVANZAR_RUTA", "parada", arrived_id,
             {"parada": arrived.nombre, "direccion": direction, "entregados":delivered})
        return {"ubicacion":arrived.nombre,"entregados":delivered,
                "punteros_ok": linked.validar_enlaces(), "cantidad_paradas":len(linked)}


def audit(user_id, limit=150):
    with session() as db, db.begin():
        admin = _actor(db, user_id, {"admin"})
        _log(db, admin, "CONSULTAR_BITACORA", "bitacora")
        rows = db.scalars(select(EventoAuditoria).where(EventoAuditoria.organizacion_id == admin.organizacion_id)
                          .order_by(EventoAuditoria.id.desc()).limit(min(int(limit), 500))).all()
        return [dict(id=r.id, fecha=r.fecha.isoformat(), usuario=r.actor_email, accion=r.accion,
                     entidad=r.entidad, entidad_id=r.entidad_id, detalles=r.detalles) for r in rows]


def list_users(admin_id):
    with session() as db:
        admin = _actor(db, admin_id, {"admin"})
        users = db.scalars(select(Usuario).where(Usuario.organizacion_id == admin.organizacion_id)
                           .order_by(Usuario.id)).all()
        return [_public_user(u) for u in users]


def record_benchmark(user_id, quantity, ratio):
    with session() as db, db.begin():
        actor = _actor(db, user_id, {"admin", "recepcionista"})
        _log(db, actor, "EJECUTAR_BENCHMARK", "benchmark", details={"n": int(quantity), "ratio": float(ratio)})
