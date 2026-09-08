"""Exercise independent request/job sessions against the same durable database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
import time

from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base, ScopedSession, system_scope, tenant_scope
from models import Appointment, Client, LoyaltyTransaction, Product, ServiceRecipe, StockMovement, User, UserRole
from routers.appointments import complete_appointment, update_status
from routers.products import move_stock
from schemas.appointment import AppointmentComplete, AppointmentStatusUpdate
from schemas.product import StockEntry
from tests.tenancy_helpers import seed_two_tenants


def test_completion_birthday_and_stock_share_atomic_mutation_boundary(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=ScopedSession, autoflush=False)
    a, b = seed_two_tenants(factory)
    with factory() as db:
        tenant_scope(db, a["tenant"])
        client = db.get(Client, a["client"])
        client.birthdate = date.today().replace(year=1990)
        product = Product(name="Shared stock", stock_qty=100, min_stock=0, unit="ml")
        db.add(product)
        db.flush()
        product_id = product.id
        db.add(ServiceRecipe(product_id=product_id, service_id=a["service"], qty_consumed=10))
        second = Appointment(client_id=a["client"], professional_id=a["professional"], service_id=a["service"],
            scheduled_at=datetime(2030, 1, 2, 10), ends_at=datetime(2030, 1, 2, 11))
        db.add(second)
        db.commit()
        second_id = second.id

    # Widen the read/update window so a missing common lock produces lost
    # balances rather than depending on fortunate thread scheduling.
    @event.listens_for(engine, "after_cursor_execute")
    def slow_balance_reads(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT") and ("clients" in statement or "products" in statement):
            time.sleep(0.005)

    def complete(appt_id):
        with factory() as db:
            tenant_scope(db, a["tenant"])
            return complete_appointment(appt_id, AppointmentComplete(price_charged=100), db=db,
                                        current_user=User(role=UserRole.admin)).id

    def stock():
        with factory() as db:
            tenant_scope(db, a["tenant"])
            move_stock(product_id, StockEntry(type="purchase", qty=5), db=db, _=None)

    import birthday_scheduler
    monkeypatch.setattr(birthday_scheduler, "SessionLocal", factory)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(complete, a["appointment"]), pool.submit(complete, second_id),
                   pool.submit(birthday_scheduler._run_birthday_job), pool.submit(stock)]
        for future in futures:
            future.result(timeout=15)
    birthday_scheduler._run_birthday_job()  # a second run cannot award twice
    with factory() as db:
        tenant_scope(db, a["tenant"])
        client = db.get(Client, a["client"])
        assert client.loyalty_points == 300
        assert client.total_visits == 2
        assert float(client.total_spent) == 200
        assert db.query(LoyaltyTransaction).count() == 3
        assert db.get(Product, product_id).stock_qty == 85
        ledger = db.query(StockMovement).order_by(StockMovement.id).all()
        assert len(ledger) == 3
        assert ledger[0].qty_before == 100
        assert all(first.qty_after == second.qty_before for first, second in zip(ledger, ledger[1:]))
        assert ledger[-1].qty_after == 85
        with pytest.raises(HTTPException) as error:
            update_status(a["appointment"], AppointmentStatusUpdate(status="scheduled"), db=db,
                          current_user=User(role=UserRole.admin))
        assert error.value.status_code == 409
    engine.dispose()


def test_concurrent_admin_deactivations_keep_one_active_owner(tmp_path):
    from auth import hash_password
    from routers.users import update_user
    from schemas.user import UserUpdate
    engine = create_engine(f"sqlite:///{tmp_path / 'admins.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, class_=ScopedSession, autoflush=False)
    a, b = seed_two_tenants(factory)
    with factory() as db:
        tenant_scope(db, a["tenant"])
        second = User(name="Second owner", email="second-owner@example.com", role=UserRole.admin,
                      hashed_password=hash_password("long-test-password"))
        db.add(second)
        db.commit()
        second_id = second.id

    def disable(target_id):
        with factory() as db:
            tenant_scope(db, a["tenant"])
            try:
                update_user(target_id, UserUpdate(is_active=False), db=db, current_user=User(role=UserRole.admin))
                return 200
            except HTTPException as error:
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(disable, [a["user"], second_id]))
    assert statuses == [200, 409]
    with factory() as db:
        tenant_scope(db, a["tenant"])
        assert db.query(User).filter(User.role == UserRole.admin, User.is_active == True).count() == 1
    engine.dispose()
