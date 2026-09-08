"""Regression coverage for complimentary services and professional dashboards."""
from datetime import datetime, timedelta
from decimal import Decimal

from models.user import User, UserRole
from routers.appointments import complete_appointment
from routers.dashboard import kpis, today_summary, weekly_revenue
from routers.professionals import professional_dashboard, professional_stats
from routers.reports import revenue_report
from schemas.appointment import AppointmentComplete
from tests.conftest import make_appointment, make_category, make_client, make_professional, make_service


def _appointment(db, *, charged=None, status="scheduled"):
    client = make_client(db)
    professional = make_professional(db)
    category = make_category(db)
    service = make_service(db, category.id, price=100, points_reward=0)
    when = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    appointment = make_appointment(
        db, client.id, professional.id, service.id,
        scheduled_at=when, ends_at=when + timedelta(hours=1), status=status,
    )
    appointment.price_charged = charged
    db.commit()
    return appointment


def test_complimentary_completion_preserves_zero_charge(db):
    appointment = _appointment(db)
    complete_appointment(
        appointment.id, AppointmentComplete(price_charged=Decimal("0.00")),
        db=db, current_user=User(role=UserRole.admin),
    )
    assert appointment.price_charged == Decimal("0.00")
    assert appointment.client.total_spent == Decimal("0.00")
    assert appointment.points_awarded == 0
    assert appointment.client.total_visits == 1


def test_zero_charge_does_not_inflate_revenue_or_commission(db):
    appointment = _appointment(db, charged=Decimal("0.00"), status="completed")
    assert today_summary(db=db, _=None)["revenue_today"] == 0
    assert kpis(period="day", db=db, _=None)["revenue"] == 0
    assert all(day["revenue"] == 0 for day in weekly_revenue(db=db, _=None))
    stats = professional_stats(appointment.professional_id, db=db, _=None)
    assert stats["revenue_this_month"] == stats["commission_this_month"] == 0
    dashboard = professional_dashboard(appointment.professional_id, db=db, _=None)
    assert dashboard["monthly_goal"]["revenue"] == dashboard["monthly_goal"]["commission"] == 0
    report = revenue_report(db=db, _=None)
    assert report["total_revenue"] == 0
    assert report["total_appointments"] == 1
    for group in ("by_professional", "by_category", "by_gender"):
        assert len(report[group]) == 1
        assert report[group][0]["revenue"] == 0


def test_professional_kpis_count_only_linked_clients(db):
    appointment = _appointment(db, charged=Decimal("25.00"), status="completed")
    other_client = make_client(db, name="Other client", code="VLR-00002", referral_code="OTHER")
    other_professional = make_professional(db, name="Other professional")
    make_appointment(db, other_client.id, other_professional.id, appointment.service_id,
                     scheduled_at=appointment.scheduled_at, status="completed")
    # Multiple visits from one client must not inflate the distinct client count.
    make_appointment(db, appointment.client_id, appointment.professional_id, appointment.service_id,
                     scheduled_at=appointment.scheduled_at - timedelta(days=1))
    db.commit()
    user = User(role=UserRole.professional, professional_id=appointment.professional_id)
    result = kpis(period="day", db=db, _=user)
    assert result["active_clients"] == result["completed_appointments"] == 1
    assert result["revenue"] == Decimal("25.00")
    assert result["points_issued"] == 0
    unlinked = kpis(period="day", db=db, _=User(role=UserRole.professional))
    assert unlinked["active_clients"] == unlinked["completed_appointments"] == 0
