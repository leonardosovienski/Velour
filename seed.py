"""
Script de seed — popula o banco Velour com dados de desenvolvimento.
Execute: python seed.py
"""
from datetime import datetime, timedelta, date
from random import choice, randint, uniform, shuffle
import sys

from database import SessionLocal, engine, Base
import models  # noqa — registra todos os modelos

from auth import hash_password
from models.user import User, UserRole
from models.client import Client, Gender, LoyaltyTier, ChatPreference, calculate_tier, generate_referral_code
from models.professional import Professional, ProfGender
from models.service import ServiceCategory, Service, GenderTarget
from models.appointment import Appointment, AppointmentStatus
from models.loyalty import LoyaltyTransaction, TransactionType
from models.referral import Referral, ReferralStatus
from models.product import Product, ProductUnit
from models.service_recipe import ServiceRecipe
from models.stock_movement import StockMovement, StockMovementType

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def limpar():
    # Ordem respeita as FKs (filhos antes dos pais)
    db.query(StockMovement).delete()
    db.query(LoyaltyTransaction).delete()
    db.query(Referral).delete()
    db.query(Appointment).delete()
    db.query(ServiceRecipe).delete()
    db.query(Product).delete()
    db.query(Client).delete()
    db.query(Professional).delete()
    db.query(Service).delete()
    db.query(ServiceCategory).delete()
    db.query(User).delete()
    db.commit()
    print("Banco limpo.")


def seed_users():
    users = [
        User(
            name="Admin Velour",
            email="admin@velour.com",
            hashed_password=hash_password("velour2026"),
            role=UserRole.admin,
        ),
        User(
            name="Gerente Operações",
            email="gerente@velour.com",
            hashed_password=hash_password("velour2026"),
            role=UserRole.manager,
        ),
    ]
    db.add_all(users)
    db.commit()
    print(f"  {len(users)} usuários criados.")
    return users


def seed_professionals():
    profs = [
        Professional(
            name="Ana Luiza Ferreira",
            phone="(11) 91111-1111",
            email="ana@velour.com",
            gender=ProfGender.F,
            specialty="Coloração, Corte Feminino, Mechas",
            bio="Especialista em coloração loura e ruiva com 8 anos de experiência.",
            commission_rate=0.45,
            monthly_goal=12000.0,
        ),
        Professional(
            name="Beatriz Costa",
            phone="(11) 92222-2222",
            email="beatriz@velour.com",
            gender=ProfGender.F,
            specialty="Manicure, Pedicure, Nail Art",
            bio="Certificada em nail design pela Europa.",
            commission_rate=0.40,
            monthly_goal=8000.0,
        ),
        Professional(
            name="Carlos Drummond",
            phone="(11) 93333-3333",
            email="carlos@velour.com",
            gender=ProfGender.M,
            specialty="Corte Masculino, Barba",
            bio="Barbeiro master com técnicas clássicas e modernas.",
            commission_rate=0.45,
            monthly_goal=9000.0,
        ),
        Professional(
            name="Diego Alves",
            phone="(11) 94444-4444",
            email="diego@velour.com",
            gender=ProfGender.M,
            specialty="Corte Masculino, Barba, Coloração Masculina",
            bio="Especialista em barbearia de luxo e undercuts.",
            commission_rate=0.40,
            monthly_goal=9500.0,
        ),
    ]
    db.add_all(profs)
    db.commit()
    print(f"  {len(profs)} profissionais criados.")
    return profs


