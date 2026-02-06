from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Lancamento
from datetime import datetime

financeiro_bp = Blueprint('financeiro', __name__)

@financeiro_bp.route('/financeiro')
@login_required
def index():
    # Busca todos os lançamentos (do mais recente para o mais antigo)
    lancamentos = Lancamento.query.order_by(Lancamento.data.desc()).all()
    
    # Cálculos Matemáticos
    total_entradas = sum(l.valor for l in lancamentos if l.tipo == 'Entrada')
    total_saidas = sum(l.valor for l in lancamentos if l.tipo == 'Saida')
    saldo = total_entradas - total_saidas
    
    return render_template('financeiro/index.html', 
                           lancamentos=lancamentos,
                           entradas=total_entradas,
                           saidas=total_saidas,
                           saldo=saldo)

@financeiro_bp.route('/financeiro/lancar', methods=['POST'])
@login_required
def lancar():
    tipo = request.form.get('tipo') # Entrada ou Saida
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor').replace(',', '.'))
    forma_pagamento = request.form.get('forma_pagamento')
    data_str = request.form.get('data')

    novo_lancamento = Lancamento(
        tipo=tipo,
        descricao=descricao,
        valor=valor,
        forma_pagamento=forma_pagamento,
        data=datetime.strptime(data_str, '%Y-%m-%d') if data_str else datetime.utcnow(),
        usuario_id=current_user.id
    )
    
    db.session.add(novo_lancamento)
    db.session.commit()
    
    flash('Lançamento registrado com sucesso!', 'success')
    return redirect(url_for('financeiro.index'))