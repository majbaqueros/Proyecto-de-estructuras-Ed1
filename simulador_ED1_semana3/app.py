"""Punto de entrada FastAPI para Vercel (app) y localhost.
Sin Flet ni WebSocket: HTML/JS estático + API HTTP + PostgreSQL persistente.
"""
import hashlib
import hmac
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import secrets
import threading
from datetime import timedelta
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select, func
from portal.db import (configure_db, session, Organizacion, Usuario, PaqueteDB,
                       Parada, EventoAuditoria, utcnow)
from portal import services as svc
from portal import recovery
from logica.metricas import ejecutar_benchmark, estimar_memoria_nodos

app = FastAPI(title="ED1 — Plataforma logística", version="3.0", docs_url=None, redoc_url=None)
BASE = Path(__file__).resolve().parent
_cookie_name = "ed1_session"
_db_lock = threading.Lock()
_initialized = False


def _secret():
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) >= 32:
        return secret
    if os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("Falta AUTH_SECRET seguro (32 o más caracteres)")
    return "ed1-development-secret-not-for-production-2026"


def _signer():
    return URLSafeTimedSerializer(_secret(), salt="ed1-session-v3")


def initialize():
    global _initialized
    if _initialized:
        return
    with _db_lock:
        if _initialized:
            return
        configure_db()
        keys = ("ADMIN_BOOTSTRAP_ORG", "ADMIN_BOOTSTRAP_EMAIL", "ADMIN_BOOTSTRAP_PASSWORD")
        if all(os.getenv(k) for k in keys):
            svc.bootstrap_admin(os.environ[keys[0]], os.environ[keys[1]], os.environ[keys[2]])
        _initialized = True


def _fingerprint(digest):
    return hmac.new(_secret().encode(), digest.encode(), hashlib.sha256).hexdigest()[:20]


