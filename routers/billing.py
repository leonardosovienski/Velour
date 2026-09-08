"""Hosted Stripe subscriptions with signed, durable and idempotent webhooks.

Stripe is the authority: no redirect, browser payload or stale event grants
access. Subscription snapshots are retrieved under the tenant's database lock.
"""
import logging
import threading
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from auth import get_current_user
from config import settings
from database import get_db, system_scope
from models import BillingWebhookEvent, Tenant, User, UserRole
from rate_limit import RateLimiter, request_key
from routers.tenants import require_owner
from schemas.billing import BillingStatus, HostedSession

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger("velour.billing")
# Complements PostgreSQL FOR UPDATE for local SQLite's single-process runtime.
_billing_lock = threading.RLock()
_session_limiter = RateLimiter(10, 60, "Muitas solicitações de cobrança. Aguarde um minuto.")
_TERMINAL = {"canceled", "incomplete_expired"}
_EVENTS = {
    "checkout.session.completed", "checkout.session.async_payment_succeeded",
    "customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted",
    "customer.subscription.paused", "customer.subscription.resumed",
    "invoice.paid", "invoice.payment_succeeded", "invoice.payment_failed",
    "invoice.payment_action_required",
}


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _timestamp(value):
    return datetime.fromtimestamp(int(value), timezone.utc).replace(tzinfo=None) if value else None


def _object_id(value):
    return value.get("id") if isinstance(value, dict) else value


def billing_configured() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_webhook_secret and settings.stripe_price_id)


def _stripe():
    if not billing_configured():
        raise HTTPException(status_code=503, detail="Cobrança ainda não configurada. Contate o suporte.")
    return stripe.StripeClient(
        settings.stripe_secret_key, max_network_retries=1,
        http_client=stripe.RequestsClient(timeout=15),
    )


def subscription_allows_access(tenant: Tenant, now: datetime | None = None) -> bool:
    now = now or _now()
    if not tenant.is_active:
        return False
    if tenant.subscription_status == "trialing":
        return bool(tenant.trial_ends_at and tenant.trial_ends_at > now)
    if tenant.subscription_status == "active":
        return bool(tenant.current_period_end and tenant.current_period_end > now)
    if tenant.subscription_status == "past_due":
        return bool(tenant.past_due_since and tenant.past_due_since + timedelta(days=7) > now)
    return False


def require_active_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not subscription_allows_access(tenant):
        raise HTTPException(status_code=402, detail="Assinatura necessária. Acesse Assinatura para regularizar ou exportar os dados.")
    return user


@router.get("/status", response_model=BillingStatus)
def billing_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).one()
    status = tenant.subscription_status
    if status == "trialing" and not subscription_allows_access(tenant):
        status = "expired"
    return BillingStatus(
        tenant_id=tenant.id, tenant_name=tenant.name, subscription_status=status,
        trial_ends_at=tenant.trial_ends_at, current_period_end=tenant.current_period_end,
        past_due_since=tenant.past_due_since, access_allowed=subscription_allows_access(tenant),
        configured=billing_configured(), can_manage_billing=user.role == UserRole.admin,
        has_billing_customer=bool(tenant.stripe_customer_id),
    )


def _store_checkout(tenant, session):
    tenant.checkout_session_id = session["id"]
    tenant.checkout_session_expires_at = _timestamp(session.get("expires_at"))
    if not session.get("url"):
        raise HTTPException(status_code=409, detail="Checkout já finalizado. Aguarde a confirmação da assinatura.")
    return {"url": session["url"]}


