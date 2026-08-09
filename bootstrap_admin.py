"""Cria o primeiro administrador sem incluir credenciais no código ou histórico."""
import getpass
import os

from database import SessionLocal
from auth import hash_password
from models.user import User, UserRole


def main() -> int:
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL") or input("E-mail do administrador: ").strip().lower()
    name = os.getenv("BOOTSTRAP_ADMIN_NAME") or input("Nome do administrador: ").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or getpass.getpass("Senha (mínimo 12 caracteres): ")

    if not email or "@" not in email or not name:
        raise SystemExit("Nome e e-mail válido são obrigatórios.")
    if len(password) < 12:
        raise SystemExit("A senha inicial deve ter pelo menos 12 caracteres.")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            raise SystemExit("Já existe um usuário com esse e-mail.")
        user = User(name=name, email=email, hashed_password=hash_password(password), role=UserRole.admin)
        db.add(user)
        db.commit()
        print(f"Administrador {email} criado com sucesso.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
