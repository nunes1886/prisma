from . import db
from flask_login import UserMixin
from datetime import datetime

# --- TABELA DE CONFIGURAÇÃO (BRANDING) ---
class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(100), default="Minha Gráfica")
    # Vamos salvar apenas o nome do arquivo, ex: 'logo.png'
    logo_filename = db.Column(db.String(200), default="logo_padrao.png") 
    favicon_filename = db.Column(db.String(200), default="img/favicon_padrao.png")

# --- TABELA DE USUÁRIOS (COM HIERARQUIA) ---
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nome_completo = db.Column(db.String(100))
    senha_hash = db.Column(db.String(200), nullable=False)
    
    # Níveis: 0=Admin, 1=Financeiro, 2=Vendas, 3=Produção
    nivel_acesso = db.Column(db.Integer, default=3, nullable=False)
    ativo = db.Column(db.Boolean, default=True)

# --- TABELA DE CLIENTES ---
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_pessoa = db.Column(db.String(2), default='PF') # PF ou PJ
    nome = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20)) # CPF/CNPJ
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    is_revenda = db.Column(db.Boolean, default=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Ex: Lona Brilho 440g
    
    # Unidade de Medida: 'm2' (Metro Quadrado), 'un' (Unidade), 'ml' (Metro Linear)
    unidade = db.Column(db.String(10), default='m2') 
    
    preco_custo = db.Column(db.Float, default=0.0) # Quanto você paga
    preco_venda = db.Column(db.Float, nullable=False) # Quanto você cobra (Base do cálculo)

    preco_revenda = db.Column(db.Float, default=0.0) # Preço para Terceirizados/Agências
    
    # Estoque atual (Opcional por enquanto, mas bom já ter)
    estoque_atual = db.Column(db.Float, default=0.0) 
    
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Material {self.nome}>'
    
    # ... (Classes anteriores: Usuario, Configuracao, Material, Cliente)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status: 'Orcamento', 'Aprovado', 'Producao', 'Finalizado', 'Cancelado'
    status = db.Column(db.String(20), default='Orcamento')
    
    # Relacionamentos
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False) # Quem atendeu
    
    # Totais (Cache para não precisar somar itens toda hora)
    valor_total = db.Column(db.Float, default=0.0)
    
    # Relacionamento Reverso (Um Pedido tem Vários Itens)
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")
    
    # Para facilitar acesso aos dados do cliente/vendedor
    cliente = db.relationship('Cliente', backref='pedidos')
    vendedor = db.relationship('Usuario', backref='vendas')

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    
    # Detalhes do Item
    altura = db.Column(db.Float, default=0.0) # Em metros (Ex: 1.50)
    largura = db.Column(db.Float, default=0.0) # Em metros (Ex: 3.00)
    quantidade = db.Column(db.Integer, default=1)
    
    # Valores CONGELADOS (Importante: Se o preço da lona subir amanhã, este pedido antigo não muda)
    preco_unitario = db.Column(db.Float, nullable=False) # O preço do m² ou un na hora da venda
    subtotal = db.Column(db.Float, nullable=False) # (Alt x Larg x Preço) * Qtd
    
    # Relacionamento para pegar nome do material
    material = db.relationship('Material')