"""Create fictional presentation data in an EMPTY migrated development database.

Run with APP_ENV=development, FISCAL_MODE=demo, AUTO_CREATE_TABLES=false.
Never resets an existing database. Credentials are generated for this demo only.
"""
import json
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from auth import hash_password
from config import settings
from database import Base, system_session
from models import Appointment, AppointmentStatus, Client, FiscalProfile, PlatformFiscalProfile, Professional, Service, ServiceCategory, Tenant, User, UserRole
from routers.fiscal import create_document, transition
from schemas.fiscal import AppointmentFiscalDraft, FiscalProfileData, SubscriptionFiscalDraft


def seed_demo():
    if settings.environment != "development" or settings.fiscal_mode != "demo" or settings.auto_create_tables:
        raise RuntimeError("Use development, FISCAL_MODE=demo e AUTO_CREATE_TABLES=false em banco vazio migrado.")
    password = secrets.token_urlsafe(18)
    party = {"legal_name": "Cliente fictício", "tax_id": "52998224725", "email": "cliente@example.com",
             "street": "Rua de Demonstração", "number": "100", "district": "Centro", "postal_code": "83702000",
             "city": "Araucária", "municipality_code": "4101804", "state": "PR"}
    profile = FiscalProfileData(**{**party, "legal_name": "Salão Aurora — Demonstração", "tax_id": "11222333000181",
                                  "municipal_registration": "DEMO", "tax_regime": "simples", "service_code": "060101", "iss_rate": "2.00"})
    now = datetime.now().replace(microsecond=0)
    with system_session() as db:
        tenants = db.query(Tenant).all()
        # The tenant migration always inserts this empty legacy placeholder.
        # Leave it untouched and reject any business data or configured tenant.
        placeholder_only = (not tenants or (len(tenants) == 1 and tenants[0].id == 1
                            and tenants[0].slug == "legacy" and tenants[0].name == "Salão existente"))
        populated = any(db.query(mapper.class_).first() is not None for mapper in Base.registry.mappers
                        if mapper.class_ is not Tenant)
        if not placeholder_only or populated:
            raise RuntimeError("Banco não está vazio. Nenhum registro foi alterado. Use outro DATABASE_URL.")
        tenant = Tenant(name="Salão Aurora · Demonstração", slug="aurora-fiscal-demo", subscription_status="trialing", trial_ends_at=now + timedelta(days=365))
        db.add(tenant); db.flush()
        user = User(tenant_id=tenant.id, name="Apresentação Velour", email="demo-fiscal@example.com",
                    hashed_password=hash_password(password), role=UserRole.admin, is_active=True, token_version=0)
        category = ServiceCategory(tenant_id=tenant.id, name="Cuidados pessoais")
        prof = Professional(tenant_id=tenant.id, name="Profissional fictícia", specialty="Estética", gender="F", phone="41999990000")
        db.add_all([user, category, prof, FiscalProfile(tenant_id=tenant.id, data=profile.model_dump(mode="json"))]); db.flush()
        service = Service(tenant_id=tenant.id, category_id=category.id, name="Corte e finalização", duration_minutes=60, price=Decimal("120.00"), points_reward=0)
        db.add(service); db.flush()
        platform_profile = profile.model_copy(update={"legal_name": "Velour — Empresa fictícia", "service_code": "010501"}).model_dump(mode="json")
        db.add(PlatformFiscalProfile(id=1, data=platform_profile))
        for index, name in enumerate(("Ana · Cliente fictícia", "Beatriz · Cliente fictícia", "Carla · Cliente fictícia", "Diana · Cliente fictícia")):
            client = Client(tenant_id=tenant.id, name=name, code=f"DEMO-{index+1}", referral_code=f"FISC{index:04}", phone="41999990000", gender="F")
            db.add(client); db.flush()
            when = now - timedelta(days=index + 1)
            appointment = Appointment(tenant_id=tenant.id, client_id=client.id, professional_id=prof.id, service_id=service.id,
                                      scheduled_at=when, ends_at=when+timedelta(hours=1), status=AppointmentStatus.completed,
                                      price_charged=Decimal("120.00") + index * 25, paid=True,
                                      amount_paid=Decimal("120.00") + index * 25, payment_method="pix")
            db.add(appointment); db.flush()
            if index < 3:
                data = AppointmentFiscalDraft(appointment_id=appointment.id, competence=when.date(), description=service.name,
                                              service_code="060101", iss_rate="2.00", recipient={**party, "legal_name": name})
                result = create_document(db, data, profile.model_dump(mode="json"), user, tenant.id, "salon", f"appointment:{appointment.id}", appointment.price_charged, appointment.id)
                from models import FiscalDocument
                doc = db.get(FiscalDocument, result.id)
                if index in (0, 2):
                    transition(db, doc, user, "simulate")
                if index == 2:
                    transition(db, doc, user, "cancel", "Cancelamento fictício para apresentação do histórico")
        subscription = SubscriptionFiscalDraft(tenant_id=tenant.id, subscription_reference="demo-mensalidade-2026-09",
                                              competence=now.date(), amount="149.90", description="Assinatura mensal Velour — demonstração",
                                              service_code="010501", iss_rate="2.00", recipient={**party, "legal_name": profile.legal_name, "tax_id": profile.tax_id})
        result = create_document(db, subscription, platform_profile, user, tenant.id, "platform", "subscription:demo-mensalidade-2026-09", subscription.amount)
        transition(db, db.get(FiscalDocument, result.id), user, "simulate")
        db.commit()
        return {"email": user.email, "password": password, "FISCAL_DEMO_PLATFORM_USER_ID": user.id,
                "notice": "Credenciais exclusivas da demonstração local. Não usar em produção."}


if __name__ == "__main__":
    print(json.dumps(seed_demo(), ensure_ascii=False, indent=2))
