from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import db, Configuracao, Usuario
from app.models import Etapa

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def index():
    config = Configuracao.query.first()
    
    if request.method == 'POST':
        config.nome_empresa = request.form.get('nome_empresa')
        config.telefone = request.form.get('telefone')
        config.endereco = request.form.get('endereco')
        config.logo_filename = request.form.get('logo_filename') # Caso use no futuro
        
        db.session.commit()
        flash('Configurações atualizadas!', 'success')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', config=config)

# --- GERENCIAR USUÁRIOS ---
@settings_bp.route('/configuracoes/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    # Segurança: Só Admin entra aqui
    if current_user.nivel_acesso != 0:
        flash('Acesso restrito apenas ao Administrador.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        username = request.form.get('username')
        senha = request.form.get('senha')
        nivel = int(request.form.get('nivel_acesso')) # 0=Admin, 1=Vendedor
        
        if Usuario.query.filter_by(username=username).first():
            flash('Erro: Esse login já existe!', 'warning')
        else:
            novo_user = Usuario(
                nome_completo=nome,
                username=username,
                senha_hash=generate_password_hash(senha),
                nivel_acesso=nivel
            )
            db.session.add(novo_user)
            db.session.commit()
            flash(f'Usuário {nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('settings.usuarios'))

    lista_usuarios = Usuario.query.all()
    return render_template('settings/usuarios.html', usuarios=lista_usuarios)

# --- EDITAR USUÁRIO (Senha / Nível) ---
@settings_bp.route('/configuracoes/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.nivel_acesso != 0:
        return redirect(url_for('main.dashboard'))
        
    user = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        user.nome_completo = request.form.get('nome')
        user.username = request.form.get('username')
        user.nivel_acesso = int(request.form.get('nivel_acesso'))
        
        # Só troca a senha se o campo não estiver vazio
        nova_senha = request.form.get('senha')
        if nova_senha:
            user.senha_hash = generate_password_hash(nova_senha)
            flash('Senha atualizada com sucesso!', 'info')
            
        db.session.commit()
        flash('Dados do usuário atualizados!', 'success')
        return redirect(url_for('settings.usuarios'))
        
    return render_template('settings/editar_usuario.html', user=user)

# --- EXCLUIR USUÁRIO ---
@settings_bp.route('/configuracoes/usuarios/deletar/<int:id>')
@login_required
def deletar_usuario(id):
    if current_user.nivel_acesso != 0:
        return redirect(url_for('main.dashboard'))
        
    user = Usuario.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode se auto-excluir!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário removido.', 'info')
        
    return redirect(url_for('settings.usuarios'))


@settings_bp.route('/configuracoes/kanban', methods=['GET', 'POST'])
@login_required
def kanban_setup():
    if current_user.nivel_acesso != 0:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        ordem = request.form.get('ordem')
        
        nova_etapa = Etapa(nome=nome, ordem=int(ordem))
        db.session.add(nova_etapa)
        db.session.commit()
        flash('Nova coluna adicionada!', 'success')
        return redirect(url_for('settings.kanban_setup'))

    etapas = Etapa.query.order_by(Etapa.ordem).all()
    return render_template('settings/kanban_setup.html', etapas=etapas)

@settings_bp.route('/configuracoes/kanban/deletar/<int:id>')
@login_required
def deletar_etapa(id):
    if current_user.nivel_acesso != 0: return redirect(url_for('main.dashboard'))
    
    etapa = Etapa.query.get_or_404(id)
    # Segurança: Se tiver pedidos nessa etapa, não deixa apagar para não quebrar o banco
    if etapa.pedidos:
        flash('Não é possível apagar uma etapa que tem pedidos dentro! Mova-os antes.', 'danger')
    else:
        db.session.delete(etapa)
        db.session.commit()
        flash('Coluna removida.', 'info')
        
    return redirect(url_for('settings.kanban_setup'))