"""Gestão de custos gerencial: custeio variável, margem de contribuição, ponto de equilíbrio e orçamento.

Os valores são calculados a partir dos atendimentos concluídos, da ficha técnica, do consumo de estoque e das
despesas. Só o orçamento mensal é gravado. É uma visão gerencial para decisão, não contabilidade de custos oficial.
"""
import csv
import io
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_CEILING
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session, joinedload, selectinload

from auth import require_manager
from database import get_db
from domain_locks import serialized_mutation
from models import (
    Appointment, AppointmentStatus, CostBudget, Expense, Product, Service, ServiceRecipe, StockMovement,
)
from models.stock_movement import StockMovementType
from routers.accounting import MONTH, cents, estimated_iss_rate, money, month_bounds

router = APIRouter(prefix='/costs', tags=['costs'])
NOTICE = ('Visão gerencial calculada a partir dos registros do Velour. Insumos pelo custo cadastrado do produto, '
          'ISS pela alíquota do cadastro fiscal demonstrativo. Não substitui contabilidade de custos oficial.')
RATIO = Decimal('0.0001')
HISTORY_MONTHS = 6

# Linhas de custo: variáveis acompanham cada atendimento; fixas vêm das despesas pelo vencimento.
COST_LINES = OrderedDict([
    ('inputs', ('Insumos consumidos', 'variable')),
    ('commissions', ('Comissões de profissionais', 'variable')),
    ('taxes', ('ISS estimado', 'variable')),
    ('rent', ('Aluguel', 'fixed')),
    ('supplies', ('Produtos e materiais', 'fixed')),
    ('utilities', ('Contas e serviços', 'fixed')),
    ('people', ('Equipe', 'fixed')),
    ('other', ('Outras despesas', 'fixed')),
])
SUMMARY_LABELS = {
    'appointments': 'Atendimentos concluídos', 'revenue': 'Receita', 'variable_costs': 'Custos variáveis',
    'contribution_margin': 'Margem de contribuição', 'contribution_margin_ratio': 'Índice de margem de contribuição',
    'fixed_costs': 'Custos fixos', 'result': 'Resultado', 'average_ticket': 'Ticket médio',
    'cost_per_appointment': 'Custo por atendimento', 'break_even_revenue': 'Ponto de equilíbrio (R$)',
    'break_even_appointments': 'Ponto de equilíbrio (atendimentos)', 'safety_margin': 'Margem de segurança',
}
STATUS_LABELS = {'within': 'dentro do orçamento', 'over': 'acima do orçamento', 'no_budget': 'sem orçamento'}
CostCategory = Literal['inputs', 'commissions', 'taxes', 'rent', 'supplies', 'utilities', 'people', 'other']


class BudgetItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: CostCategory
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BudgetInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: list[BudgetItem] = Field(max_length=len(COST_LINES))

    @field_validator('items')
    @classmethod
    def unique_categories(cls, items):
        if len({item.category for item in items}) != len(items):
            raise ValueError('Cada linha de custo pode aparecer uma vez')
        return items


def shift_month(start: date, months: int) -> date:
    year, month = divmod(start.year * 12 + start.month - 1 + months, 12)
    return date(year, month + 1, 1) if year >= 1 else date(1, 1, 1)


def month_key(day: date) -> str:
    return f'{day.year:04d}-{day.month:02d}'


def ratio(part: Decimal, whole: Decimal):
    return (part / whole).quantize(RATIO) if whole > 0 else None


def parse_month(month: str):
    try:
        return month_bounds(month)
    except ValueError:
        raise HTTPException(422, 'Mês inválido')


def budget_items(db: Session, month: str) -> list[dict]:
    rows = {row.category: row.amount for row in db.query(CostBudget).filter(CostBudget.month == month).all()}
    return [{'category': key, 'label': label, 'amount': cents(rows[key])}
            for key, (label, _) in COST_LINES.items() if key in rows]


