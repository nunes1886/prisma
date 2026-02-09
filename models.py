from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Tabela de associação para permissões de setores
usuario_setores = db.Table('usuario_setores',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('setor_id', db.Integer, db.ForeignKey('setores.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    funcao = db.Column(db.String(20), nullable=False) # admin ou colaborador
    acesso_estoque = db.Column(db.Boolean, default=False)
    acessos = db.relationship('Setor', secondary=usuario_setores, backref=db.backref('usuarios_permitidos', lazy=True))

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(20)) # PF, PJ ou Terceiro
    documento = db.Column(db.String(20), unique=True) # CPF/CNPJ
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
    
    # Relacionamentos
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'))
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    financeiro = db.relationship('Financeiro', backref='card_ref', lazy=True)

class Financeiro(db.Model):
    __tablename__ = 'financeiro'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False) # RECEITA ou DESPESA
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pendente') # Pendente ou Pago
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