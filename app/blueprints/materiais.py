from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Material

materiais_bp = Blueprint('materiais', __name__)

@materiais_bp.route('/materiais')
@login_required
def index():
    # Lista todos os materiais ativos
    itens = Material.query.filter_by(ativo=True).all()
    return render_template('materiais/index.html', itens=itens)

@materiais_bp.route('/materiais/novo', methods=['POST'])
@login_required
def novo():
    if current_user.nivel_acesso > 1:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('materiais.index'))

    nome = request.form.get('nome')
    unidade = request.form.get('unidade')
    
    # Tratamento de vírgula para ponto
    preco_venda = request.form.get('preco_venda').replace(',', '.')
    preco_custo = request.form.get('preco_custo').replace(',', '.')
    preco_revenda = request.form.get('preco_revenda').replace(',', '.') # NOVO

    novo_item = Material(
        nome=nome,
        unidade=unidade,
        preco_venda=float(preco_venda),
        preco_custo=float(preco_custo) if preco_custo else 0.0,
        # Lógica: Se não preencher revenda, usa o preço de venda normal
        preco_revenda=float(preco_revenda) if preco_revenda else float(preco_venda)
    )
    
    db.session.add(novo_item)
    db.session.commit()
    flash('Material cadastrado com sucesso!', 'success')
    return redirect(url_for('materiais.index'))

@materiais_bp.route('/materiais/deletar/<int:id>')
@login_required
def deletar(id):
    if current_user.nivel_acesso > 1:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('materiais.index'))
        
    item = Material.query.get_or_404(id)
    item.ativo = False # Soft delete (não apaga do banco, só esconde)
    db.session.commit()
    flash('Material removido.', 'info')
    return redirect(url_for('materiais.index'))

@materiais_bp.route('/materiais/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    if current_user.nivel_acesso > 1:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('materiais.index'))

    # Busca o material pelo ID ou dá erro 404 se não achar
    material = Material.query.get_or_404(id)

    # Atualiza os dados vindos do formulário
    material.nome = request.form.get('nome')
    material.unidade = request.form.get('unidade')
    
    # Tratamento de vírgula/ponto
    p_venda = request.form.get('preco_venda').replace(',', '.')
    p_revenda = request.form.get('preco_revenda').replace(',', '.')
    p_custo = request.form.get('preco_custo').replace(',', '.')

    material.preco_venda = float(p_venda)
    # Se revenda vier vazio, assume igual a venda
    material.preco_revenda = float(p_revenda) if p_revenda else float(p_venda)
    material.preco_custo = float(p_custo) if p_custo else 0.0

    db.session.commit()
    flash('Material atualizado com sucesso!', 'success')
    return redirect(url_for('materiais.index'))