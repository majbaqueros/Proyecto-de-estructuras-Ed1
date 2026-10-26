"""Entidades persistentes y acceso PostgreSQL. Identificadores del tenant en datos privados."""
import os
from datetime import datetime, timezone
from sqlalchemy import (create_engine, String, Integer, Float, ForeignKey, DateTime,
                        UniqueConstraint, Index, Text, JSON)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Organizacion(Base):
    __tablename__ = "organizaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    parada_actual_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)  # admin, recepcionista, cliente
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Parada(Base):
    __tablename__ = "paradas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    clave: Mapped[str] = mapped_column(String(130), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("organizacion_id", "clave", name="uq_parada_tenant_clave"),)


class PaqueteDB(Base):
    __tablename__ = "paquetes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"), nullable=False, index=True)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    destino_id: Mapped[int] = mapped_column(ForeignKey("paradas.id"), nullable=False)
    peso: Mapped[float] = mapped_column(Float, nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    estado: Mapped[str] = mapped_column(String(22), nullable=False, default="solicitado")
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    aprobado: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entregado: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    destinatario: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    nota: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    __table_args__ = (Index("idx_paquete_tenant_estado", "organizacion_id", "estado"),)


class EventoAuditoria(Base):
    __tablename__ = "bitacora"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    accion: Mapped[str] = mapped_column(String(90), nullable=False)
    entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalles: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (Index("idx_bitacora_tenant_fecha", "organizacion_id", "fecha"),)


class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    fallos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inicio_ventana: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    codigo_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    creado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expira: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    intentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    utilizado: Mapped[bool] = mapped_column(default=False, nullable=False)


def database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        if os.environ.get("VERCEL") or os.environ.get("ENVIRONMENT") == "production":
            raise RuntimeError("Configura DATABASE_URL de PostgreSQL (Vercel requiere base externa persistente)")
        return "sqlite:///./ed1_desarrollo.sqlite3"  # solo desarrollo local
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_engine = None
_Session = None


def configure_db(url=None):
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    connection = url or database_url()
    options = {"pool_pre_ping": True, "pool_recycle": 240}
    if connection.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    _engine = create_engine(connection, **options)
    _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    return _engine


def session():
    if _Session is None:
        configure_db()
    return _Session()