def seed_categories_and_services():
    categorias = [
        ServiceCategory(name="Cabelo Feminino", gender_target=GenderTarget.F, icon="scissors"),
        ServiceCategory(name="Coloração", gender_target=GenderTarget.all, icon="palette"),
        ServiceCategory(name="Barba & Barbearia", gender_target=GenderTarget.M, icon="razor"),
        ServiceCategory(name="Manicure & Pedicure", gender_target=GenderTarget.all, icon="sparkles"),
        ServiceCategory(name="Cabelo Masculino", gender_target=GenderTarget.M, icon="scissors"),
    ]
    db.add_all(categorias)
    db.flush()

    cab_f, coloracao, barba, unhas, cab_m = categorias

    servicos = [
        # Cabelo Feminino
        Service(category_id=cab_f.id, name="Corte Feminino", duration_minutes=60, price=180.0, points_reward=180),
        Service(category_id=cab_f.id, name="Escova Premium", duration_minutes=45, price=120.0, points_reward=120),
        Service(category_id=cab_f.id, name="Hidratação Profunda", duration_minutes=60, price=150.0, points_reward=150),
        # Coloração
        Service(category_id=coloracao.id, name="Coloração Global", description="Coloração completa com produto profissional", duration_minutes=120, price=350.0, points_reward=350),
        Service(category_id=coloracao.id, name="Mechas Californianas", duration_minutes=180, price=550.0, points_reward=550),
        Service(category_id=coloracao.id, name="Balayage", description="Técnica de pintura livre para efeito natural", duration_minutes=150, price=480.0, points_reward=480),
        # Barba & Barbearia
        Service(category_id=barba.id, name="Barba Clássica", duration_minutes=30, price=80.0, points_reward=80),
        Service(category_id=barba.id, name="Barba com Toalha Quente", duration_minutes=45, price=110.0, points_reward=110),
        Service(category_id=barba.id, name="Bigode & Acabamento", duration_minutes=20, price=60.0, points_reward=60),
        # Manicure & Pedicure
        Service(category_id=unhas.id, name="Manicure Gel", duration_minutes=60, price=130.0, points_reward=130),
        Service(category_id=unhas.id, name="Pedicure Spa", duration_minutes=60, price=110.0, points_reward=110),
        Service(category_id=unhas.id, name="Nail Art Premium", duration_minutes=90, price=200.0, points_reward=200),
        # Cabelo Masculino
        Service(category_id=cab_m.id, name="Corte Masculino", duration_minutes=45, price=90.0, points_reward=90),
        Service(category_id=cab_m.id, name="Corte + Barba", duration_minutes=75, price=160.0, points_reward=160),
        Service(category_id=cab_m.id, name="Tratamento Capilar Masculino", duration_minutes=60, price=140.0, points_reward=140),
    ]
    db.add_all(servicos)
    db.commit()
    print(f"  {len(categorias)} categorias e {len(servicos)} serviços criados.")
    return servicos


def seed_products_and_recipes(servicos):
    """Cria insumos de estoque e amarra fichas técnicas aos serviços de coloração."""
    from datetime import date as _date

    produtos = [
        Product(name="Pó Descolorante", unit=ProductUnit.g, stock_qty=2000, min_stock=300, cost_per_unit=0.12,
                expiry_date=_date(2027, 3, 1)),
        Product(name="Oxidante 20 vol", unit=ProductUnit.ml, stock_qty=5000, min_stock=800, cost_per_unit=0.04,
                expiry_date=_date(2026, 9, 1)),
        Product(name="Coloração 7.3 Louro Dourado", unit=ProductUnit.ml, stock_qty=1200, min_stock=200, cost_per_unit=0.18,
                expiry_date=_date(2026, 7, 10)),
        Product(name="Coloração 9.0 Louro Claro", unit=ProductUnit.ml, stock_qty=900, min_stock=200, cost_per_unit=0.18),
        Product(name="Matizador Violeta", unit=ProductUnit.ml, stock_qty=600, min_stock=150, cost_per_unit=0.22),
        Product(name="Shampoo Pós-Química", unit=ProductUnit.ml, stock_qty=3000, min_stock=500, cost_per_unit=0.03),
        Product(name="Luvas Descartáveis", unit=ProductUnit.unit, stock_qty=200, min_stock=40, cost_per_unit=0.50),
    ]
    db.add_all(produtos)
    db.flush()  # garante os ids

    # Movimentações de saldo inicial (mantém o ledger íntegro)
    for p in produtos:
        if p.stock_qty > 0:
            db.add(StockMovement(
                product_id=p.id, type=StockMovementType.purchase,
                qty=p.stock_qty, qty_before=0.0, qty_after=p.stock_qty,
                description="Saldo inicial",
            ))

    po, ox, cor73, cor90, matiz, shampoo, luvas = produtos
    svc_by_name = {s.name: s for s in servicos}

    # Ficha técnica: serviço -> [(produto, qty na unidade do produto)]
    receitas = {
        "Coloração Global": [(cor73, 60), (ox, 90), (shampoo, 30), (luvas, 1)],
        "Mechas Californianas": [(po, 80), (ox, 120), (matiz, 20), (shampoo, 40), (luvas, 2)],
        "Balayage": [(po, 60), (ox, 90), (cor90, 30), (shampoo, 40), (luvas, 2)],
    }
    n_recipes = 0
    for nome, itens in receitas.items():
        svc = svc_by_name.get(nome)
        if not svc:
            continue
        for produto, qty in itens:
            db.add(ServiceRecipe(service_id=svc.id, product_id=produto.id, qty_consumed=qty))
            n_recipes += 1

    db.commit()
    print(f"  {len(produtos)} insumos e {n_recipes} itens de ficha técnica criados.")
    return produtos


