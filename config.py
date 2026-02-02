import os

class Config:
    # Chave de segurança para proteger formulários (em produção, mudamos isso)
    SECRET_KEY = 'chave-secreta-do-prisma-sistema-offline'
    
    # Caminho do Banco de Dados SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'prisma.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False