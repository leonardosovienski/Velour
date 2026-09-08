"""SaaS accounts, tenant ownership, credential revocation and billing ledger.

Revision ID: d9e64a3b2f10
Revises: c4f1a9d7e2b0
"""
from datetime import datetime, timedelta

from alembic import op
import sqlalchemy as sa

revision = "d9e64a3b2f10"
down_revision = "c4f1a9d7e2b0"
branch_labels = None
depends_on = None

TABLES = ["professionals", "users", "clients", "service_categories", "services", "products",
          "appointments", "referrals", "loyalty_transactions", "service_recipes", "stock_movements", "audit_logs"]
REFERENCES = {
    "users": {"professional_id": "professionals"},
    "clients": {"referred_by_id": "clients"},
    "services": {"category_id": "service_categories"},
    "appointments": {"client_id": "clients", "professional_id": "professionals", "service_id": "services"},
    "referrals": {"referrer_id": "clients", "referred_id": "clients"},
    "loyalty_transactions": {"client_id": "clients", "appointment_id": "appointments", "referral_id": "referrals"},
    "service_recipes": {"service_id": "services", "product_id": "products"},
    "stock_movements": {"product_id": "products", "appointment_id": "appointments"},
    "audit_logs": {"user_id": "users"},
}


def upgrade():
    # Login and recovery use normalized addresses. Refuse ambiguous historical
    # identities before changing schema, instead of silently locking users out.
    users = sa.table("users", sa.column("email", sa.String()))
    normalized_email = sa.func.lower(sa.func.trim(users.c.email))
    collisions = op.get_bind().execute(sa.select(sa.func.count()).select_from(users)
        .group_by(normalized_email).having(sa.func.count() > 1)).first()
    if collisions:
        raise RuntimeError("E-mails legados duplicados após normalização. Resolva os cadastros antes de executar esta migração.")
    op.execute(users.update().values(email=normalized_email))
    op.create_table("tenants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("subscription_status", sa.String(32), nullable=False),
        sa.Column("trial_ends_at", sa.DateTime()),
        sa.Column("current_period_end", sa.DateTime()),
        sa.Column("past_due_since", sa.DateTime()),
        sa.Column("stripe_customer_id", sa.String(255), unique=True),
        sa.Column("stripe_subscription_id", sa.String(255), unique=True),
        sa.Column("accepted_terms_at", sa.DateTime()),
        sa.Column("terms_version", sa.String(40)),
        sa.Column("checkout_session_id", sa.String(255)),
        sa.Column("checkout_session_expires_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
    now = datetime.utcnow()
    legacy = sa.table("tenants", sa.column("id", sa.Integer()), sa.column("name", sa.String()),
        sa.column("slug", sa.String()), sa.column("is_active", sa.Boolean()),
        sa.column("subscription_status", sa.String()), sa.column("trial_ends_at", sa.DateTime()),
        sa.column("created_at", sa.DateTime()))
    op.bulk_insert(legacy, [{"id": 1, "name": "Salão existente", "slug": "legacy",
        "is_active": True, "subscription_status": "trialing", "trial_ends_at": now + timedelta(days=14), "created_at": now}])
    # Explicit inserted ID must advance PostgreSQL's sequence before self-service signup.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("SELECT setval(pg_get_serial_sequence('tenants','id'), 1, true)")

    for name in TABLES:
        op.add_column(name, sa.Column("tenant_id", sa.Integer(), nullable=True))
        op.execute(sa.text(f"UPDATE {name} SET tenant_id = 1"))
        with op.batch_alter_table(name) as batch:
            batch.alter_column("tenant_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f"fk_{name}_tenant_id", "tenants", ["tenant_id"], ["id"])
            batch.create_unique_constraint(f"uq_{name}_tenant_id", ["tenant_id", "id"])
            batch.create_index(f"ix_{name}_tenant_id", ["tenant_id"])
    # Second pass: every referenced parent now has the composite unique key.
    for name, references in REFERENCES.items():
        with op.batch_alter_table(name) as batch:
            for column, parent in references.items():
                batch.create_foreign_key(f"fk_{name}_{column}_tenant", parent,
                    ["tenant_id", column], ["tenant_id", "id"])
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    naming = {"uq": "uq_%(table_name)s_%(column_0_name)s"}
    referral_constraint = next((item["name"] for item in sa.inspect(op.get_bind()).get_unique_constraints("clients")
                                if item["column_names"] == ["referral_code"]), None)
    with op.batch_alter_table("clients", naming_convention=naming) as batch:
        batch.drop_index("ix_clients_code")
        batch.create_index("ix_clients_code", ["code"], unique=False)
        batch.drop_constraint(referral_constraint or "uq_clients_referral_code", type_="unique")
        batch.create_unique_constraint("uq_clients_tenant_code", ["tenant_id", "code"])
        batch.create_unique_constraint("uq_clients_tenant_referral_code", ["tenant_id", "referral_code"])
    op.create_table("password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_password_reset_tokens_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"], name="fk_password_reset_tokens_user_id_tenant"),
    )
    op.create_index("ix_password_reset_tokens_tenant_id", "password_reset_tokens", ["tenant_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    op.create_table("billing_webhook_events",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    # Merging independently numbered salon data would destroy the tenant boundary.
    raise RuntimeError("Irreversible tenant migration: restore a verified pre-migration backup instead.")