def _vlr_code(seq: int) -> str:
    return f"VLR-{seq:05d}"


def seed_clients():
    nomes_f = [
        "Maria Fernandes", "Ana Carolina Lima", "Juliana Souza", "Camila Rodrigues",
        "Beatriz Almeida", "Fernanda Torres", "Larissa Mendes", "Patrícia Vasconcelos",
        "Amanda Oliveira", "Renata Carvalho",
    ]
    nomes_m = [
        "Ricardo Santos", "Bruno Costa", "Felipe Marques", "Thiago Barbosa",
        "Gustavo Pereira", "Leonardo Melo", "Matheus Gomes", "Rafael Nascimento",
        "Daniel Ferreira", "Eduardo Cardoso",
    ]

    clientes = []
    for i, nome in enumerate(nomes_f + nomes_m, start=1):
        gender = Gender.F if i <= len(nomes_f) else Gender.M
        total_spent = uniform(0, 4000)
        tier = calculate_tier(total_spent)
        pts = int(total_spent * 0.8)
        visits = randint(1, 20)

        rcode = generate_referral_code()
        while any(c.referral_code == rcode for c in clientes):
            rcode = generate_referral_code()

        c = Client(
            code=_vlr_code(i),
            name=nome,
            phone=f"(11) 9{randint(1000, 9999)}-{randint(1000, 9999)}",
            email=f"{nome.split()[0].lower()}@email.com",
            gender=gender,
            birthdate=date(randint(1975, 2000), randint(1, 12), randint(1, 28)),
            first_visit=date(2024, randint(1, 12), randint(1, 28)),
            preferred_drink=choice(["Café sem açúcar", "Espumante", "Chá verde", "Água com gás", None]),
            music_preference=choice(["Jazz instrumental", "Pop brasileiro", "Silêncio", "MPB", None]),
            temperature_preference=choice(["Fria", "Agradável", "Quente", None]),
            chat_preference=choice([ChatPreference.chatty, ChatPreference.quiet, ChatPreference.neutral]),
            allergies=choice([None, None, None, "Amônia concentrada", "Parafenilenediamina"]),
            notes=choice([None, None, "Prefere horários da manhã", "Sempre pede café ao chegar"]),
            loyalty_points=pts,
            loyalty_tier=tier,
            total_spent=round(total_spent, 2),
            total_visits=visits,
            referral_code=rcode,
        )
        clientes.append(c)

    db.add_all(clientes)
    db.commit()
    print(f"  {len(clientes)} clientes criados.")
    return clientes


