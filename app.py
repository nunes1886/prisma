import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import func

# Importa o banco e as tabelas do arquivo models.py
from models import db, Usuario, Cliente, Card, Financeiro, Setor, Status, Material

# --- CONFIGURAÇÃO ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'prisma-erp-2026-secure-token'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prisma.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco com este app
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- ROTAS DE ACESSO ---

@app.route('/')
@login_required
def index():
    # Carrega colunas do Kanban
    setores = Setor.query.order_by(Setor.ordem).all()
    return render_template('index.html', setores=setores, user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ROTAS DE GESTÃO (Admin) ---

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.funcao != 'admin': return redirect(url_for('index'))

    # KPIs
    faturamento = db.session.query(func.sum(Financeiro.valor)).filter(Financeiro.status == 'Pago').scalar() or 0.0
    a_receber = db.session.query(func.sum(Financeiro.valor)).filter(Financeiro.status == 'Pendente').scalar() or 0.0
    ativos = Card.query.filter_by(is_archived=False).count()

    # Dados do Gráfico
    setores = Setor.query.all()
    labels_setores = [s.nome for s in setores]
    valores_setores = [Card.query.filter_by(setor_id=s.id, is_archived=False).count() for s in setores]

    return render_template('dashboard.html', faturamento=faturamento, receber=a_receber, ativos=ativos,
                           labels_setores=labels_setores, valores_setores=valores_setores)

@app.route('/usuarios')
@login_required
def usuarios():
    if current_user.funcao != 'admin': return redirect(url_for('index'))
    lista_users = Usuario.query.all()
    return render_template('usuarios.html', usuarios=lista_users) # Você precisará criar esse HTML depois se quiser gerenciar

# --- ROTAS DE VENDAS E CLIENTES ---

@app.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/cliente/novo', methods=['POST'])
@login_required
def novo_cliente():
    try:
        c = Cliente(
            nome=request.form.get('nome'),
            tipo=request.form.get('tipo'), # Final, Terceiro, etc
            documento=request.form.get('documento'),
            whatsapp=request.form.get('whatsapp')
        )
        db.session.add(c); db.session.commit()
        flash('Cliente cadastrado!')
    except:
        flash('Erro: Verifique se o documento já existe.')
    return redirect(url_for('listar_clientes'))

@app.route('/pedido/novo', methods=['GET', 'POST'])
@login_required
def novo_pedido():
    # Bloqueia quem é da produção
    if current_user.funcao == 'producao':
        flash('Acesso restrito.', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Dados do Form
            cliente_id = int(request.form.get('cliente_id'))
            prazo = request.form.get('prazo')
            resumo_itens = request.form.get('resumo_itens') # Vem do JS
            valor_total = float(request.form.get('valor_total_pedido'))
            titulo_pedido = request.form.get('titulo_pedido')

            # Setores Padrão
            setor_ini = Setor.query.order_by(Setor.ordem).first()
            status_ini = Status.query.first()

            # Cria Card
            novo_card = Card(
                titulo=titulo_pedido,
                descricao=resumo_itens,
                valor_total=valor_total,
                cliente_id=cliente_id,
                setor_id=setor_ini.id,
                status_id=status_ini.id,
                prazo=prazo,
                created_by=current_user.username
            )
            db.session.add(novo_card)
            db.session.flush() # Gera o ID

            # Gera Financeiro
            if valor_total > 0:
                dt_venc = datetime.strptime(prazo, '%Y-%m-%d').date()
                fin = Financeiro(
                    tipo='RECEITA',
                    descricao=f"Pedido #{novo_card.id} - {titulo_pedido}",
                    valor=valor_total,
                    data_vencimento=dt_venc,
                    card_id=novo_card.id
                )
                db.session.add(fin)
            
            db.session.commit()
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            return f"Erro ao salvar: {e}"

    # GET: Mostra tela
    clientes = Cliente.query.order_by(Cliente.nome).all()
    materiais = Material.query.order_by(Material.nome).all()
    return render_template('novo_pedido.html', clientes=clientes, materiais=materiais)

# --- ROTAS FINANCEIRAS E CONFIG ---

@app.route('/financeiro')
@login_required
def financeiro():
    if current_user.funcao == 'producao': return redirect(url_for('index'))
    receitas = Financeiro.query.filter_by(tipo='RECEITA').all()
    total_receber = sum(r.valor for r in receitas if r.status == 'Pendente')
    return render_template('financeiro.html', receitas=receitas, total_receber=total_receber)

@app.route('/financeiro/baixar/<int:id>', methods=['POST'])
@login_required
def baixar_pagamento(id):
    lancamento = Financeiro.query.get_or_404(id)
    if lancamento.status == 'Pendente':
        lancamento.status = 'Pago'
        lancamento.data_pagamento = datetime.now().date()
        db.session.commit()
        flash('Pagamento confirmado!')
    return redirect(url_for('financeiro'))

@app.route('/config/materiais', methods=['GET', 'POST'])
@login_required
def config_materiais():
    if current_user.funcao != 'admin': return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            m = Material(
                nome=request.form.get('nome'),
                preco_final=float(request.form.get('preco_final').replace(',', '.')),
                preco_terceiro=float(request.form.get('preco_terceiro').replace(',', '.'))
            )
            db.session.add(m)
            db.session.commit()
            flash('Material salvo!')
        except: flash('Erro ao salvar material.')
        
    materiais = Material.query.all()
    return render_template('config_materiais.html', materiais=materiais)

@app.route('/material/excluir/<int:id>')
@login_required
def excluir_material(id):
    if current_user.funcao == 'admin':
        m = Material.query.get(id)
        if m: db.session.delete(m); db.session.commit()
    return redirect(url_for('config_materiais'))

@app.route('/orcamento/print/<int:id>')
@login_required
def print_orcamento(id):
    card = Card.query.get_or_404(id)
    fin = Financeiro.query.filter_by(card_id=id).first()
    return render_template('orcamento_print.html', card=card, financeiro=fin)

# --- INICIALIZAÇÃO DO BANCO (RESET) ---

if __name__ == '__main__':
    with app.app_context():
        # Cria todas as tabelas novas do models.py
        db.create_all()

        # 1. Cria Admin se não existir
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(username='admin', funcao='admin')
            admin.set_password('123') # Senha padrão
            db.session.add(admin)
            print(">>> Admin criado.")

        # 2. Cria Setores Iniciais
        if not Setor.query.first():
            db.session.add_all([
                Setor(nome="Arte", ordem=1),
                Setor(nome="Impressão", ordem=2),
                Setor(nome="Acabamento", ordem=3),
                Setor(nome="Entrega", ordem=4)
            ])
            print(">>> Setores criados.")

        # 3. Cria Status Iniciais
        if not Status.query.first():
            db.session.add_all([
                Status(nome="Aguardando", cor="#ffc107"),
                Status(nome="Produzindo", cor="#0d6efd"),
                Status(nome="Pronto", cor="#198754")
            ])
            print(">>> Status criados.")

        # 4. Cria Materiais de Exemplo
        if not Material.query.first():
            db.session.add_all([
                Material(nome="Lona 440g", preco_final=80.0, preco_terceiro=45.0),
                Material(nome="Adesivo Vinil", preco_final=90.0, preco_terceiro=55.0)
            ])
            print(">>> Materiais criados.")

        db.session.commit()
        print(">>> Banco de dados PRISMA pronto!")

    app.run(debug=True)