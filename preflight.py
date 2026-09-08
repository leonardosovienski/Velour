"""Read-only release checks. Never emits credentials or changes provider data."""
import argparse
import json
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Require live billing and public registration")
    parser.add_argument("--services", action="store_true", help="Also connect to DB and read the Stripe Price")
    args = parser.parse_args()
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})

    try:
        from config import settings
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"ready": False, "configuration_error": str(exc)}, ensure_ascii=False))
        return 1

    check("production_environment", settings.environment == "production")
    check("postgresql", settings.database_url.startswith("postgresql+psycopg://"))
    check("explicit_migrations", not settings.auto_create_tables)
    check("https_app_url", urlsplit(settings.app_url).scheme == "https")
    check("transactional_email_configured", settings.smtp_host and settings.smtp_from and settings.smtp_use_tls)
    check("published_terms_and_privacy", settings.terms_url and settings.privacy_url)
    check("stripe_configured", settings.stripe_secret_key and settings.stripe_webhook_secret and settings.stripe_price_id)
    if args.strict:
        check("public_registration_enabled", settings.signup_enabled)
        check("live_billing", settings.stripe_livemode and settings.stripe_secret_key.startswith(("sk_live_", "rk_live_")))

    if args.services:
        try:
            from database import engine
            from sqlalchemy import inspect, text
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
            with engine.connect() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                check("database_migration_at_head", revision == head)
                check("tenant_schema_present", "tenants" in inspect(connection).get_table_names())
        except Exception:
            check("database_connection_and_migration", False)
        try:
            import stripe
            client = stripe.StripeClient(settings.stripe_secret_key, max_network_retries=1,
                                         http_client=stripe.RequestsClient(timeout=15))
            price = client.v1.prices.retrieve(settings.stripe_price_id)
            recurring = price.get("recurring") or {}
            check("stripe_monthly_price", price.get("active") and recurring.get("interval") == "month" and recurring.get("interval_count") == 1)
            check("stripe_mode_matches", price.get("livemode") == settings.stripe_livemode)
        except Exception:
            check("stripe_price_accessible", False)
    ready = all(item["ok"] for item in checks)
    print(json.dumps({"ready": ready, "checks": checks,
                      "requires_operational_evidence": ["HTTPS acessível", "webhook e pagamento de teste", "e-mail entregue", "restauração de backup", "termos da empresa publicados"]},
                     ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
