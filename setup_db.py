from app import create_app, db
from app.models import Usuario, Etapa
from werkzeug.security import generate_password_hash
import os

app = create_app()

# Caminho do banco de dados
db_path = os.path.join('instance', 'prisma.db')

with app.app_context():
    # 1. Apaga o banco antigo se existir (Começar do zero)
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Banco antigo removido: {db_path}")

    # 2. Cria as tabelas novas
    db.create_all()
    print("✨ Novas tabelas criadas.")

    # 3. Cria o Admin
    admin = Usuario(
        nome_completo='Patrão (Admin)',
        username='admin',
        senha_hash=generate_password_hash('123456'),
        nivel_acesso=0 # Admin Total
    )
    db.session.add(admin)
    print("👤 Usuário 'admin' criado (Senha: 123456).")

    # 4. Cria as Etapas do Kanban (Padrão)
    etapas_padrao = [
        ("Orçamento", 1),
        ("Arte / Aprovação", 2),
        ("Impressão", 3),
        ("Acabamento", 4),
        ("Pronto / Entrega", 5)
    ]

    for nome, ordem in etapas_padrao:
        nova_etapa = Etapa(nome=nome, ordem=ordem)
        db.session.add(nova_etapa)
    
    print("🏗️ 5 Etapas do Kanban configuradas.")

    # Salva tudo
    db.session.commit()
    print("✅ TUDO PRONTO! Pode rodar o sistema.")