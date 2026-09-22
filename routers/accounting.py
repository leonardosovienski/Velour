"""Contabilidade demonstrativa: DRE, lançamentos e balancete calculados a partir dos registros.

Nada é gravado nem transmitido. Os relatórios servem para apresentação acadêmica do MVP e
não substituem escrituração contábil, SPED ou apuração oficial de tributos.
"""
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from auth import require_manager
from database import get_db
from models import Appointment, AppointmentStatus, Expense, FiscalProfile, Product, StockMovement, Tenant
from models.stock_movement import StockMovementType

router = APIRouter(prefix='/accounting', tags=['accounting'])
NOTICE = 'DEMONSTRAÇÃO ACADÊMICA — SEM VALIDADE CONTÁBIL OU FISCAL. Valores calculados a partir dos registros do Velour.'
CENT = Decimal('0.01')
MONTH = Query(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')

# Plano de contas simplificado: código -> (nome, natureza). Natureza devedora = ativo/despesa.
ACCOUNTS = OrderedDict([
    ('1.1.1', ('Caixa e equivalentes', 'D')),
    ('1.1.2', ('Clientes a receber', 'D')),
    ('1.1.3', ('Estoque de insumos', 'D')),
    ('2.1.1', ('Fornecedores e contas a pagar', 'C')),
    ('2.1.2', ('Comissões a pagar', 'C')),
    ('2.1.3', ('ISS a recolher', 'C')),
    ('3.1.1', ('Receita de serviços', 'C')),
    ('3.2.1', ('(-) ISS sobre serviços', 'D')),
    ('4.1.1', ('Custo de insumos consumidos', 'D')),
    ('4.1.2', ('Comissões de profissionais', 'D')),
    ('4.2.1', ('Aluguel', 'D')),
    ('4.2.2', ('Produtos e materiais', 'D')),
    ('4.2.3', ('Contas e serviços', 'D')),
    ('4.2.4', ('Equipe', 'D')),
    ('4.2.5', ('Outras despesas', 'D')),
])
EXPENSE_ACCOUNTS = {'rent': '4.2.1', 'supplies': '4.2.2', 'utilities': '4.2.3', 'people': '4.2.4', 'other': '4.2.5'}


def cents(value) -> Decimal:
    return Decimal(value or 0).quantize(CENT)


def month_bounds(month: str):
    start = date.fromisoformat(month + '-01')
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    if start.year < 1:
        raise ValueError
    return start, end


def build_report(db: Session, month: str) -> dict:
    try:
        start, end = month_bounds(month)
    except ValueError:
        raise HTTPException(422, 'Mês inválido')
    start_dt, end_dt = datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())
    appointments = (db.query(Appointment)
                    .options(joinedload(Appointment.client), joinedload(Appointment.service), joinedload(Appointment.professional))
                    .filter(Appointment.status == AppointmentStatus.completed,
                            Appointment.scheduled_at >= start_dt, Appointment.scheduled_at < end_dt)
                    .order_by(Appointment.scheduled_at, Appointment.id).all())
    expenses = (db.query(Expense).filter(Expense.due_date >= start, Expense.due_date < end)
                .order_by(Expense.due_date, Expense.id).all())
    consumption = (db.query(StockMovement, Product).join(Product, Product.id == StockMovement.product_id)
                   .filter(StockMovement.type == StockMovementType.consumption,
                           StockMovement.created_at >= start_dt, StockMovement.created_at < end_dt).all())
    profile = db.query(FiscalProfile).first()
    iss_rate = Decimal(str(profile.data.get('iss_rate', '0'))) if profile else Decimal('0')

    entries = []

    def post(day, history, debit, credit, amount):
        amount = cents(amount)
        if amount > 0:
            entries.append({'date': day.isoformat(), 'history': history, 'debit': debit, 'credit': credit, 'amount': amount})

    revenue = commissions = Decimal('0')
    for a in appointments:
        price = cents(a.price_charged if a.price_charged is not None else a.service.price)
        received = cents(a.amount_paid) if a.paid else Decimal('0')
        commission = cents(price * (a.professional.commission_rate or 0))
        revenue += price
        commissions += commission
        day = a.scheduled_at.date()
        label = f'Atendimento #{a.id} — {a.service.name} ({a.client.name})'
        post(day, label, '1.1.2', '3.1.1', price)
        post(day, f'Recebimento do atendimento #{a.id}', '1.1.1', '1.1.2', min(received, price))
        post(day, f'Comissão de {a.professional.name} no atendimento #{a.id}', '4.1.2', '2.1.2', commission)

    supplies = cents(sum((Decimal(str(-m.qty)) * Decimal(p.cost_per_unit or 0) for m, p in consumption), Decimal('0')))
    last_day = date.fromordinal(end.toordinal() - 1)
    post(last_day, 'Baixa de insumos consumidos nos atendimentos do mês', '4.1.1', '1.1.3', supplies)
    iss = cents(revenue * iss_rate / 100)
    post(last_day, f'ISS estimado do mês ({iss_rate:.2f}% sobre a receita de serviços)', '3.2.1', '2.1.3', iss)

    by_category = OrderedDict((code, Decimal('0')) for code in EXPENSE_ACCOUNTS.values())
    for e in expenses:
        account = EXPENSE_ACCOUNTS[e.category]
        by_category[account] += cents(e.amount)
        post(e.due_date, f'Despesa: {e.description}', account, '2.1.1', e.amount)
        if e.paid_on:
            post(e.paid_on, f'Pagamento da despesa: {e.description}', '2.1.1', '1.1.1', e.amount)
    entries.sort(key=lambda row: row['date'])

    totals = {code: {'debit': Decimal('0'), 'credit': Decimal('0')} for code in ACCOUNTS}
    for row in entries:
        totals[row['debit']]['debit'] += row['amount']
        totals[row['credit']]['credit'] += row['amount']
    trial = []
    for code, (name, nature) in ACCOUNTS.items():
        debit, credit = totals[code]['debit'], totals[code]['credit']
        if debit or credit:
            balance = debit - credit if nature == 'D' else credit - debit
            trial.append({'code': code, 'name': name, 'debit': debit, 'credit': credit, 'balance': balance, 'nature': nature})

    net_revenue = revenue - iss
    service_costs = supplies + commissions
    gross_profit = net_revenue - service_costs
    operating = sum(by_category.values(), Decimal('0'))
    dre = [
        {'label': 'Receita bruta de serviços', 'value': revenue, 'level': 0},
        {'label': '(-) ISS estimado', 'value': -iss, 'level': 1},
        {'label': 'Receita líquida', 'value': net_revenue, 'level': 0},
        {'label': '(-) Custo de insumos consumidos', 'value': -supplies, 'level': 1},
        {'label': '(-) Comissões de profissionais', 'value': -commissions, 'level': 1},
        {'label': 'Lucro bruto', 'value': gross_profit, 'level': 0},
        *({'label': f'(-) {ACCOUNTS[code][0]}', 'value': -value, 'level': 1} for code, value in by_category.items() if value),
        {'label': 'Despesas operacionais', 'value': -operating, 'level': 0},
        {'label': 'Resultado do período', 'value': gross_profit - operating, 'level': 0},
    ]
    return {
        'month': month, 'notice': NOTICE, 'iss_rate': iss_rate, 'dre': dre, 'entries': entries, 'trial_balance': trial,
        'total_debit': sum((r['debit'] for r in trial), Decimal('0')),
        'total_credit': sum((r['credit'] for r in trial), Decimal('0')),
        'result': gross_profit - operating,
        'chart_of_accounts': [{'code': code, 'name': name, 'nature': nature} for code, (name, nature) in ACCOUNTS.items()],
    }


