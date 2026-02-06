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
    # ... (outros campos: data, cliente_id, usuario_id, valor_total) ...
    
    # REMOVER ou IGNORAR o campo antigo 'status' string se quiser, 
    # mas vamos manter por compatibilidade por enquanto e usar o etapa_id como principal.
    status = db.Column(db.String(20), default='Aguardando') 
    
    # NOVO CAMPO: Em qual coluna esse pedido está?
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapa.id'), nullable=True)

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

    # ... (Classes anteriores: Usuario, Configuracao, Material, Cliente, Pedido, ItemPedido)

class Lancamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tipo: 'Entrada' (Dinheiro entrando) ou 'Saida' (Dinheiro saindo)
    tipo = db.Column(db.String(10), nullable=False) 
    
    descricao = db.Column(db.String(200), nullable=False) # Ex: "Pagamento Pedido #4" ou "Conta de Luz"
    valor = db.Column(db.Float, nullable=False)
    
    # Detalhes
    forma_pagamento = db.Column(db.String(50)) # Pix, Dinheiro, Cartão Crédito, Boleto
    
    # Vínculo com Pedido (Opcional: Só preenche se for recebimento de venda)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=True)
    
    # Quem lançou isso no sistema?
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    def __repr__(self):
        return f'<Lancamento R$ {self.valor}>'
    
class Etapa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ordem = db.Column(db.Integer, default=0) # 1, 2, 3... para ordenar na tela
    
    # Relacionamento com Pedidos
    pedidos = db.relationship('Pedido', backref='etapa', lazy=True)