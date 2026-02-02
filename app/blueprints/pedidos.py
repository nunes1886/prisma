from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Pedido, ItemPedido, Cliente, Material
from datetime import datetime
import json

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/pedidos/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            # 1. Dados Básicos do Pedido
            cliente_id = request.form.get('cliente_id')
            data_str = request.form.get('data')
            
            if not cliente_id:
                flash('Selecione um cliente!', 'warning')
                return redirect(url_for('pedidos.novo'))

            # Cria o Cabeçalho do Pedido
            novo_pedido = Pedido(
                cliente_id=int(cliente_id),
                usuario_id=current_user.id,
                data_criacao=datetime.strptime(data_str, '%Y-%m-%d') if data_str else datetime.utcnow(),
                status='Orcamento',
                valor_total=0.0 # Será atualizado após somar os itens
            )
            db.session.add(novo_pedido)
            db.session.flush() # Gera o ID do pedido antes do commit final

            # 2. Processamento dos Itens (A Mágica)
            itens_processados = {} 
            
            for key, value in request.form.items():
                if key.startswith('itens['):
                    partes = key.split('[') 
                    indice = partes[1].replace(']', '')
                    campo = partes[2].replace(']', '')
                    
                    if indice not in itens_processados:
                        itens_processados[indice] = {}
                    
                    itens_processados[indice][campo] = value

            total_pedido = 0.0

            # 3. Salvar cada item no banco
            for idx, dados in itens_processados.items():
                material = Material.query.get(dados['material_id'])
                
                qtd = int(dados['quantidade'])
                largura = float(dados['largura']) if dados.get('largura') else 0.0
                altura = float(dados['altura']) if dados.get('altura') else 0.0
                
                # Recalcula preço no servidor
                cliente = Cliente.query.get(cliente_id)
                preco_unit = material.preco_revenda if cliente.is_revenda else material.preco_venda
                
                subtotal = 0.0
                if material.unidade == 'm2':
                    area = largura * altura
                    subtotal = area * preco_unit * qtd
                else:
                    subtotal = preco_unit * qtd

                total_pedido += subtotal

                novo_item = ItemPedido(
                    pedido_id=novo_pedido.id,
                    material_id=material.id,
                    altura=altura,
                    largura=largura,
                    quantidade=qtd,
                    preco_unitario=preco_unit,
                    subtotal=subtotal
                )
                db.session.add(novo_item)

            # 4. Atualiza o total e finaliza
            novo_pedido.valor_total = total_pedido
            db.session.commit()

            flash(f'Pedido #{novo_pedido.id} salvo com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar pedido: {str(e)}', 'danger')
            return redirect(url_for('pedidos.novo'))

    # --- MÉTODO GET ---
    clientes = Cliente.query.filter_by(is_revenda=False).order_by(Cliente.nome).all()
    revendas = Cliente.query.filter_by(is_revenda=True).order_by(Cliente.nome).all()
    materiais = Material.query.filter_by(ativo=True).all()
    
    hoje = datetime.utcnow().strftime('%Y-%m-%d')

    materiais_dict = {}
    for m in materiais:
        materiais_dict[m.id] = {
            'nome': m.nome,
            'unidade': m.unidade,
            'preco_venda': m.preco_venda,
            'preco_revenda': m.preco_revenda
        }

    return render_template('pedidos/novo.html', 
                           clientes=clientes, 
                           revendas=revendas,
                           materiais=materiais,
                           now=hoje,
                           materiais_json=json.dumps(materiais_dict))

@pedidos_bp.route('/pedidos/<int:id>')
@login_required
def visualizar(id):
    pedido = Pedido.query.get_or_404(id)
    # ATENÇÃO: O nome do arquivo aqui deve ser igual ao que você salvou na pasta templates
    return render_template('pedidos/detalhes.html', pedido=pedido)

@pedidos_bp.route('/pedidos/<int:id>/status/<string:novo_status>')
@login_required
def alterar_status(id, novo_status):
    pedido = Pedido.query.get_or_404(id)
    
    # Bloqueio simples de segurança
    if pedido.status == 'Finalizado' and novo_status == 'Cancelado':
        flash('Pedido já finalizado não pode ser cancelado.', 'warning')
        return redirect(url_for('pedidos.visualizar', id=id))

    pedido.status = novo_status
    db.session.commit()
    
    flash(f'Status atualizado para: {novo_status}', 'success')
    return redirect(url_for('pedidos.visualizar', id=id))