def money(value: Decimal) -> str:
    text = f'{abs(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'-R$ {text}' if value < 0 else f'R$ {text}'


def report_lines(report: dict, salon: str) -> list[str]:
    width = 78
    br_month = '/'.join(reversed(report['month'].split('-')))
    lines = ['VELOUR — RELATÓRIO CONTÁBIL DEMONSTRATIVO', f'Salão: {salon}', f'Competência: {br_month}',
             f'Gerado em: {datetime.now():%d/%m/%Y %H:%M}', '', report['notice'], '', '=' * width,
             'DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO (DRE)', '=' * width]
    for row in report['dre']:
        label = ('    ' if row['level'] else '') + row['label']
        lines.append(f'{label:<58}{money(row["value"]):>20}')
    lines += ['', '=' * width, 'LIVRO DIÁRIO (LANÇAMENTOS SIMULADOS)', '=' * width]
    if not report['entries']:
        lines.append('Nenhum lançamento no período.')
    for i, row in enumerate(report['entries'], 1):
        day = '/'.join(reversed(row['date'].split('-')))
        lines += [f'{i:>3}. {day}  {row["history"][:62]}',
                  f'       D {row["debit"]} {ACCOUNTS[row["debit"]][0]:<34}{money(row["amount"]):>20}',
                  f'       C {row["credit"]} {ACCOUNTS[row["credit"]][0]:<34}{money(row["amount"]):>20}']
    lines += ['', '=' * width, 'BALANCETE DE VERIFICAÇÃO', '=' * width,
              f'{"Conta":<36}{"Débitos":>14}{"Créditos":>14}{"Saldo":>14}']
    for row in report['trial_balance']:
        lines.append(f'{row["code"] + " " + row["name"]:<36.36}{money(row["debit"]):>14}{money(row["credit"]):>14}{money(row["balance"]):>14}')
    lines += ['-' * width, f'{"TOTAIS":<36}{money(report["total_debit"]):>14}{money(report["total_credit"]):>14}',
              'Débitos = créditos: ' + ('sim' if report['total_debit'] == report['total_credit'] else 'NÃO'), '',
              'Critérios: receitas e comissões pela data do atendimento concluído; despesas pelo vencimento;',
              'insumos pelo custo cadastrado do produto; ISS pela alíquota do cadastro fiscal demonstrativo.']
    return lines


