from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Cliente

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes')
@login_required
def index():
    # Sistema de busca simples
    busca = request.args.get('q')
    if busca:
        # Busca por nome OU documento (CPF/CNPJ)
        clientes = Cliente.query.filter(
            (Cliente.nome.contains(busca)) | 
            (Cliente.documento.contains(busca))
        ).all()
    else:
        clientes = Cliente.query.order_by(Cliente.id.desc()).all()
        
    return render_template('clientes/index.html', clientes=clientes)

@clientes_bp.route('/clientes/novo', methods=['POST'])
@login_required
def novo():
    nome = request.form.get('nome')
    tipo = request.form.get('tipo_pessoa')
    doc = request.form.get('documento')
    tel = request.form.get('telefone')
    # O checkbox HTML só envia valor se estiver marcado
    is_revenda = True if request.form.get('is_revenda') else False
    
    novo_cliente = Cliente(
        nome=nome,
        tipo_pessoa=tipo,
        documento=doc,
        telefone=tel,
        is_revenda=is_revenda
    )
    
    db.session.add(novo_cliente)
    db.session.commit()
    flash('Cliente cadastrado!', 'success')
    return redirect(url_for('clientes.index'))

@clientes_bp.route('/clientes/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    
    cliente.nome = request.form.get('nome')
    cliente.tipo_pessoa = request.form.get('tipo_pessoa')
    cliente.documento = request.form.get('documento')
    cliente.telefone = request.form.get('telefone')
    cliente.is_revenda = True if request.form.get('is_revenda') else False
    
    db.session.commit()
    flash('Dados atualizados.', 'success')
    return redirect(url_for('clientes.index'))

@clientes_bp.route('/clientes/deletar/<int:id>')
@login_required
def deletar(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente removido.', 'info')
    return redirect(url_for('clientes.index'))