def _issue_cookie(response, user_id, password_hash):
    csrf = secrets.token_urlsafe(24)
    signed = _signer().dumps({"uid": user_id, "pwd": _fingerprint(password_hash), "csrf": csrf})
    response.set_cookie(_cookie_name, signed, httponly=True,
                        secure=bool(os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production"),
                        samesite="lax", max_age=60*60*8, path="/")
    return csrf


def _auth(req: Request, mutation=False):
    token = req.cookies.get(_cookie_name, "")
    if not token:
        raise HTTPException(401, "Debes iniciar sesión")
    try:
        data = _signer().loads(token, max_age=60*60*8)
    except (BadSignature, SignatureExpired):
        raise HTTPException(401, "La sesión ha caducado") from None
    if mutation:
        sent = req.headers.get("x-csrf-token", "")
        if not sent or not hmac.compare_digest(sent, data.get("csrf", "")):
            raise HTTPException(403, "Protección CSRF: vuelve a iniciar sesión")
    with session() as db:
        user = db.get(Usuario, data.get("uid"))
        if not user or not user.activo or not hmac.compare_digest(_fingerprint(user.password_hash), data.get("pwd", "")):
            raise HTTPException(401, "La sesión ya no es válida")
        return user.id, data.get("csrf")


@app.middleware("http")
async def protections(req: Request, call_next):
    # El frontend solo hace POST application/json. No se habilita CORS de terceros.
    if req.method not in ("GET", "HEAD", "OPTIONS"):
        origin = req.headers.get("origin")
        if origin:
            u = urlparse(origin)
            host = req.headers.get("host", "").casefold()
            if u.netloc.casefold() != host:
                return JSONResponse({"detail":"Origen no permitido"}, status_code=403)
    response = await call_next(req)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store" if req.url.path.startswith("/api") else "public, max-age=60"
    response.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self'; style-src 'self'; "
                                                     "img-src 'self' data:; connect-src 'self'; "
                                                     "object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
    return response


@app.exception_handler(ValueError)
async def bad_value(req, ex):
    return JSONResponse({"detail":str(ex)}, status_code=400)


@app.exception_handler(PermissionError)
async def forbidden(req, ex):
    return JSONResponse({"detail":str(ex)}, status_code=403)


@app.head("/", include_in_schema=False)
def homepage_head():
    return Response(status_code=200)


@app.get("/", include_in_schema=False)
def homepage():
    return HTMLResponse((BASE / "public" / "index.html").read_text(encoding="utf-8"))


@app.get("/style.css", include_in_schema=False)
def style():
    return FileResponse(BASE / "public" / "style.css", media_type="text/css")


@app.get("/client.js", include_in_schema=False)
def client():
    return FileResponse(BASE / "public" / "client.js", media_type="application/javascript")


@app.get("/api/health")
def health():
    initialize()
    with session() as db:
        db.execute(select(func.count()).select_from(Organizacion)).scalar()
    return {"status":"ok", "database":"conectada", "mode":"fastapi", "email_configured":recovery.email_configured()}


class SignIn(BaseModel):
    email: str
    password: str


class SignUp(SignIn):
    code: str
    name: str


class ResetRequest(BaseModel):
    email: str


class ResetConfirm(ResetRequest):
    code: str
    new_password: str


class NewRoute(BaseModel):
    name: str


class NewOrder(BaseModel):
    route_id: int
    weight: float
    recipient: str = ""


class Decision(BaseModel):
    action: str
    priority: int = 3


class NewReceptionist(BaseModel):
    name: str
    email: str
    password: str


class Move(BaseModel):
    direction: int = 1


class Benchmark(BaseModel):
    amount: int = Field(default=200, ge=10, le=10000)


def _session_response(user):
    with session() as db:
        obj = db.get(Usuario, user["id"])
        digest = obj.password_hash
    csrf = secrets.token_urlsafe(24)
    data = _signer().dumps({"uid": user["id"], "pwd": _fingerprint(digest), "csrf": csrf})
    reply = JSONResponse({"user": user, "csrf": csrf})
    reply.set_cookie(_cookie_name, data, httponly=True,
                     secure=bool(os.getenv("VERCEL") or os.getenv("ENVIRONMENT") == "production"),
                     samesite="lax", max_age=60*60*8, path="/")
    return reply


@app.post("/api/auth/login")
def login(form: SignIn):
    initialize()
    user = svc.login(form.email, form.password)
    return _session_response(user)


@app.post("/api/auth/register")
def register(form: SignUp):
    initialize()
    user = svc.sign_up_client(form.code, form.name, form.email, form.password)
    return _session_response(user)


@app.get("/api/me")
def me(req: Request):
    initialize()
    uid, csrf = _auth(req)
    with session() as db:
        u = db.get(Usuario, uid)
        result = {"id":u.id, "nombre":u.nombre, "email":u.email,"rol":u.rol}
    return {"user":result, "csrf":csrf, "organization":svc.organization(uid)}


@app.post("/api/auth/logout")
def logout(req: Request):
    initialize()
    uid,_ = _auth(req, True)
    svc.logout(uid)
    resp = JSONResponse({"ok":True})
    resp.delete_cookie(_cookie_name, path="/")
    return resp


@app.post("/api/auth/password/request")
def request_password(form: ResetRequest):
    initialize()
    if not recovery.email_configured():
        raise HTTPException(503, "El administrador debe configurar un proveedor de correo para recuperar contraseñas")
    return {"message":recovery.request_reset(form.email)}


@app.post("/api/auth/password/reset")
def reset_password(form: ResetConfirm):
    initialize()
    return {"message":recovery.confirm_reset(form.email, form.code, form.new_password)}


@app.get("/api/organization")
def org(req: Request):
    initialize()
    uid,_ = _auth(req)
    return svc.organization(uid)


@app.get("/api/routes")
def routes(req: Request):
    initialize()
    uid,_ = _auth(req)
    return {"items":svc.list_routes(uid),"current":svc.current_location(uid)}


@app.post("/api/routes")
def add_route(req: Request, form: NewRoute):
    initialize()
    uid,_ = _auth(req, True)
    return svc.add_route(uid, form.name)


@app.delete("/api/routes/{route_id}")
def remove_route(req: Request, route_id: int):
    initialize()
    uid,_ = _auth(req, True)
    svc.delete_route(uid, route_id)
    return {"ok":True}


@app.post("/api/routes/advance")
def advance(req: Request, form: Move):
    initialize()
    uid,_ = _auth(req, True)
    return svc.advance_and_deliver(uid, form.direction)


@app.get("/api/orders")
def orders(req: Request):
    initialize()
    uid,_ = _auth(req)
    return {"items":svc.list_orders(uid)}


@app.post("/api/orders")
def new_order(req: Request, form: NewOrder):
    initialize()
    uid,_ = _auth(req, True)
    pid = svc.create_request(uid, form.route_id, form.weight, form.recipient)
    return {"id":pid, "ok":True}


@app.post("/api/orders/{package_id}/decision")
def decision(req: Request, package_id: int, form: Decision):
    initialize()
    uid,_ = _auth(req, True)
    return {"estado":svc.set_order_status(uid, package_id, form.action, form.priority)}


@app.get("/api/users")
def users(req: Request):
    initialize()
    uid,_ = _auth(req)
    return {"items":svc.list_users(uid)}


@app.post("/api/users")
def new_user(req: Request, form: NewReceptionist):
    initialize()
    uid,_ = _auth(req, True)
    return svc.create_receptionist(uid, form.name, form.email, form.password)


@app.get("/api/audit")
def audit(req: Request):
    initialize()
    uid,_ = _auth(req)
    return {"items":svc.audit(uid)}


@app.get("/api/metrics")
def metrics(req: Request):
    initialize()
    uid,_ = _auth(req)
    with session() as db:
        u = db.get(Usuario, uid)
        if u.rol not in ("admin", "recepcionista"):
            raise PermissionError("Solo el personal puede consultar las métricas")
        total = db.scalar(select(func.count(EventoAuditoria.id)).where(EventoAuditoria.organizacion_id == u.organizacion_id)) or 0
        recent = db.scalar(select(func.count(EventoAuditoria.id)).where(
            EventoAuditoria.organizacion_id == u.organizacion_id,
            EventoAuditoria.fecha >= utcnow() - timedelta(seconds=5))) or 0
        n = (db.scalar(select(func.count(Parada.id)).where(Parada.organizacion_id == u.organizacion_id)) or 0) + (
            db.scalar(select(func.count(PaqueteDB.id)).where(PaqueteDB.organizacion_id == u.organizacion_id)) or 0)
    return {"operations_total":total,"operations_per_second":recent / 5,"memory":estimar_memoria_nodos(n),"nodes":n}


@app.post("/api/metrics/benchmark")
def benchmark(req: Request, form: Benchmark):
    initialize()
    uid,_ = _auth(req, True)
    from portal.services import record_benchmark
    r = ejecutar_benchmark(form.amount)
    record_benchmark(uid, r.cantidad, r.ratio)
    return {"quantity":r.cantidad,"insert_ms":r.append_ms,"search_ms":r.buscar_ms,"ratio":r.ratio}
