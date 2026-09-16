"""Explicit simulation only: no transmission, official number or fiscal authorization."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from config import settings
from database import get_db, system_scope
from domain_locks import serialized_mutation
from models import Appointment, AppointmentStatus, Client, FiscalDocument, FiscalEvent, FiscalProfile, PlatformFiscalProfile, Service, Tenant, User, UserRole
from models.fiscal import utcnow
from routers.billing import require_active_subscription
from routers.tenants import require_owner
from schemas.fiscal import AppointmentFiscalDraft, FiscalCancellation, FiscalDocumentResponse, FiscalProfileData, SubscriptionFiscalDraft

router = APIRouter(prefix="/fiscal", tags=["fiscal"])
platform_router = APIRouter(prefix="/fiscal-platform", tags=["fiscal-demo-platform"])
NOTICE = "DEMONSTRAÇÃO — SEM VALIDADE FISCAL. Não transmitido à Receita Federal ou à prefeitura."


def is_demo_operator(user: User) -> bool:
    return (settings.environment != "production" and user.role == UserRole.admin
            and settings.fiscal_demo_platform_user_id > 0
            and user.id == settings.fiscal_demo_platform_user_id)


def require_demo_operator(user: User = Depends(get_current_user)):
    if not is_demo_operator(user):
        raise HTTPException(403, "Operação restrita ao responsável pela demonstração do Velour")
    return user


def require_demo():
    if settings.fiscal_mode != "demo":
        raise HTTPException(503, "Módulo fiscal desativado. Configure FISCAL_MODE=demo para demonstração.")


@router.get("/config")
def fiscal_config(user: User = Depends(require_owner)):
    return {"mode": settings.fiscal_mode, "notice": NOTICE, "real_issuance_available": False,
            "can_manage_platform": is_demo_operator(user)}


@router.get("/profile")
def get_profile(user: User = Depends(require_owner), db: Session = Depends(get_db)):
    profile = db.query(FiscalProfile).filter(FiscalProfile.tenant_id == user.tenant_id).first()
    return profile.data if profile else None


@router.put("/profile")
@serialized_mutation
def save_profile(data: FiscalProfileData, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    require_demo()
    profile = db.query(FiscalProfile).filter(FiscalProfile.tenant_id == user.tenant_id).first()
    if profile is None:
        profile = FiscalProfile(tenant_id=user.tenant_id)
        db.add(profile)
    profile.data = data.model_dump(mode="json")
    db.commit()
    return profile.data


@router.get("/appointments")
def eligible_appointments(user: User = Depends(require_owner), db: Session = Depends(get_db)):
    rows = (db.query(Appointment, Client.name, Service.name).join(Client, Client.id == Appointment.client_id)
            .join(Service, Service.id == Appointment.service_id)
            .filter(Appointment.status == AppointmentStatus.completed, Appointment.price_charged > 0)
            .order_by(Appointment.scheduled_at.desc()).limit(200).all())
    existing = {x[0] for x in db.query(FiscalDocument.appointment_id).filter(FiscalDocument.issuer_kind == "salon").all()}
    return [{"id": a.id, "client_name": client_name, "service_name": service_name,
             "amount": float(a.price_charged), "competence": a.scheduled_at.date().isoformat()}
            for a, client_name, service_name in rows if a.id not in existing]


@router.get("/documents", response_model=list[FiscalDocumentResponse])
def list_documents(kind: Literal["salon", "platform"] = "salon", offset: int = Query(0, ge=0),
                   limit: int = Query(50, ge=1, le=200), user: User = Depends(require_owner), db: Session = Depends(get_db)):
    return (db.query(FiscalDocument).filter(FiscalDocument.issuer_kind == kind)
            .order_by(FiscalDocument.id.desc()).offset(offset).limit(limit).all())


def document(db, document_id, *, platform=False):
    doc = db.query(FiscalDocument).filter(FiscalDocument.id == document_id).first()
    if doc is None or (platform and doc.issuer_kind != "platform"):
        raise HTTPException(404, "Documento não encontrado")
    return doc


def record(db, doc, action, user):
    db.add(FiscalEvent(tenant_id=doc.tenant_id, document_id=doc.id, action=action, actor_user_id=user.id))


def create_document(db, data, issuer, user, tenant_id, kind, source_key, amount, appointment_id=None):
    if db.query(FiscalDocument).filter(FiscalDocument.tenant_id == tenant_id,
                                     FiscalDocument.issuer_kind == kind, FiscalDocument.source_key == source_key).first():
        raise HTTPException(409, "Já existe documento para esta origem; consulte o histórico.")
    value = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    doc = FiscalDocument(tenant_id=tenant_id, issuer_kind=kind, source_key=source_key,
                         appointment_id=appointment_id, competence=data.competence,
                         description=data.description, service_code=data.service_code,
                         amount=value, iss_rate=data.iss_rate,
                         iss_amount=(value * data.iss_rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                         issuer=dict(issuer), recipient=data.recipient.model_dump(mode="json"),
                         status="draft", environment="demo")
    db.add(doc)
    db.flush()
    record(db, doc, "created", user)
    db.commit()
    return FiscalDocumentResponse.model_validate(doc)


@router.post("/documents", response_model=FiscalDocumentResponse, status_code=201)
@serialized_mutation
def appointment_draft(data: AppointmentFiscalDraft, user: User = Depends(require_owner),
                      active: User = Depends(require_active_subscription), db: Session = Depends(get_db)):
    require_demo()
    appointment = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
    if appointment is None:
        raise HTTPException(404, "Atendimento não encontrado")
    if appointment.status != AppointmentStatus.completed or not appointment.price_charged or appointment.price_charged <= 0:
        raise HTTPException(409, "Conclua um atendimento com valor positivo antes de preparar o documento.")
    profile = db.query(FiscalProfile).filter(FiscalProfile.tenant_id == user.tenant_id).first()
    if profile is None:
        raise HTTPException(409, "Preencha o cadastro fiscal do salão antes de continuar.")
    return create_document(db, data, profile.data, user, user.tenant_id, "salon",
                           f"appointment:{appointment.id}", appointment.price_charged, appointment.id)


@router.get("/documents/{document_id}", response_model=FiscalDocumentResponse)
def get_document(document_id: int, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    return document(db, document_id)


def transition(db, doc, user, action, reason=None):
    require_demo()
    if doc.environment != "demo":
        raise HTTPException(409, "Ambiente fiscal incompatível")
    if action == "simulate":
        if doc.status == "simulated":  # retry is idempotent
            return FiscalDocumentResponse.model_validate(doc)
        if doc.status != "draft":
            raise HTTPException(409, "Somente rascunhos podem ser emitidos em demonstração.")
        doc.status, doc.issued_at = "simulated", utcnow()
        doc.number = f"DEMO-{doc.id:08d}"
    else:
        if doc.status == "cancelled":
            return FiscalDocumentResponse.model_validate(doc)
        if doc.status not in {"draft", "simulated"}:
            raise HTTPException(409, "Documento não pode ser cancelado")
        doc.status, doc.cancelled_at, doc.cancellation_reason = "cancelled", utcnow(), reason
    record(db, doc, action, user)
    db.commit()
    return FiscalDocumentResponse.model_validate(doc)


@router.post("/documents/{document_id}/simulate", response_model=FiscalDocumentResponse)
@serialized_mutation
def simulate_document(document_id: int, user: User = Depends(require_owner),
                      active: User = Depends(require_active_subscription), db: Session = Depends(get_db)):
    doc = document(db, document_id)
    if doc.issuer_kind != "salon":
        raise HTTPException(403, "Somente o Velour pode emitir seus documentos de assinatura")
    return transition(db, doc, user, "simulate")


@router.post("/documents/{document_id}/cancel", response_model=FiscalDocumentResponse)
@serialized_mutation
def cancel_document(document_id: int, data: FiscalCancellation, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    doc = document(db, document_id)
    if doc.issuer_kind != "salon":
        raise HTTPException(403, "Somente o Velour pode cancelar seus documentos de assinatura")
    return transition(db, doc, user, "cancel", data.reason)


def events(db, doc):
    return [{"id": e.id, "action": e.action, "created_at": e.created_at}
            for e in db.query(FiscalEvent).filter(FiscalEvent.document_id == doc.id).order_by(FiscalEvent.id).all()]


@router.get("/documents/{document_id}/events")
def document_events(document_id: int, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    return events(db, document(db, document_id))


def printable(doc):
    def e(value):
        return escape(str(value or ""))

    def party(data):
        return (f'<strong>{e(data["legal_name"])}</strong><br>CPF/CNPJ: {e(data["tax_id"])}<br>'
                f'{e(data["street"])}, {e(data["number"])} — {e(data["district"])}<br>'
                f'{e(data["city"])}/{e(data["state"])} — CEP {e(data["postal_code"])}')

    labels = {"draft": "Rascunho", "simulated": "Emissão simulada", "cancelled": "Cancelado"}
    body = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Velour — documento demonstrativo</title>
    <style>body{{font:16px system-ui;max-width:820px;margin:40px auto;color:#222;padding:20px}}h1{{font-size:28px}}
    .notice{{border:3px solid #92400e;padding:16px;color:#92400e;font-weight:bold}}section{{margin:24px 0}}
    .columns{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}pre{{white-space:pre-wrap;font:inherit}}
    table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #ccc;padding:12px;text-align:left}}
    @media print{{body{{margin:0}}.notice{{border:3px solid black}}}}</style>
    <h1>VELOUR · Demonstrativo de serviço</h1><p class="notice">{e(NOTICE)}</p>
    <p><b>{e(doc.number or 'RASCUNHO-' + str(doc.id))}</b> · {labels[doc.status]} · Competência: {e(doc.competence)}</p>
    <div class="columns"><section><h2>Prestador</h2>{party(doc.issuer)}</section><section><h2>Tomador</h2>{party(doc.recipient)}</section></div>
    <section><h2>Serviço</h2><pre>{e(doc.description)}</pre><p>Código informado: {e(doc.service_code)}</p></section>
    <table><tr><th>Valor do serviço</th><th>Alíquota ilustrativa</th><th>ISS ilustrativo</th></tr>
    <tr><td>R$ {doc.amount:.2f}</td><td>{doc.iss_rate:.2f}%</td><td>R$ {doc.iss_amount:.2f}</td></tr></table>
    <p>Este cálculo não apura tributos a recolher. Não há autorização, chave de acesso, protocolo ou XML fiscal.</p>
    <p>{'Motivo do cancelamento: ' + e(doc.cancellation_reason) if doc.cancelled_at else ''}</p>
    <footer>Documento para apresentação do MVP. Use a função Imprimir do navegador para salvar em PDF.</footer></html>'''
    return HTMLResponse(body, headers={"Content-Disposition": f'attachment; filename="velour-demo-{doc.id}.html"',
                                     "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                     "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'"})


@router.get("/documents/{document_id}/print")
def print_document(document_id: int, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    return printable(document(db, document_id))


# Cross-tenant demo operations require an explicit server-configured operator and
# are impossible in production. No tenant role is upgraded to a platform role.
@platform_router.get("/profile")
def platform_profile(user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        profile = db.get(PlatformFiscalProfile, 1)
        return profile.data if profile else None


@platform_router.put("/profile")
@serialized_mutation
def save_platform_profile(data: FiscalProfileData, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    require_demo()
    with system_scope(db):
        profile = db.get(PlatformFiscalProfile, 1)
        if profile is None:
            profile = PlatformFiscalProfile(id=1)
            db.add(profile)
        profile.data = data.model_dump(mode="json")
        db.commit()
        return profile.data


@platform_router.get("/tenants")
def platform_tenants(user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        return [{"id": t.id, "name": t.name, "fiscal_profile": p.data if p else None}
                for t, p in db.query(Tenant, FiscalProfile).outerjoin(FiscalProfile, FiscalProfile.tenant_id == Tenant.id)
                .filter(Tenant.is_active == True).order_by(Tenant.id).limit(200).all()]


@platform_router.get("/documents", response_model=list[FiscalDocumentResponse])
def platform_documents(user: User = Depends(require_demo_operator), db: Session = Depends(get_db),
                       offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    with system_scope(db):
        return [FiscalDocumentResponse.model_validate(d) for d in db.query(FiscalDocument)
                .filter(FiscalDocument.issuer_kind == "platform").order_by(FiscalDocument.id.desc()).offset(offset).limit(limit).all()]


@platform_router.post("/documents", response_model=FiscalDocumentResponse, status_code=201)
@serialized_mutation
def subscription_draft(data: SubscriptionFiscalDraft, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    require_demo()
    with system_scope(db):
        tenant = db.get(Tenant, data.tenant_id)
        if not tenant or not tenant.is_active:
            raise HTTPException(404, "Salão não encontrado")
        profile = db.get(PlatformFiscalProfile, 1)
        if not profile:
            raise HTTPException(409, "Preencha o cadastro fiscal do Velour.")
        return create_document(db, data, profile.data, user, tenant.id, "platform",
                               f"subscription:{data.subscription_reference}", data.amount)


@platform_router.get("/documents/{document_id}/events")
def platform_events(document_id: int, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        return events(db, document(db, document_id, platform=True))


@platform_router.get("/documents/{document_id}/print")
def platform_print(document_id: int, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        return printable(document(db, document_id, platform=True))


@platform_router.post("/documents/{document_id}/simulate", response_model=FiscalDocumentResponse)
@serialized_mutation
def platform_simulate(document_id: int, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        return transition(db, document(db, document_id, platform=True), user, "simulate")


@platform_router.post("/documents/{document_id}/cancel", response_model=FiscalDocumentResponse)
@serialized_mutation
def platform_cancel(document_id: int, data: FiscalCancellation, user: User = Depends(require_demo_operator), db: Session = Depends(get_db)):
    with system_scope(db):
        return transition(db, document(db, document_id, platform=True), user, "cancel", data.reason)
