from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se o cara já tá logado, chuta ele pro dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) # Vamos criar 'main.dashboard' jájá

    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        
        user = Usuario.query.filter_by(username=username).first()

        # Verifica se o usuário existe E se a senha bate com o hash
        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            
            # Redirecionamento inteligente baseada no cargo (Seu requisito #1)
            # 0=Admin, 1=Financeiro, 2=Vendas, 3=Produção
            if user.nivel_acesso == 3:
                return redirect(url_for('producao.kanban')) # Futuro
            else:
                return redirect(url_for('main.dashboard')) # Futuro
        else:
            flash('Usuário ou senha incorretos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))