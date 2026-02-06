from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from config import Config
import os

# Inicializando extensões
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Garante que a pasta instance existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Inicializa plugins
    db.init_app(app)
    login_manager.init_app(app)

    # Context Processor: Injeta a configuração em todos os templates
    @app.context_processor
    def inject_config():
        try:
            from .models import Configuracao
            config_db = Configuracao.query.first()
            return dict(config_sistema=config_db)
        except:
            return dict(config_sistema=None)

    # Inicialização do Banco de Dados
    with app.app_context():
        from . import models 
        db.create_all()
        
        # Cria a configuração padrão se não existir
        from .models import Configuracao
        if not Configuracao.query.first():
            padrao = Configuracao(nome_empresa="Gráfica Prisma")
            db.session.add(padrao)
            db.session.commit()
            print(">> Configuração padrão criada com sucesso!")

    # --- REGISTRO DE BLUEPRINTS ---
    
    from .blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from .blueprints.settings import settings_bp
    app.register_blueprint(settings_bp)

    from .blueprints.materiais import materiais_bp
    app.register_blueprint(materiais_bp)

    from .blueprints.clientes import clientes_bp
    app.register_blueprint(clientes_bp)

    from .blueprints.pedidos import pedidos_bp
    app.register_blueprint(pedidos_bp)

    from .blueprints.financeiro import financeiro_bp
    app.register_blueprint(financeiro_bp)

    # --- ROTA DO DASHBOARD (ATUALIZADA) ---
    @app.route('/')
    @app.route('/dashboard')
    @login_required 
    def dashboard():
        # Importamos aqui dentro para evitar erros de ciclo
        from app.models import Pedido 
        
        # 1. Total de Pedidos
        total_pedidos = Pedido.query.count()
        
        # 2. Últimos 5 Pedidos (para a tabela)
        ultimos_pedidos = Pedido.query.order_by(Pedido.id.desc()).limit(5).all()
        
        # 3. Faturamento Total (Soma de todos os pedidos)
        todos = Pedido.query.all()
        faturamento = sum(p.valor_total for p in todos)

        # Envia tudo para o HTML
        return render_template('index.html', 
                               total_pedidos=total_pedidos,
                               ultimos_pedidos=ultimos_pedidos,
                               faturamento=faturamento)

    # Gambiarra técnica para o redirect funcionar
    app.add_url_rule('/dashboard', endpoint='main.dashboard', view_func=dashboard)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import Usuario
    return Usuario.query.get(int(user_id))