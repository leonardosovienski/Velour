from datetime import datetime
from decimal import Decimal

from database import tenant_scope
from models import Appointment, AppointmentStatus, FiscalProfile, Product, Professional, StockMovement, User, UserRole
from models.stock_movement import StockMovementType
from tests.test_tenancy import tenant_api, isolated_accounts, headers  # noqa: F401


def prepare(factory, account):
    with factory() as db:
        tenant_scope(db, account['tenant'])
        a = db.get(Appointment, account['appointment'])
        a.status = AppointmentStatus.completed
        a.scheduled_at = datetime(2026, 9, 15, 10)
        a.price_charged = Decimal('200.00')
        a.paid = True
        a.amount_paid = Decimal('150.00')
        db.get(Professional, account['professional']).commission_rate = Decimal('0.40')
        product = Product(name='Tintura', cost_per_unit=Decimal('0.50'), stock_qty=100)
        db.add_all([product, FiscalProfile(data={'iss_rate': '2.00'})])
        db.flush()
        db.add(StockMovement(product_id=product.id, appointment_id=a.id, type=StockMovementType.consumption, qty=-40,
                             qty_before=100, qty_after=60, description='Consumo', created_at=datetime(2026, 9, 15, 11)))
        db.commit()


def test_dre_journal_and_trial_balance_are_consistent(tenant_api):
    api, factory, (a, b) = tenant_api
    prepare(factory, a)
    auth = headers(a)
    body = {'description': 'Aluguel de setembro', 'category': 'rent', 'amount': '50.00', 'due_date': '2026-09-05', 'paid_on': '2026-09-05'}
    assert api.post('/finance/expenses', json=body, headers=auth).status_code == 201
    data = api.get('/accounting/report?month=2026-09', headers=auth).json()
    dre = {row['label']: row['value'] for row in data['dre']}
    assert dre['Receita bruta de serviços'] == 200
    assert dre['(-) ISS estimado'] == -4
    assert dre['(-) Custo de insumos consumidos'] == -20
    assert dre['(-) Comissões de profissionais'] == -80
    assert dre['Lucro bruto'] == 96
    assert dre['(-) Aluguel'] == -50
    assert dre['Resultado do período'] == 46 == data['result']
    assert data['total_debit'] == data['total_credit']
    balances = {row['code']: row['balance'] for row in data['trial_balance']}
    assert balances['1.1.1'] == 100  # 150 recebidos - 50 de aluguel
    assert balances['1.1.2'] == 50
    assert all(row['debit'] != row['credit'] for row in data['entries']) and len(data['entries']) == 7
    # Outro salão não enxerga os dados, e mês vazio não inventa lançamentos.
    other = api.get('/accounting/report?month=2026-09', headers=headers(b)).json()
    assert other['entries'] == [] and other['result'] == 0
    assert api.get('/accounting/report?month=2026-13', headers=auth).status_code == 422


def test_downloads_txt_and_pdf(tenant_api):
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    auth = headers(a)
    txt = api.get('/accounting/report/download?month=2026-09&format=txt', headers=auth)
    assert txt.status_code == 200 and txt.headers['content-type'].startswith('text/plain')
    assert 'velour-contabil-2026-09.txt' in txt.headers['content-disposition']
    assert 'SEM VALIDADE' in txt.text and 'BALANCETE' in txt.text and 'Débitos = créditos: sim' in txt.text
    pdf = api.get('/accounting/report/download?month=2026-09&format=pdf', headers=auth)
    assert pdf.status_code == 200 and pdf.headers['content-type'] == 'application/pdf'
    assert pdf.content.startswith(b'%PDF-1.4') and pdf.content.rstrip().endswith(b'%%EOF')
    assert api.get('/accounting/report/download?month=2026-09&format=docx', headers=auth).status_code == 422


def test_professional_cannot_read_accounting(tenant_api):
    api, factory, (a, _) = tenant_api
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(User, a['user']).role = UserRole.professional
        db.commit()
    assert api.get('/accounting/report?month=2026-09', headers=headers(a)).status_code == 403
    assert api.get('/accounting/report/download?month=2026-09', headers=headers(a)).status_code == 403