def pdf_escape(text: str) -> bytes:
    raw = text.encode('cp1252', errors='replace')
    return raw.replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')


def build_pdf(lines: list[str]) -> bytes:
    """PDF mínimo (texto monoespaçado, A4) sem dependências externas."""
    per_page, pages = 60, []
    for i in range(0, max(len(lines), 1), per_page):
        chunk = lines[i:i + per_page]
        body = b'BT /F1 8 Tf 10 TL 40 800 Td ' + b' '.join(b'(' + pdf_escape(line) + b') Tj T*' for line in chunk) + b' ET'
        pages.append(body)
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', None,
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>']
    kids = []
    for content in pages:
        objects.append(b'<< /Length %d >>\nstream\n' % len(content) + content + b'\nendstream')
        objects.append(b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>' % len(objects))
        kids.append(len(objects))
    objects[1] = b'<< /Type /Pages /Kids [' + b' '.join(b'%d 0 R' % k for k in kids) + b'] /Count %d >>' % len(kids)
    out, offsets = bytearray(b'%PDF-1.4\n'), []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b'%d 0 obj\n' % number + obj + b'\nendobj\n'
    xref = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objects) + 1)
    out += b''.join(b'%010d 00000 n \n' % offset for offset in offsets)
    out += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objects) + 1, xref)
    return bytes(out)


@router.get('/report')
def report(month: str = MONTH, user=Depends(require_manager), db: Session = Depends(get_db)):
    return build_report(db, month)


@router.get('/report/download')
def download(month: str = MONTH, format: str = Query('txt', pattern='^(txt|pdf)$'),
             user=Depends(require_manager), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    lines = report_lines(build_report(db, month), tenant.name if tenant else '')
    headers = {'Content-Disposition': f'attachment; filename="velour-contabil-{month}.{format}"', 'Cache-Control': 'no-store'}
    if format == 'pdf':
        return Response(build_pdf(lines), media_type='application/pdf', headers=headers)
    return Response('\n'.join(lines) + '\n', media_type='text/plain; charset=utf-8', headers=headers)
