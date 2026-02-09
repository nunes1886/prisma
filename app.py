import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# --- CONFIGURAÇÃO ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'prisma-erp-2026-secure-token'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prisma.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---

usuario_setores = db.Table('usuario_setores',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('setor_id', db.Integer, db.ForeignKey('setores.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    funcao = db.Column(db.String(20), default='colaborador')
    acesso_estoque = db.Column(db.Boolean, default=False)
    acessos = db.relationship('Setor', secondary=usuario_setores, backref=db.backref('usuarios_permitidos', lazy=True))

    def set_password(self, password): self.senha = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.senha, password)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(20)) # PF, PJ, TERCEIRO
    documento = db.Column(db.String(20), unique=True)
    whatsapp = db.Column(db.String(20))
    pedidos = db.relationship('Card', backref='cliente_ref', lazy=True)

class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    valor_total = db.Column(db.Float, default=0.0)
    prazo = db.Column(db.String(20))
    imagem_path = db.Column(db.Text)
    is_archived = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'))
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    financeiro = db.relationship('Financeiro', backref='card_ref', lazy=True)

class Financeiro(db.Model):
    __tablename__ = 'financeiro'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False) # RECEITA / DESPESA
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pendente') # Pendente / Pago
    data_vencimento = db.Column(db.Date, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=True)

class Setor(db.Model):
    __tablename__ = 'setores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    cards = db.relationship('Card', backref='setor_ref', lazy=True)

class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cor = db.Column(db.String(20), default='#CCCCCC')

@login_manager.user_loader
def load_user(user_id): return Usuario.query.get(int(user_id))

# --- ROTAS PRINCIPAIS ---

@app.route('/')
@login_required
def index():
    setores = Setor.query.order_by(Setor.ordem).all()
    clientes = Cliente.query.order_by(Cliente.nome).all()
    status_list = Status.query.all()
    return render_template('index.html', setores=setores, clientes=clientes, status_list=status_list, user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user); return redirect(url_for('index'))
        flash('Credenciais inválidas.')
    return render_template('login.html')

@app.route('/logout')
def logout(): logout_user(); return redirect(url_for('login'))

@app.route('/financeiro/baixar/<int:id>', methods=['POST'])
@login_required
def baixar_pagamento(id):
    # Busca o lançamento ou retorna 404 se não existir
    lancamento = Financeiro.query.get_or_404(id)
    
    if lancamento.status == 'Pendente':
        lancamento.status = 'Pago'
        # Usamos datetime.now().date() para registrar apenas o dia
        # Certifique-se de que o modelo Financeiro tenha o campo data_pagamento
        # Caso não tenha, o status 'Pago' já é um grande avanço
        db.session.commit()
        flash(f'Pagamento de R$ {lancamento.valor:.2f} recebido com sucesso!')
    else:
        flash('Este lançamento já consta como pago.')
        
    return redirect(url_for('financeiro'))


@app.route('/dashboard')
@login_required
def dashboard():
    # KPI 1: Faturamento Total (Tudo que foi marcado como 'Pago')
    faturamento_total = db.session.query(func.sum(Financeiro.valor)).filter(Financeiro.status == 'Pago').scalar() or 0.0
    
    # KPI 2: Receita Pendente (A receber)
    a_receber = db.session.query(func.sum(Financeiro.valor)).filter(Financeiro.status == 'Pendente').scalar() or 0.0
    
    # KPI 3: Total de Pedidos Ativos
    pedidos_ativos = Card.query.filter_by(is_archived=False).count()

    # Dados para o Gráfico: Pedidos por Setor
    setores = Setor.query.all()
    labels_setores = [s.nome for s in setores]
    valores_setores = [Card.query.filter_by(setor_id=s.id, is_archived=False).count() for s in setores]

    return render_template('dashboard.html', 
                           faturamento=faturamento_total, 
                           receber=a_receber, 
                           ativos=pedidos_ativos,
                           labels_setores=labels_setores,
                           valores_setores=valores_setores,
                           user=current_user)

# --- MÓDULO CLIENTES ---

@app.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes.html', clientes=clientes, user=current_user)

@app.route('/cliente/novo', methods=['POST'])
@login_required
def novo_cliente():
    try:
        c = Cliente(
            nome=request.form.get('nome'),
            tipo=request.form.get('tipo'),
            documento=request.form.get('documento'),
            whatsapp=request.form.get('whatsapp')
        )
        db.session.add(c); db.session.commit()
        flash('Cliente cadastrado!')
    except: flash('Erro ao cadastrar documento duplicado.')
    return redirect(url_for('listar_clientes'))

# --- MÓDULO VENDA E FINANCEIRO ---

@app.route('/venda/nova', methods=['POST'])
@login_required
def criar_venda():
    # Pega o primeiro setor (ex: Atendimento) e primeiro status
    setor_ini = Setor.query.order_by(Setor.ordem).first()
    status_ini = Status.query.first()
    
    # 1. Cria o Pedido (Card)
    novo_card = Card(
        titulo=request.form.get('servico'),
        descricao=request.form.get('detalhes'),
        valor_total=float(request.form.get('valor')),
        cliente_id=int(request.form.get('cliente_id')),
        setor_id=setor_ini.id,
        status_id=status_ini.id,
        prazo=request.form.get('prazo')
    )
    db.session.add(novo_card)
    db.session.flush() # Garante o ID para o financeiro

    # 2. Lança Receita no Financeiro
    data_venc = datetime.strptime(request.form.get('prazo'), '%Y-%m-%d').date()
    lancamento = Financeiro(
        tipo='RECEITA',
        descricao=f"Pedido #{novo_card.id} - {novo_card.titulo}",
        valor=novo_card.valor_total,
        data_vencimento=data_venc,
        card_id=novo_card.id
    )
    db.session.add(lancamento)
    db.session.commit()
    flash('Venda realizada com sucesso!')
    return redirect(url_for('index'))

@app.route('/financeiro')
@login_required
def financeiro():
    receitas = Financeiro.query.filter_by(tipo='RECEITA').all()
    despesas = Financeiro.query.filter_by(tipo='DESPESA').all()
    total_receber = sum(r.valor for r in receitas if r.status == 'Pendente')
    return render_template('financeiro.html', receitas=receitas, despesas=despesas, total_receber=total_receber, user=current_user)

# --- INICIALIZAÇÃO ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed inicial
        if not Usuario.query.filter_by(username='admin').first():
            u = Usuario(username='admin', funcao='admin'); u.set_password('admin'); db.session.add(u)
        if not Setor.query.first():
            db.session.add(Setor(nome="Atendimento", ordem=1))
            db.session.add(Setor(nome="Produção", ordem=2))
        if not Status.query.first():
            db.session.add(Status(nome="Aguardando", cor="#ffcc00"))
        db.session.commit()
    app.run(debug=True)