@router.post("/checkout-session", response_model=HostedSession)
def checkout_session(request: Request, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    _session_limiter.check_and_record(request_key(request, user))
    client = _stripe()
    with _billing_lock, system_scope(db):
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).populate_existing().with_for_update().one()
        try:
            if not tenant.stripe_customer_id:
                customer = client.v1.customers.create(
                    {"name": tenant.name, "email": user.email, "metadata": {"tenant_id": str(tenant.id)}},
                    options={"idempotency_key": f"velour-customer-{tenant.id}"},
                )
                tenant.stripe_customer_id = customer["id"]
            # Stripe may have processed payment before its webhook reaches us.
            # Inspect all states so a past-due or incomplete subscription cannot
            # accidentally create a second recurring charge.
            subscriptions = client.v1.subscriptions.list({"customer": tenant.stripe_customer_id, "status": "all", "limit": 100})
            if subscriptions.get("has_more") or any(s.get("status") not in _TERMINAL for s in subscriptions.get("data", [])):
                raise HTTPException(status_code=409, detail="Já existe uma assinatura. Use Gerenciar assinatura para atualizar o pagamento.")
            sessions = client.v1.checkout.sessions.list({"customer": tenant.stripe_customer_id, "status": "open", "limit": 100})
            for session in sessions.get("data", []):
                if session.get("mode") == "subscription" and session.get("metadata", {}).get("tenant_id") == str(tenant.id):
                    result = _store_checkout(tenant, session)
                    db.commit()
                    return result
            if sessions.get("has_more"):
                raise HTTPException(status_code=409, detail="Há sessões pendentes. Contate o suporte antes de iniciar outra cobrança.")
            price = client.v1.prices.retrieve(settings.stripe_price_id)
            recurring = price.get("recurring") or {}
            if (not price.get("active") or price.get("type") != "recurring"
                    or recurring.get("interval") != "month" or recurring.get("interval_count") != 1
                    or bool(price.get("livemode")) != settings.stripe_livemode):
                raise HTTPException(status_code=503, detail="Plano de assinatura indisponível. Contate o suporte.")
            now = _now()
            subscription_data = {"metadata": {"tenant_id": str(tenant.id)}}
            if tenant.subscription_status == "trialing" and not tenant.stripe_subscription_id and tenant.trial_ends_at and tenant.trial_ends_at > now:
                # Checkout requires an absolute trial end >=48h away. A signup
                # near day 14 receives a short extension, never an early charge.
                trial_end = max(tenant.trial_ends_at, now + timedelta(hours=49))
                subscription_data["trial_end"] = int(trial_end.replace(tzinfo=timezone.utc).timestamp())
            params = {
                "mode": "subscription", "customer": tenant.stripe_customer_id,
                "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
                "client_reference_id": str(tenant.id), "metadata": {"tenant_id": str(tenant.id)},
                "subscription_data": subscription_data,
                "success_url": f"{settings.frontend_url}/billing?checkout=success",
                "cancel_url": f"{settings.frontend_url}/billing?checkout=cancelled",
            }
            session = client.v1.checkout.sessions.create(params)
            result = _store_checkout(tenant, session)
            db.commit()
            return result
        except stripe.StripeError as exc:
            db.rollback()
            logger.warning("Stripe checkout unavailable (%s)", type(exc).__name__)
            raise HTTPException(status_code=502, detail="Não foi possível abrir a cobrança. Tente novamente em instantes.") from exc


@router.post("/portal-session", response_model=HostedSession)
def portal_session(request: Request, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    _session_limiter.check_and_record(request_key(request, user))
    client = _stripe()
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).one()
    if not tenant.stripe_customer_id:
        raise HTTPException(status_code=409, detail="Inicie sua assinatura antes de abrir o portal.")
    try:
        session = client.v1.billing_portal.sessions.create({"customer": tenant.stripe_customer_id, "return_url": f"{settings.frontend_url}/billing"})
        return {"url": session["url"]}
    except stripe.StripeError as exc:
        logger.warning("Stripe portal unavailable (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Portal temporariamente indisponível. Tente novamente em instantes.") from exc


def _subscription_id(event_type, obj):
    if event_type.startswith("customer.subscription."):
        return obj.get("id")
    direct = _object_id(obj.get("subscription"))
    # API Basil+ moved the invoice's subscription into parent details.
    details = (obj.get("parent") or {}).get("subscription_details") or {}
    return direct or _object_id(details.get("subscription"))


