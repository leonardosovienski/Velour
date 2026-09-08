"""Fail-closed tenant sessions. Privileged code must explicitly enter system_scope."""
from contextlib import contextmanager

from sqlalchemy import Column, ForeignKey, Integer, create_engine, event, inspect, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, with_loader_criteria

from config import settings


class TenantIsolationError(RuntimeError):
    pass


class Base(DeclarativeBase):
    pass


class TenantScoped:
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)


def tenant_scope(db: Session, tenant_id: int) -> Session:
    if type(tenant_id) is not int or tenant_id <= 0:
        raise TenantIsolationError("A positive tenant ID is required")
    previous = db.info.get("tenant_id")
    if previous is not None and previous != tenant_id:
        raise TenantIsolationError("A session cannot change tenant")
    for obj in db.identity_map.values():
        if isinstance(obj, TenantScoped) and obj.tenant_id != tenant_id:
            raise TenantIsolationError("Session contains data from another tenant")
    db.info["tenant_id"] = tenant_id
    return db


@contextmanager
def system_scope(db: Session):
    """Trusted authentication, billing and maintenance only; never driven by request data."""
    previous = db.info.get("system_scope", False)
    db.info["system_scope"] = True
    try:
        yield db
    finally:
        # Privileged reads must not leave foreign objects in the identity map,
        # where future get()/relationship access could return them without SQL.
        if not previous:
            tenant_id = db.info.get("tenant_id")
            for obj in list(db.identity_map.values()):
                if isinstance(obj, TenantScoped) and (tenant_id is None or obj.tenant_id != tenant_id):
                    db.expunge(obj)
        db.info["system_scope"] = previous


class ScopedSession(Session):
    def connection(self, *args, **kwargs):
        if not self.info.get("system_scope"):
            raise TenantIsolationError("Direct connections require system_scope")
        return super().connection(*args, **kwargs)

    def get(self, entity, ident, **kwargs):
        # Session.get can bypass SQL and its criteria via the identity map.
        if not self.info.get("system_scope"):
            _require_scope(self)
            from models.tenant import Tenant
            if not issubclass(inspect(entity).class_, (TenantScoped, Tenant)):
                raise TenantIsolationError("Global records require system_scope")
        result = super().get(entity, ident, **kwargs)
        if result is not None and not self.info.get("system_scope"):
            from models.tenant import Tenant
            if isinstance(result, TenantScoped) and result.tenant_id != self.info["tenant_id"]:
                return None
            if isinstance(result, Tenant) and result.id != self.info["tenant_id"]:
                return None
        return result

    def bulk_save_objects(self, *args, **kwargs):
        if not self.info.get("system_scope"):
            raise TenantIsolationError("Use normal ORM inserts inside tenant sessions")
        return super().bulk_save_objects(*args, **kwargs)

    def bulk_insert_mappings(self, *args, **kwargs):
        if not self.info.get("system_scope"):
            raise TenantIsolationError("Use normal ORM inserts inside tenant sessions")
        return super().bulk_insert_mappings(*args, **kwargs)

    def bulk_update_mappings(self, *args, **kwargs):
        if not self.info.get("system_scope"):
            raise TenantIsolationError("Use scoped ORM updates inside tenant sessions")
        return super().bulk_update_mappings(*args, **kwargs)


def _require_scope(db):
    tenant_id = db.info.get("tenant_id")
    if type(tenant_id) is not int or tenant_id <= 0:
        raise TenantIsolationError("Database access requires tenant_scope or explicit system_scope")
    return tenant_id


@event.listens_for(ScopedSession, "do_orm_execute")
def _scope_statement(state):
    if state.session.info.get("system_scope"):
        return
    tenant_id = _require_scope(state.session)
    from sqlalchemy.orm.context import FromStatement
    if not state.is_orm_statement or state.is_insert or isinstance(state.statement, FromStatement):
        raise TenantIsolationError("Raw SQL, Core statements and bulk inserts require system_scope")
    from models.tenant import Tenant
    if any(not issubclass(mapper.class_, (TenantScoped, Tenant)) for mapper in state.all_mappers):
        raise TenantIsolationError("Global records require system_scope")

    state.statement = state.statement.options(
        with_loader_criteria(TenantScoped, lambda cls: cls.tenant_id == tenant_id, include_aliases=True),
        with_loader_criteria(Tenant, lambda cls: cls.id == tenant_id, include_aliases=True),
    )
    if state.is_update or state.is_delete:
        mapper = state.bind_mapper
        if mapper is None or not issubclass(mapper.class_, TenantScoped):
            raise TenantIsolationError("Global records cannot be bulk-mutated by a tenant")
        if state.is_update:
            if isinstance(state.parameters, list):
                raise TenantIsolationError("Bulk primary-key updates require system_scope")
            protected = {"id", "tenant_id"} | {c.name for c in mapper.columns if c.foreign_keys}
            assignments = getattr(state.statement, "_values", {}) or {}
            ordered = getattr(state.statement, "_ordered_values", []) or []
            keys = list(assignments) + [key for key, value in ordered]
            if any(getattr(key, "name", key) in protected for key in keys):
                raise TenantIsolationError("Ownership and references cannot be bulk-updated")
        state.statement = state.statement.where(mapper.class_.tenant_id == tenant_id)


@event.listens_for(ScopedSession, "before_flush")
def _validate_tenant_writes(db, flush_context, instances):
    privileged = db.info.get("system_scope")
    tenant_id = None if privileged else _require_scope(db)
    objects = set(db.new) | set(db.dirty) | set(db.deleted)
    for obj in objects:
        if not isinstance(obj, TenantScoped):
            if not privileged:
                raise TenantIsolationError("Global records require system_scope")
            continue
        if obj in db.new and obj.tenant_id is None and not privileged:
            obj.tenant_id = tenant_id
        if obj.tenant_id is None or (not privileged and obj.tenant_id != tenant_id):
            raise TenantIsolationError("Cannot write data owned by another tenant")
        state = inspect(obj)
        if state.persistent and state.attrs.tenant_id.history.has_changes():
            raise TenantIsolationError("Tenant ownership is immutable")
    for obj in objects - set(db.deleted):
        if not isinstance(obj, TenantScoped):
            continue
        mapper = inspect(obj).mapper
        for relationship in mapper.relationships:
            if relationship.key not in obj.__dict__:
                continue
            value = obj.__dict__[relationship.key]
            related = value if relationship.uselist else [value]
            if any(isinstance(item, TenantScoped) and item.tenant_id != obj.tenant_id for item in (related or [])):
                raise TenantIsolationError("Cross-tenant relationship is forbidden")
        for col in mapper.columns:
            if col.name == "tenant_id":
                continue
            value = getattr(obj, col.key)
            if value is None:
                continue
            for fk in col.foreign_keys:
                target = fk.column.table
                if "tenant_id" not in target.c:
                    continue
                found = Session.connection(db).execute(select(target.c.tenant_id).where(fk.column == value)).scalar_one_or_none()
                if found is not None and found != obj.tenant_id:
                    raise TenantIsolationError("Cross-tenant reference is forbidden")


engine_options = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.database_url, **engine_options)
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=ScopedSession)


@contextmanager
def system_session():
    with SessionLocal() as db, system_scope(db):
        yield db


def get_db():
    with SessionLocal() as db:
        yield db