def build_cost_report(db: Session, month: str) -> dict:
    start, end = parse_month(month)
    window_start = shift_month(start, -(HISTORY_MONTHS - 1))
    window_dt, end_dt = datetime.combine(window_start, datetime.min.time()), datetime.combine(end, datetime.min.time())
    iss_rate = estimated_iss_rate(db)

    appointments = (db.query(Appointment)
                    .options(joinedload(Appointment.service).joinedload(Service.category), joinedload(Appointment.professional))
                    .filter(Appointment.status == AppointmentStatus.completed,
                            Appointment.scheduled_at >= window_dt, Appointment.scheduled_at < end_dt)
                    .order_by(Appointment.scheduled_at, Appointment.id).all())
    # Insumos seguem o atendimento que os consumiu (competência), não a data do movimento de estoque.
    inputs_by_appointment = defaultdict(lambda: Decimal('0'))
    consumption = (db.query(StockMovement, Product)
                   .join(Product, Product.id == StockMovement.product_id)
                   .join(Appointment, Appointment.id == StockMovement.appointment_id)
                   .filter(StockMovement.type == StockMovementType.consumption,
                           Appointment.status == AppointmentStatus.completed,
                           Appointment.scheduled_at >= window_dt, Appointment.scheduled_at < end_dt).all())
    for movement, product in consumption:
        inputs_by_appointment[movement.appointment_id] += Decimal(str(-movement.qty)) * Decimal(product.cost_per_unit or 0)
    expenses = db.query(Expense).filter(Expense.due_date >= window_start, Expense.due_date < end).all()

    history = OrderedDict()
    cursor = window_start
    while cursor < end:
        history[month_key(cursor)] = {'revenue': Decimal('0'), 'inputs': Decimal('0'), 'commissions': Decimal('0'),
                                      'fixed': OrderedDict((k, Decimal('0')) for k, (_, kind) in COST_LINES.items() if kind == 'fixed'),
                                      'appointments': 0}
        cursor = shift_month(cursor, 1)

    services, professionals = OrderedDict(), OrderedDict()
    for a in appointments:
        price = cents(a.price_charged if a.price_charged is not None else a.service.price)
        commission = cents(price * (a.professional.commission_rate or 0))
        inputs = cents(inputs_by_appointment[a.id])
        bucket = history[month_key(a.scheduled_at.date())]
        bucket['revenue'] += price
        bucket['inputs'] += inputs
        bucket['commissions'] += commission
        bucket['appointments'] += 1
        if a.scheduled_at < datetime.combine(start, datetime.min.time()):
            continue
        for groups, key, base in ((services, a.service_id, {'name': a.service.name, 'category': a.service.category.name}),
                                  (professionals, a.professional_id, {'name': a.professional.name,
                                                                     'commission_rate': Decimal(a.professional.commission_rate or 0)})):
            row = groups.setdefault(key, {'id': key, **base, 'appointments': 0, 'revenue': Decimal('0'),
                                          'inputs': Decimal('0'), 'commissions': Decimal('0')})
            row['appointments'] += 1
            row['revenue'] += price
            row['inputs'] += inputs
            row['commissions'] += commission
    for e in expenses:
        history[month_key(e.due_date)]['fixed'][e.category] += cents(e.amount)

    def close(row):
        row['taxes'] = cents(row['revenue'] * iss_rate / 100)
        row['contribution_margin'] = row['revenue'] - row['inputs'] - row['commissions'] - row['taxes']
        row['margin_ratio'] = ratio(row['contribution_margin'], row['revenue'])
        return row

    current = history[month]
    revenue, count = current['revenue'], current['appointments']
    actual = OrderedDict([('inputs', current['inputs']), ('commissions', current['commissions']),
                          ('taxes', cents(revenue * iss_rate / 100)), *current['fixed'].items()])
    variable = sum((actual[k] for k, (_, kind) in COST_LINES.items() if kind == 'variable'), Decimal('0'))
    fixed = sum(current['fixed'].values(), Decimal('0'))
    margin = revenue - variable
    if fixed == 0:
        break_even = Decimal('0')
    elif revenue > 0 and margin > 0:
        break_even = fixed * revenue / margin
    else:
        break_even = None
    if break_even is None or break_even == 0:
        break_even_count = None if break_even is None else 0
    else:  # ponto positivo implica receita e atendimentos no mês
        break_even_count = int((break_even * count / revenue).to_integral_value(rounding=ROUND_CEILING))
    summary = {
        'appointments': count, 'revenue': revenue, 'variable_costs': variable, 'contribution_margin': margin,
        'contribution_margin_ratio': ratio(margin, revenue), 'fixed_costs': fixed, 'result': margin - fixed,
        'average_ticket': cents(revenue / count) if count else None,
        'cost_per_appointment': cents((variable + fixed) / count) if count else None,
        'break_even_revenue': cents(break_even) if break_even is not None else None,
        'break_even_appointments': break_even_count,
        'safety_margin': ratio(revenue - break_even, revenue) if break_even is not None else None,
    }

    budgets = {item['category']: item['amount'] for item in budget_items(db, month)}
    lines, alerts = [], []
    for key, (label, kind) in COST_LINES.items():
        budget = budgets.get(key)
        variance = actual[key] - budget if budget is not None else None
        status = 'no_budget' if budget is None else ('over' if actual[key] > budget else 'within')
        lines.append({'category': key, 'label': label, 'kind': kind, 'actual': actual[key], 'budget': budget,
                      'variance': variance, 'consumed_ratio': ratio(actual[key], budget) if budget is not None else None,
                      'status': status})
        if status == 'over':
            alerts.append({'level': 'warning', 'message': f'{label} acima do orçamento em {money(variance)}.'})

    service_rows = [close(row) for row in services.values()]
    professional_rows = [close(row) for row in professionals.values()]
    for row in service_rows:
        if row['contribution_margin'] < 0:
            alerts.append({'level': 'danger', 'message': f'{row["name"]} teve margem de contribuição negativa no mês.'})

    standard = []
    catalog = (db.query(Service).options(selectinload(Service.recipes).selectinload(ServiceRecipe.product))
               .filter(Service.is_active == True).order_by(Service.name, Service.id).all())  # noqa: E712
    for service in catalog:
        price = cents(service.price)
        input_cost = cents(sum((Decimal(str(r.qty_consumed)) * Decimal(r.product.cost_per_unit or 0) for r in service.recipes),
                               Decimal('0')))
        taxes = cents(price * iss_rate / 100)
        standard.append({'id': service.id, 'name': service.name, 'price': price, 'recipe_items': len(service.recipes),
                         'standard_input_cost': input_cost, 'input_ratio': ratio(input_cost, price), 'taxes': taxes,
                         'margin_before_commission': price - input_cost - taxes})
        if price > 0 and input_cost + taxes >= price:
            alerts.append({'level': 'danger', 'message': f'O preço de {service.name} não cobre insumos e ISS da ficha técnica.'})

    if count and summary['result'] < 0:
        alerts.append({'level': 'danger', 'message': 'Resultado negativo: a margem de contribuição não cobriu os custos fixos do mês.'})
    elif break_even is None and fixed > 0:
        alerts.append({'level': 'warning', 'message': 'Sem margem de contribuição positiva no mês, não há ponto de equilíbrio calculável.'})

    trend = []
    for key, bucket in history.items():
        taxes = cents(bucket['revenue'] * iss_rate / 100)
        variable_costs = bucket['inputs'] + bucket['commissions'] + taxes
        fixed_costs = sum(bucket['fixed'].values(), Decimal('0'))
        trend.append({'month': key, 'appointments': bucket['appointments'], 'revenue': bucket['revenue'],
                      'variable_costs': variable_costs, 'fixed_costs': fixed_costs,
                      'result': bucket['revenue'] - variable_costs - fixed_costs})

    return {
        'month': month, 'notice': NOTICE, 'iss_rate': iss_rate, 'summary': summary, 'lines': lines,
        'budget_total': sum(budgets.values(), Decimal('0')) if budgets else None,
        'services': sorted(service_rows, key=lambda row: (-row['contribution_margin'], row['name'])),
        'professionals': sorted(professional_rows, key=lambda row: (-row['contribution_margin'], row['name'])),
        'standard_costs': standard, 'history': trend, 'alerts': alerts,
    }