def _apply_subscription(tenant, subscription, event_created):
    if _object_id(subscription.get("customer")) != tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Assinatura não pertence à conta informada")
    if subscription.get("metadata", {}).get("tenant_id") != str(tenant.id):
        raise HTTPException(status_code=400, detail="Vínculo da assinatura inválido")
    if bool(subscription.get("livemode")) != settings.stripe_livemode:
        raise HTTPException(status_code=400, detail="Ambiente de assinatura inválido")
    items = (subscription.get("items") or {}).get("data", [])
    plan_valid = len(items) == 1 and _object_id(items[0].get("price")) == settings.stripe_price_id and items[0].get("quantity") == 1
    status = subscription.get("status", "unknown")
    tenant.stripe_subscription_id = subscription["id"]
    tenant.subscription_status = {"canceled": "cancelled", "incomplete_expired": "expired"}.get(status, status)
    if not plan_valid:
        tenant.subscription_status = "unsupported_plan"
    period_end = subscription.get("current_period_end") or (items[0].get("current_period_end") if items else None)
    tenant.current_period_end = _timestamp(period_end)
    if status == "trialing":
        tenant.trial_ends_at = _timestamp(subscription.get("trial_end"))
    if status == "past_due":
        # Derive grace from the current unpaid invoice, never an old event's
        # timestamp (events can arrive months out of order).
        invoice = subscription.get("latest_invoice") or {}
        failure_timestamp = invoice.get("created") if isinstance(invoice, dict) else None
        failure_at = min(_timestamp(failure_timestamp) or _now(), _now())
        tenant.past_due_since = min(tenant.past_due_since, failure_at) if tenant.past_due_since else failure_at
    elif status in {"active", "trialing"}:
        tenant.past_due_since = None


def process_stripe_event(event, db: Session):
    if bool(event.get("livemode")) != settings.stripe_livemode:
        raise HTTPException(status_code=400, detail="Ambiente do webhook inválido")
    event_type = event.get("type")
    if event_type not in _EVENTS:
        return {"received": True, "ignored": True}
    if not event.get("id"):
        raise HTTPException(status_code=400, detail="Evento inválido")
    obj = (event.get("data") or {}).get("object")
    if not isinstance(obj, dict):
        raise HTTPException(status_code=400, detail="Evento inválido")
    customer_id = _object_id(obj.get("customer"))
    sub_id = _subscription_id(event_type, obj)
    client = _stripe()
    with _billing_lock, system_scope(db):
        if db.query(BillingWebhookEvent).filter(BillingWebhookEvent.id == event["id"]).first():
            return {"received": True, "duplicate": True}
        tenant = db.query(Tenant).filter(Tenant.stripe_customer_id == customer_id).populate_existing().with_for_update().first() if customer_id else None
        try:
            db.add(BillingWebhookEvent(id=event["id"], event_type=event_type))
            db.flush()
            if tenant and sub_id:
                # An old canceled subscription must not overwrite a newer one.
                if tenant.stripe_subscription_id and tenant.stripe_subscription_id != sub_id:
                    current = client.v1.subscriptions.retrieve(tenant.stripe_subscription_id, {"expand": ["latest_invoice"]})
                    if current.get("status") not in _TERMINAL:
                        db.commit()
                        return {"received": True, "ignored": True}
                current = client.v1.subscriptions.retrieve(sub_id, {"expand": ["latest_invoice"]})
                _apply_subscription(tenant, current, event.get("created"))
            db.commit()
            return {"received": True}
        except IntegrityError:
            db.rollback()
            if db.query(BillingWebhookEvent).filter(BillingWebhookEvent.id == event["id"]).first():
                return {"received": True, "duplicate": True}
            raise
        except stripe.StripeError as exc:
            db.rollback()
            logger.warning("Stripe webhook retry required (%s)", type(exc).__name__)
            raise HTTPException(status_code=502, detail="Confirmação indisponível. Reenvie o webhook.") from exc


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not billing_configured():
        raise HTTPException(status_code=503, detail="Webhook indisponível")
    body = await request.body()
    if len(body) > 512 * 1024:
        raise HTTPException(status_code=413, detail="Evento muito grande")
    try:
        event = stripe.Webhook.construct_event(body, request.headers.get("stripe-signature", ""), settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Assinatura do webhook inválida") from exc
    return await run_in_threadpool(process_stripe_event, event, db)
