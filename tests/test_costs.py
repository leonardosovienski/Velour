from datetime import datetime
from decimal import Decimal

from database import tenant_scope
from models import Appointment, AppointmentStatus, CostBudget, Product, Service, ServiceRecipe, User, UserRole
from tests.test_accounting import prepare
from tests.test_tenancy import tenant_api, isolated_accounts, headers  # noqa: F401

RENT = {'description': 'Aluguel de setembro', 'category': 'rent', 'amount': '50.00', 'due_date': '2026-09-05', 'paid_on': '2026-09-05'}


def with_recipe(factory, account):
    """Ficha técnica do serviço: 40 unidades de Tintura (R$ 0,50) = custo-padrão de R$ 20,00."""
    with factory() as db:
        tenant_scope(db, account['tenant'])
        product = db.query(Product).filter(Product.name == 'Tintura').one()
        db.add(ServiceRecipe(service_id=account['service'], product_id=product.id, qty_consumed=40))
        db.commit()


def test_contribution_margin_break_even_and_dre_agree(tenant_api):
    api, factory, (a, b) = tenant_api
    prepare(factory, a)
    with_recipe(factory, a)
    auth = headers(a)
    assert api.post('/finance/expenses', json=RENT, headers=auth).status_code == 201
    data = api.get('/costs/report?month=2026-09', headers=auth).json()
    summary = data['summary']
    # Receita 200; variáveis = insumos 20 + comissão 80 + ISS 4; fixos = aluguel 50.
    assert summary['revenue'] == 200 and summary['variable_costs'] == 104
    assert summary['contribution_margin'] == 96 and summary['contribution_margin_ratio'] == 0.48
    assert summary['fixed_costs'] == 50 and summary['result'] == 46
    assert summary['break_even_revenue'] == 104.17 and summary['break_even_appointments'] == 1
    assert summary['safety_margin'] == 0.4792 and summary['average_ticket'] == 200 and summary['cost_per_appointment'] == 154
    # O resultado gerencial é o mesmo da DRE quando o consumo é baixado no mês do atendimento.
    assert summary['result'] == api.get('/accounting/report?month=2026-09', headers=auth).json()['result']
    lines = {line['category']: line for line in data['lines']}
    assert [lines[k]['actual'] for k in ('inputs', 'commissions', 'taxes', 'rent')] == [20, 80, 4, 50]
    assert all(line['status'] == 'no_budget' for line in data['lines']) and data['budget_total'] is None
    [service] = data['services']
    assert service['name'] == 'Alpha service' and service['appointments'] == 1
    assert service['contribution_margin'] == 96 and service['margin_ratio'] == 0.48
    [professional] = data['professionals']
    assert professional['commissions'] == 80 and professional['commission_rate'] == 0.4
    [standard] = data['standard_costs']
    assert standard['price'] == 100 and standard['standard_input_cost'] == 20 and standard['recipe_items'] == 1
    assert standard['margin_before_commission'] == 78 and standard['input_ratio'] == 0.2
    assert [row['month'] for row in data['history']] == ['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
    assert data['history'][-1]['result'] == 46 and data['history'][0]['revenue'] == 0
    assert data['alerts'] == []
    # Outro salão não vê os números nem a ficha técnica do primeiro.
    other = api.get('/costs/report?month=2026-09', headers=headers(b)).json()
    assert other['summary']['revenue'] == 0 and other['services'] == []
    assert [row['name'] for row in other['standard_costs']] == ['Beta service']


def test_empty_month_does_not_invent_ratios(tenant_api):
    api, _, (a, _) = tenant_api
    summary = api.get('/costs/report?month=2026-01', headers=headers(a)).json()['summary']
    assert summary['revenue'] == 0 and summary['appointments'] == 0
    assert summary['contribution_margin_ratio'] is None and summary['average_ticket'] is None
    # Sem custos fixos não há o que cobrir; sem receita não há margem de segurança.
    assert summary['break_even_revenue'] == 0 and summary['break_even_appointments'] == 0
    assert summary['safety_margin'] is None
    assert api.get('/costs/report?month=2026-13', headers=headers(a)).status_code == 422
    assert api.get('/costs/report?month=0000-01', headers=headers(a)).status_code == 422
    assert api.get('/costs/report?month=0001-03', headers=headers(a)).status_code == 200


def test_fixed_costs_without_margin_have_no_break_even(tenant_api):
    api, _, (a, _) = tenant_api
    assert api.post('/finance/expenses', json=RENT, headers=headers(a)).status_code == 201
    data = api.get('/costs/report?month=2026-09', headers=headers(a)).json()
    assert data['summary']['break_even_revenue'] is None and data['summary']['break_even_appointments'] is None
    assert data['summary']['result'] == -50
    assert any('ponto de equilíbrio' in alert['message'] for alert in data['alerts'])


def test_budget_replaces_month_and_flags_overruns(tenant_api):
    api, factory, (a, b) = tenant_api
    prepare(factory, a)
    auth = headers(a)
    body = {'items': [{'category': 'commissions', 'amount': '60.00'}, {'category': 'inputs', 'amount': '30'},
                      {'category': 'rent', 'amount': '0'}]}
    saved = api.put('/costs/budget?month=2026-09', json=body, headers=auth)
    assert saved.status_code == 200
    assert [item['category'] for item in saved.json()['items']] == ['inputs', 'commissions', 'rent']
    data = api.get('/costs/report?month=2026-09', headers=auth).json()
    lines = {line['category']: line for line in data['lines']}
    assert lines['commissions']['status'] == 'over' and lines['commissions']['variance'] == 20
    assert lines['commissions']['consumed_ratio'] == 1.3333
    assert lines['inputs']['status'] == 'within' and lines['inputs']['variance'] == -10
    assert lines['rent']['status'] == 'within' and lines['rent']['budget'] == 0
    assert data['budget_total'] == 90
    assert 'Comissões de profissionais acima do orçamento em R$ 20,00.' in [alert['message'] for alert in data['alerts']]
    # PUT substitui a lista inteira: linhas omitidas deixam de ter orçamento.
    assert api.put('/costs/budget?month=2026-09', json={'items': [{'category': 'inputs', 'amount': '25'}]}, headers=auth).status_code == 200
    with factory() as db:
        tenant_scope(db, a['tenant'])
        assert [(row.category, row.amount) for row in db.query(CostBudget).all()] == [('inputs', Decimal('25.00'))]
    # Orçamento é por salão e por mês.
    assert all(line['budget'] is None for line in api.get('/costs/report?month=2026-09', headers=headers(b)).json()['lines'])
    assert all(line['budget'] is None for line in api.get('/costs/report?month=2026-10', headers=auth).json()['lines'])


def test_budget_validation(tenant_api):
    api, _, (a, _) = tenant_api
    auth = headers(a)
    for body in ({'items': [{'category': 'rent', 'amount': '1'}, {'category': 'rent', 'amount': '2'}]},
                 {'items': [{'category': 'rent', 'amount': '-1'}]},
                 {'items': [{'category': 'marketing', 'amount': '1'}]},
                 {'items': [{'category': 'rent', 'amount': '1.001'}]},
                 {'items': [], 'tenant_id': 99}):
        assert api.put('/costs/budget?month=2026-09', json=body, headers=auth).status_code == 422, body
    assert api.put('/costs/budget?month=2026-9', json={'items': []}, headers=auth).status_code == 422
    assert api.put('/costs/budget?month=2026-09', json={'items': []}, headers=auth).json() == {'month': '2026-09', 'items': []}


def test_negative_margin_and_price_below_recipe_are_flagged(tenant_api):
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(Appointment, a['appointment']).price_charged = Decimal('30.00')
        db.get(Service, a['service']).price = Decimal('15.00')
        db.commit()
    with_recipe(factory, a)
    messages = [alert['message'] for alert in api.get('/costs/report?month=2026-09', headers=headers(a)).json()['alerts']]
    assert 'Alpha service teve margem de contribuição negativa no mês.' in messages
    assert 'O preço de Alpha service não cobre insumos e ISS da ficha técnica.' in messages
    assert any(message.startswith('Resultado negativo') for message in messages)


def test_inputs_follow_the_appointment_month(tenant_api):
    """Consumo baixado no mês seguinte continua no custo do atendimento que o gerou."""
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        appointment = db.get(Appointment, a['appointment'])
        appointment.scheduled_at = datetime(2026, 8, 31, 18)
        db.commit()
    august = api.get('/costs/report?month=2026-08', headers=headers(a)).json()
    assert {line['category']: line['actual'] for line in august['lines']}['inputs'] == 20
    september = api.get('/costs/report?month=2026-09', headers=headers(a)).json()
    assert {line['category']: line['actual'] for line in september['lines']}['inputs'] == 0
    assert september['history'][-2]['variable_costs'] == august['summary']['variable_costs']


def test_csv_download_escapes_formulas(tenant_api):
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(Service, a['service']).name = '=HYPERLINK("http://example.com")'
        db.commit()
    result = api.get('/costs/report/download?month=2026-09', headers=headers(a))
    assert result.status_code == 200 and result.headers['content-type'].startswith('text/csv')
    assert 'velour-custos-2026-09.csv' in result.headers['content-disposition']
    assert result.headers['cache-control'] == 'no-store'
    assert result.text.startswith('﻿Velour — gestão de custos;2026-09')
    assert ';200,00;' in result.text and '\'=HYPERLINK' in result.text
    assert 'Margem de contribuição;96,00' in result.text and 'sem orçamento' in result.text
    assert '\n=HYPERLINK' not in result.text and ';=HYPERLINK' not in result.text


def test_professional_cannot_read_or_budget_costs(tenant_api):
    api, factory, (a, _) = tenant_api
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(User, a['user']).role = UserRole.professional
        db.commit()
    auth = headers(a)
    assert api.get('/costs/report?month=2026-09', headers=auth).status_code == 403
    assert api.get('/costs/report/download?month=2026-09', headers=auth).status_code == 403
    assert api.put('/costs/budget?month=2026-09', json={'items': []}, headers=auth).status_code == 403
    assert api.get('/costs/report?month=2026-09').status_code == 401


def test_budget_is_exported_with_the_salon(tenant_api):
    api, _, (a, _) = tenant_api
    auth = headers(a)
    api.put('/costs/budget?month=2026-09', json={'items': [{'category': 'people', 'amount': '1200.50'}]}, headers=auth)
    exported = api.get('/tenants/export', headers=auth).json()['data']['cost_budgets']
    assert [(row['month'], row['category'], row['amount']) for row in exported] == [('2026-09', 'people', 1200.5)]


def test_completed_status_is_required(tenant_api):
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(Appointment, a['appointment']).status = AppointmentStatus.cancelled
        db.commit()
    summary = api.get('/costs/report?month=2026-09', headers=headers(a)).json()['summary']
    assert summary['revenue'] == 0 and summary['variable_costs'] == 0


def test_zero_price_month_without_expenses(tenant_api):
    """Cortesias (valor zero) sem despesas não podem dividir zero por zero."""
    api, factory, (a, _) = tenant_api
    prepare(factory, a)
    with factory() as db:
        tenant_scope(db, a['tenant'])
        db.get(Appointment, a['appointment']).price_charged = Decimal('0.00')
        db.commit()
    result = api.get('/costs/report?month=2026-09', headers=headers(a))
    assert result.status_code == 200
    summary = result.json()['summary']
    assert summary['appointments'] == 1 and summary['revenue'] == 0 and summary['average_ticket'] == 0
    assert summary['break_even_revenue'] == 0 and summary['break_even_appointments'] == 0
    assert summary['contribution_margin_ratio'] is None and summary['safety_margin'] is None
    assert api.get('/costs/report/download?month=2026-09', headers=headers(a)).status_code == 200