def seed_appointments(clientes, profissionais, servicos):
    agendamentos = []
    hoje = datetime.now()

    # Distribui serviços por profissional de acordo com a especialidade declarada
    servicos_ana = [s for s in servicos if any(kw in s.name for kw in
        ["Corte Feminino", "Escova", "Hidratação", "Coloração", "Mechas", "Balayage"])]
    servicos_beatriz = [s for s in servicos if any(kw in s.name for kw in
        ["Manicure", "Pedicure", "Nail"])]
    servicos_masculino = [s for s in servicos if any(kw in s.name for kw in
        ["Barba", "Bigode", "Corte Masculino", "Corte +", "Tratamento"])]
    servicos_diego = servicos_masculino + [s for s in servicos if "Coloração Global" in s.name]

    prof_map = {
        profissionais[0]: servicos_ana,       # Ana — cabelo feminino e coloração
        profissionais[1]: servicos_beatriz,   # Beatriz — manicure, pedicure, nail art
        profissionais[2]: servicos_masculino, # Carlos — corte masculino e barba
        profissionais[3]: servicos_diego,     # Diego — corte, barba e coloração masculina
    }

    status_passados = [AppointmentStatus.completed, AppointmentStatus.completed, AppointmentStatus.completed, AppointmentStatus.no_show, AppointmentStatus.cancelled]

    horarios = [9, 10, 11, 13, 14, 15, 16, 17]

    for i in range(30):
        dias_offset = randint(-90, 14)
        data_base = hoje + timedelta(days=dias_offset)
        hora = choice(horarios)
        scheduled_at = data_base.replace(hour=hora, minute=0, second=0, microsecond=0)

        prof = choice(profissionais)
        servicos_disponiveis = prof_map[prof]
        if not servicos_disponiveis:
            servicos_disponiveis = servicos
        servico = choice(servicos_disponiveis)
        cliente = choice(clientes)

        ends_at = scheduled_at + timedelta(minutes=servico.duration_minutes)

        # Verificar conflito simples
        conflict = any(
            a.professional_id == prof.id and
            a.scheduled_at < ends_at and a.ends_at > scheduled_at
            for a in agendamentos
        )
        if conflict:
            continue

        is_past = dias_offset < 0
        if is_past:
            status = choice(status_passados)
        elif dias_offset == 0:
            status = choice([AppointmentStatus.confirmed, AppointmentStatus.in_progress, AppointmentStatus.scheduled])
        else:
            status = choice([AppointmentStatus.scheduled, AppointmentStatus.confirmed])

        price_charged = servico.price if status == AppointmentStatus.completed else None
        formula = None
        if status == AppointmentStatus.completed and "Coloração" in servico.name:
            formula = choice(["Wella 7.3 + 7.0 (50/50)", "L'Oréal 9.1 + 9.0", "Schwarzkopf 6.35", "Wella 5.65 + 5.0"])

        appt = Appointment(
            client_id=cliente.id,
            professional_id=prof.id,
            service_id=servico.id,
            scheduled_at=scheduled_at,
            ends_at=ends_at,
            status=status,
            price_charged=price_charged,
            formula_used=formula,
            occasion=choice([None, None, None, "Aniversário", "Casamento", "Formatura"]),
            points_awarded=int(price_charged) if price_charged else 0,
        )
        agendamentos.append(appt)

    db.add_all(agendamentos)
    db.commit()
    print(f"  {len(agendamentos)} agendamentos criados.")
    return agendamentos


def seed_referrals(clientes):
    refs = []
    indicadores = clientes[:5]
    indicados = clientes[15:]

    for i, indicado in enumerate(indicados[:5]):
        referrer = indicadores[i]
        indicado.referred_by_id = referrer.id

        converted_at_dt = datetime.now() - timedelta(days=randint(5, 60))
        ref = Referral(
            referrer_id=referrer.id,
            referred_id=indicado.id,
            status=ReferralStatus.converted,
            points_awarded_referrer=150,
            points_awarded_referred=75,
            converted_at=converted_at_dt,
            created_at=converted_at_dt - timedelta(days=randint(1, 7)),
        )
        refs.append(ref)

    # Pendentes
    for indicado in clientes[5:8]:
        referrer = choice(indicadores)
        indicado.referred_by_id = referrer.id
        refs.append(Referral(referrer_id=referrer.id, referred_id=indicado.id, status=ReferralStatus.pending))

    db.add_all(refs)
    db.commit()
    print(f"  {len(refs)} indicações criadas.")


def seed_loyalty_transactions(clientes, agendamentos):
    txs = []
    for appt in agendamentos:
        if appt.status == AppointmentStatus.completed and appt.points_awarded:
            txs.append(LoyaltyTransaction(
                client_id=appt.client_id,
                appointment_id=appt.id,
                type=TransactionType.earned_appointment,
                points=appt.points_awarded,
                description=f"Atendimento concluído",
                created_at=appt.scheduled_at,
            ))

    # Bônus de aniversário para alguns clientes
    for c in clientes[:3]:
        txs.append(LoyaltyTransaction(
            client_id=c.id,
            type=TransactionType.earned_birthday,
            points=100,
            description="Bônus de aniversário",
        ))

    db.add_all(txs)
    db.commit()
    print(f"  {len(txs)} transações de fidelidade criadas.")


if __name__ == "__main__":
    print("Iniciando seed do banco Velour...")
    limpar()
    print("Criando dados:")
    seed_users()
    profs = seed_professionals()
    servicos = seed_categories_and_services()
    seed_products_and_recipes(servicos)
    clientes = seed_clients()
    appts = seed_appointments(clientes, profs, servicos)
    seed_referrals(clientes)
    seed_loyalty_transactions(clientes, appts)
    print("\nSeed concluído com sucesso!")
    print("\nCredenciais de acesso:")
    print("  Admin:   admin@velour.com / velour2026")
    print("  Gerente: gerente@velour.com / velour2026")
    print("\nSwagger UI: http://127.0.0.1:8000/docs")
    db.close()