@router.get('/report')
def report(month: str = MONTH, user=Depends(require_manager), db: Session = Depends(get_db)):
    return build_cost_report(db, month)


@router.put('/budget')
@serialized_mutation
def save_budget(body: BudgetInput, month: str = MONTH, user=Depends(require_manager), db: Session = Depends(get_db)):
    """Substitui o orçamento inteiro do mês; linhas omitidas deixam de ter orçamento."""
    parse_month(month)
    wanted = {item.category: item.amount for item in body.items}
    for row in db.query(CostBudget).filter(CostBudget.month == month).all():
        if row.category in wanted:
            row.amount = wanted.pop(row.category)
        else:
            db.delete(row)
    for category, amount in wanted.items():
        db.add(CostBudget(tenant_id=user.tenant_id, month=month, category=category, amount=amount))
    db.commit()
    return {'month': month, 'items': budget_items(db, month)}


def csv_cell(value) -> str:
    if value is None:
        return ''
    if isinstance(value, Decimal):
        return str(value).replace('.', ',')
    text = str(value)
    # Evita que planilhas interpretem nomes cadastrados como fórmulas.
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


@router.get('/report/download')
def download(month: str = MONTH, user=Depends(require_manager), db: Session = Depends(get_db)):
    data = build_cost_report(db, month)
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';', lineterminator='\n')
    rows = [['Velour — gestão de custos', month], [data['notice']], [],
            ['Indicador', 'Valor'], *([SUMMARY_LABELS[key], value] for key, value in data['summary'].items()), [],
            ['Linha de custo', 'Tipo', 'Realizado', 'Orçado', 'Variação', 'Situação'],
            *([line['label'], 'variável' if line['kind'] == 'variable' else 'fixo', line['actual'], line['budget'],
               line['variance'], STATUS_LABELS[line['status']]] for line in data['lines']), [],
            ['Serviço', 'Categoria', 'Atendimentos', 'Receita', 'Insumos', 'Comissões', 'ISS', 'Margem de contribuição', 'Margem %'],
            *([row['name'], row['category'], row['appointments'], row['revenue'], row['inputs'], row['commissions'],
               row['taxes'], row['contribution_margin'], row['margin_ratio']] for row in data['services']), [],
            ['Profissional', 'Atendimentos', 'Receita', 'Insumos', 'Comissões', 'ISS', 'Margem de contribuição', 'Margem %'],
            *([row['name'], row['appointments'], row['revenue'], row['inputs'], row['commissions'], row['taxes'],
               row['contribution_margin'], row['margin_ratio']] for row in data['professionals']), [],
            ['Serviço (ficha técnica)', 'Preço', 'Custo-padrão de insumos', 'ISS', 'Margem antes da comissão'],
            *([row['name'], row['price'], row['standard_input_cost'], row['taxes'], row['margin_before_commission']]
              for row in data['standard_costs'])]
    writer.writerows([[csv_cell(value) for value in row] for row in rows])
    headers = {'Content-Disposition': f'attachment; filename="velour-custos-{month}.csv"', 'Cache-Control': 'no-store'}
    return Response('﻿' + out.getvalue(), media_type='text/csv; charset=utf-8', headers=headers)
