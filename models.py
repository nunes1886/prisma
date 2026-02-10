from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Instancia o banco de dados aqui para ser importado no app.py
db = SQLAlchemy()

# Tabela de associação (Muitos-para-Muitos)
usuario_setores = db.Table('usuario_setores',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('setor_id', db.Integer, db.ForeignKey('setores.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    funcao = db.Column(db.String(20), default='colaborador') # admin, vendas, producao
    acesso_estoque = db.Column(db.Boolean, default=False)
    acessos = db.relationship('Setor', secondary=usuario_setores, backref=db.backref('usuarios_permitidos', lazy=True))

    def set_password(self, password):
        self.senha = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.senha, password)

class Material(db.Model):
    __tablename__ = 'materiais'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_final = db.Column(db.Float, default=0.0)      # Preço Cliente Final
    preco_terceiro = db.Column(db.Float, default=0.0)   # Preço Revenda

class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cor = db.Column(db.String(20), default='#6c757d')
    cards = db.relationship('Card', backref='status_ref', lazy=True)

class Setor(db.Model):
    __tablename__ = 'setores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    cards = db.relationship('Card', backref='setor_ref', lazy=True)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(20), default='Final') # Final, Terceiro, PJ
    documento = db.Column(db.String(20)) 
    whatsapp = db.Column(db.String(20))
    pedidos = db.relationship('Card', backref='cliente_ref', lazy=True)

class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    valor_total = db.Column(db.Float, default=0.0)
    prazo = db.Column(db.String(20))
    is_archived = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80)) 
    
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=True)
    financeiro = db.relationship('Financeiro', backref='card_ref', lazy=True)

class Financeiro(db.Model):
    __tablename__ = 'financeiro'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False) # RECEITA ou DESPESA
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Pendente')
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=True)