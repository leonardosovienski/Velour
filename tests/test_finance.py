from datetime import datetime, date, timedelta
from decimal import Decimal

from database import tenant_scope
from models import Appointment, AppointmentStatus, User, UserRole
from tests.test_tenancy import tenant_api, isolated_accounts, headers  # noqa: F401


def complete(factory, account, month='2026-09-15'):
    with factory() as db:
        tenant_scope(db, account['tenant'])
        a = db.get(Appointment, account['appointment'])
        a.status = AppointmentStatus.completed
        a.scheduled_at = datetime.fromisoformat(month + 'T10:00:00')
        a.price_charged = Decimal('101.10')
        db.commit()


def test_finance_month_settlement_and_fiscal_independence(tenant_api):
    api, factory, (a, b) = tenant_api
    complete(factory, a)
    complete(factory, b)
    auth = headers(a)
    data = api.get('/finance/overview?month=2026-09', headers=auth).json()
    assert data['receivable'] == 101.1 and data['received'] == 0
    assert [r['id'] for r in data['receipts']] == [a['appointment']]
    assert api.get('/finance/overview?month=2026-08', headers=auth).json()['receipts'] == []
    path = f"/finance/receipts/{a['appointment']}/settle"
    for _ in range(2):
        result = api.post(path, json={'payment_method': 'pix'}, headers=auth)
        assert result.status_code == 200, result.text
    data = api.get('/finance/overview?month=2026-09', headers=auth).json()
    assert data['received'] == 101.1 and data['receivable'] == 0
    assert data['receipts'][0]['document_id'] is None
    with factory() as db:
        tenant_scope(db, a['tenant'])
        assert db.get(Appointment, a['appointment']).points_awarded == 0
    assert api.post(f"/finance/receipts/{b['appointment']}/settle", json={'payment_method': 'pix'}, headers=auth).status_code == 404
    assert api.get('/finance/overview?month=2026-13', headers=auth).status_code == 422
    assert api.get('/finance/overview?month=0000-01', headers=auth).status_code == 422


def test_expenses_tenant_permissions_pay_and_export(tenant_api):
    api, factory, (a, b) = tenant_api
    auth = headers(a)
    body = {'description': 'Produtos para salão', 'category': 'supplies', 'amount': '20.10', 'due_date': '2026-09-15'}
    response = api.post('/finance/expenses', json=body, headers=auth)
    assert response.status_code == 201, response.text
    expense = response.json()
    assert api.get('/finance/overview?month=2026-09', headers=headers(b)).json()['expenses'] == []
    path = f"/finance/expenses/{expense['id']}/pay"
    assert api.post(path, json={'paid_on': date.today().isoformat()}, headers=headers(b)).status_code == 404
    assert api.post(path, json={'paid_on': (date.today() + timedelta(days=1)).isoformat()}, headers=auth).status_code == 422
    for _ in range(2):
        assert api.post(path, json={'paid_on': date.today().isoformat()}, headers=auth).status_code == 200
    data = api.get('/finance/overview?month=2026-09', headers=auth).json()
    assert data['expenses_paid'] == 20.1 and data['expenses_pending'] == 0 and data['balance'] == -20.1
    assert api.get('/tenants/export', headers=auth).json()['data']['expenses'][0]['id'] == expense['id']
    for value in ('0', '-10', '1.001'):
        assert api.post('/finance/expenses', json={**body, 'amount': value}, headers=auth).status_code == 422
    assert api.post('/finance/expenses', json={**body, 'tenant_id': b['tenant']}, headers=auth).status_code == 422
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(User, a['user']).role = UserRole.professional
        db.commit()
    assert api.get('/finance/overview?month=2026-09', headers=auth).status_code == 403
    assert api.post('/finance/expenses', json=body, headers=auth).status_code == 403


def test_partial_receipt_and_uncompleted_guard(tenant_api):
    api, factory, (a, b) = tenant_api
    assert api.post(f"/finance/receipts/{a['appointment']}/settle", json={'payment_method': 'pix'}, headers=headers(a)).status_code == 409
    complete(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        row = db.get(Appointment, a['appointment'])
        row.paid = True
        row.amount_paid = Decimal('50.00')
        db.commit()
    data = api.get('/finance/overview?month=2026-09', headers=headers(a)).json()
    assert data['received'] == 50 and data['receivable'] == 51.1
    assert api.post(f"/finance/receipts/{a['appointment']}/settle", json={'payment_method': 'cash'}, headers=headers(a)).status_code == 200
    assert api.get('/finance/overview?month=2026-09', headers=headers(a)).json()['received'] == 101.1
