from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import db, Configuracao
from werkzeug.utils import secure_filename
import os

settings_bp = Blueprint('settings', __name__)

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ico'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def index():
    config_db = Configuracao.query.first()
    
    if request.method == 'POST':
        # 1. Nome da Empresa
        novo_nome = request.form.get('nome_empresa')
        if novo_nome:
            config_db.nome_empresa = novo_nome

        # 2. Upload da Logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                caminho_salvar = os.path.join(current_app.root_path, 'static', 'img', filename)
                file.save(caminho_salvar)
                config_db.logo_filename = f"img/{filename}"

        # 3. Upload do Favicon (NOVO CÓDIGO)
        if 'favicon' in request.files:
            file = request.files['favicon']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"fav_{file.filename}") # Prefixo fav_ para organizar
                caminho_salvar = os.path.join(current_app.root_path, 'static', 'img', filename)
                file.save(caminho_salvar)
                config_db.favicon_filename = f"img/{filename}"

        db.session.commit()
        flash('Configurações atualizadas com sucesso!', 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/index.html', config=config_db)