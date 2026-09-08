"""Host-only tenant support. No platform privilege is exposed over HTTP.

Examples:
  python platform_admin.py list
  python platform_admin.py suspend 4 --confirm-slug salao-ab12 --reason "Pedido do titular"
  python platform_admin.py resume 4 --confirm-slug salao-ab12 --reason "Solicitação resolvida"
Billing state remains exclusively controlled by Stripe and trial timestamps.
"""
import argparse
import json

from sqlalchemy import update

from database import system_session
from models import AuditLog, Tenant, User


def set_availability(db, tenant_id: int, *, active: bool, confirm_slug: str, reason: str):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).with_for_update().one_or_none()
    if not tenant or tenant.slug != confirm_slug:
        raise ValueError("Salão ou slug não confere; nenhuma alteração realizada.")
    if not reason.strip() or len(reason) > 300:
        raise ValueError("Informe o motivo com até 300 caracteres, sem dados pessoais.")
    tenant.is_active = active
    # Both suspension and restoration revoke previous access tokens.
    db.execute(update(User).where(User.tenant_id == tenant_id).values(token_version=User.token_version + 1))
    db.add(AuditLog(tenant_id=tenant_id, user_id=None, action="PLATFORM",
                    resource=f"tenant/{tenant_id}/{'resume' if active else 'suspend'}: {reason.strip()}",
                    status_code=200))
    db.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--limit", type=int, default=100)
    listing.add_argument("--offset", type=int, default=0)
    for name in ("suspend", "resume"):
        command = commands.add_parser(name)
        command.add_argument("tenant_id", type=int)
        command.add_argument("--confirm-slug", required=True)
        command.add_argument("--reason", required=True)
    args = parser.parse_args()
    with system_session() as db:
        if args.command == "list":
            if not 1 <= args.limit <= 500 or args.offset < 0:
                parser.error("limit deve ser 1–500 e offset >=0")
            tenants = db.query(Tenant).order_by(Tenant.id).offset(args.offset).limit(args.limit).all()
            print(json.dumps([{"id": t.id, "name": t.name, "slug": t.slug,
                               "is_active": t.is_active, "subscription_status": t.subscription_status}
                              for t in tenants], ensure_ascii=False, indent=2))
        else:
            try:
                set_availability(db, args.tenant_id, active=args.command == "resume",
                                 confirm_slug=args.confirm_slug, reason=args.reason)
            except ValueError as exc:
                parser.error(str(exc))
            print("Estado atualizado; usuários precisam entrar novamente. A assinatura não foi alterada.")


if __name__ == "__main__":
    main()
