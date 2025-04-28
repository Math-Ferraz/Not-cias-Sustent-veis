from flask import Flask, render_template, request, jsonify, redirect, url_for 
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Importar classes do Flask-Login
from werkzeug.security import generate_password_hash, check_password_hash # Para gerenciar senhas de forma segura

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_projeto' # **Defina uma chave secreta forte!** Essencial para segurança da sessão.

#salvar o banco de dados na mesma pasta
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')

# Configuração do banco de dados SQLite
db = SQLAlchemy(app)

#Para criar tabela no render
with app.app_context():
    db.create_all()

# Diretório de uploads
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define o nome da função (rota) de login
login_manager.login_message = 'Por favor, faça login para acessar esta página.' # Mensagem exibida se tentar acessar página protegida sem login


# Modelo para a mensagem de contato
class MensagemContato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.datetime.utcnow) # Usar datetime.datetime.utcnow para data/hora UTC
    is_read = db.Column(db.Boolean, default=False, nullable=False) # Novo campo is_read


    def __repr__(self):
        return f"MensagemContato(nome='{self.nome}', email='{self.email}', data_envio='{self.data_envio}', is_read={self.is_read})" # Atualizado para mostrar is_read



# Modelo para a denúncia
class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.Text, nullable=False) # Descrição do problema
    endereco = db.Column(db.String(200), nullable=False) # Endereço da ocorrência
    foto_url = db.Column(db.String(200), nullable=True) # Caminho para a foto (opcional)
    data_envio = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False) # Novo campo is_read

    def __repr__(self):
        return f"Denuncia(endereco='{self.endereco}', data_envio='{self.data_envio}', is_read={self.is_read})" # Atualizado para mostrar is_read


# Modelo para a sugestão
class Sugestao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=True) # Nome (opcional no formulário HTML, mas nullable=True permite salvar sem nome)
    endereco = db.Column(db.String(200), nullable=True) # Endereço da sugestão (opcional)
    sugestao = db.Column(db.Text, nullable=False) # Conteúdo da sugestão
    data_envio = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False) # Novo campo is_read

    def __repr__(self):
        return f"Sugestao(nome='{self.nome}', data_envio='{self.data_envio}', is_read={self.is_read})" # Atualizado para mostrar is_read


# **Novo Modelo para o Usuário**
class User(UserMixin, db.Model): # Herda de UserMixin para funcionalidades do Flask-Login
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False) # Nome de usuário único
    password_hash = db.Column(db.String(200), nullable=False) # Hash da senha (NUNCA salve a senha pura!)

    def set_password(self, password):
        # Cria o hash da senha
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Verifica se a senha fornecida corresponde ao hash salvo
        return check_password_hash(self.password_hash, password)

#MODELO DE NOTICIA NO APP.PY
class Noticia(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    imagem_url = db.Column(db.String(200), nullable=True)
    data_publicacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"Noticia(titulo='{self.titulo}', data_publicacao='{self.data_publicacao}')"


# 2. ROTA PARA ADMINISTRAR NOTICIAS (listagem e envio)
@app.route('/admin/noticias', methods=['GET', 'POST'])
@login_required
def admin_noticias():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        imagem = request.files.get('imagem')
        imagem_url = None

        if not titulo or not conteudo:
            return render_template('admin_noticias.html', erro="Preencha todos os campos obrigatórios.", noticias=Noticia.query.all())

        if imagem and imagem.filename != '':
            filename = secure_filename(imagem.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem.save(filepath)
            imagem_url = f'static/uploads/{filename}'

        nova_noticia = Noticia(titulo=titulo, conteudo=conteudo, imagem_url=imagem_url)
        db.session.add(nova_noticia)
        db.session.commit()

        return redirect('/admin/noticias')

    noticias = Noticia.query.order_by(Noticia.data_publicacao.desc()).all()
    return render_template('admin_noticias.html', noticias=noticias)


# 3. ROTA PARA EXCLUIR NOTICIA
@app.route('/admin/noticia/<int:noticia_id>/excluir', methods=['POST'])
@login_required
def excluir_noticia(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    db.session.delete(noticia)
    db.session.commit()
    return redirect('/admin/noticias')    



# Função para carregar o usuário pelo ID (obrigatória para o Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Página inicial // Rota principal
@app.route('/')
def home():
    noticias = Noticia.query.order_by(Noticia.data_publicacao.desc()).all()
    return render_template('index.html', noticias=noticias)

# Enviar mensagem de contato (via JSON) - Rota original, manter se necessário ou remover
@app.route('/api/mensagem', methods=['POST'])
def receber_mensagem():
    data = request.json
    mensagem = data.get('mensagem', '')
    resposta = f"Mensagem recebida: {mensagem}"
    return jsonify({'resposta': resposta})

# Receber formulário de denúncia (com imagem)
@app.route('/enviar-denuncia', methods=['POST'])
def enviar_denuncia():
    descricao = request.form.get('descricao')
    endereco = request.form.get('endereco')
    foto = request.files.get('foto')
    foto_url = None # Inicializa a URL da foto como None

    if not descricao or not endereco:
        return jsonify({'mensagem': 'Preencha todos os campos obrigatórios.', 'sucesso': False}), 400

    if foto and foto.filename != '':
        filename = secure_filename(foto.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(filepath)
        foto_url = f'static/uploads/{filename}'

    # Cria um novo objeto Denuncia
    nova_denuncia = Denuncia(descricao=descricao, endereco=endereco, foto_url=foto_url)

    # Adiciona e salva no banco de dados
    db.session.add(nova_denuncia)
    db.session.commit()

    print(f"🚨 Nova denúncia recebida para o endereço: {endereco}")

    return jsonify({'mensagem': 'Denúncia enviada com sucesso!', 'sucesso': True})


# Receber formulário de sugestões
@app.route('/enviar-sugestao', methods=['POST'])
def enviar_sugestao():
    print("Dados do formulário de sugestão recebidos:", request.form) # Adicione esta linha
    # Captura os dados do formulário de sugestão
    nome = request.form.get('nome')
    endereco = request.form.get('endereco')
    sugestao = request.form.get('sugestao')

    # Validação aprimorada: verifica se a sugestão não está vazia ou contém apenas espaços em branco
    if not sugestao or not sugestao.strip():
        return jsonify({'mensagem': 'Por favor, preencha o campo de sugestão.', 'sucesso': False}), 400

    # Cria um novo objeto Sugestao
    nova_sugestao = Sugestao(nome=nome, endereco=endereco, sugestao=sugestao)

    # Adiciona e salva no banco de dados
    db.session.add(nova_sugestao)
    db.session.commit()

    print(f"💡 Nova sugestão recebida de {nome if nome else 'Anônimo'}")
    return jsonify({'mensagem': 'Sugestão recebida com sucesso!', 'sucesso': True})

@app.route('/enviar-contato', methods=['POST'])
def enviar_contato():
    # Captura os dados do formulário
    nome = request.form.get('nome')
    email = request.form.get('email')
    mensagem = request.form.get('mensagem')

    # Validação simples (você pode adicionar mais validações aqui)
    if not nome or not email or not mensagem:
        return jsonify({'mensagem': 'Por favor, preencha todos os campos.', 'sucesso': False}), 400

    # Cria um novo objeto MensagemContato
    nova_mensagem = MensagemContato(nome=nome, email=email, mensagem=mensagem)

    # Adiciona a nova mensagem à sessão do banco de dados e salva
    db.session.add(nova_mensagem)
    db.session.commit()

    print(f"📧 Nova mensagem de contato recebida de {nome} ({email})")

    return jsonify({'mensagem': 'Mensagem de contato recebida com sucesso!', 'sucesso': True})


# Rota para marcar uma denúncia como lida/respondida
@app.route('/mark_read/denuncia/<int:id>')
@login_required
def mark_read_denuncia(id):
    denuncia = Denuncia.query.get_or_404(id)
    denuncia.is_read = True # Define o campo is_read como True
    db.session.commit() # Salva a mudança no banco de dados
    print(f"👁️ Denúncia com ID {id} marcada como lida.")
    return redirect(url_for('admin')) # Redireciona de volta para a página admin


# Rota para marcar uma sugestão como lida/respondida
@app.route('/mark_read/sugestao/<int:id>')
@login_required
def mark_read_sugestao(id):
    sugestao = Sugestao.query.get_or_404(id)
    sugestao.is_read = True # Define o campo is_read como True
    db.session.commit() # Salva a mudança no banco de dados
    print(f"👁️ Sugestão com ID {id} marcada como lida.")
    return redirect(url_for('admin')) # Redireciona de volta para a página admin


# Rota para marcar uma mensagem de contato como lida/respondida
@app.route('/mark_read/contato/<int:id>')
@login_required
def mark_read_contato(id):
    mensagem = MensagemContato.query.get_or_404(id)
    mensagem.is_read = True # Define o campo is_read como True
    db.session.commit() # Salva a mudança no banco de dados
    print(f"👁️ Mensagem de contato com ID {id} marcada como lida.")
    return redirect(url_for('admin')) # Redireciona de volta para a página admin



# Rota para excluir uma denúncia
@app.route('/delete/denuncia/<int:id>', methods=['POST', 'GET']) # Aceita GET e POST para simplicidade, ideal seria POST
@login_required
def delete_denuncia(id):
    # Busca a denúncia pelo ID ou retorna erro 404 se não encontrar
    denuncia = Denuncia.query.get_or_404(id)

    # Exclui o registro do banco de dados
    db.session.delete(denuncia)
    db.session.commit()

    print(f"🗑️ Denúncia com ID {id} excluída.")

    # Redireciona de volta para a página admin
    return redirect(url_for('admin'))


# Rota para excluir uma sugestão
@app.route('/delete/sugestao/<int:id>', methods=['POST', 'GET']) # Aceita GET e POST para simplicidade, ideal seria POST
@login_required
def delete_sugestao(id):
    # Busca a sugestão pelo ID ou retorna erro 404 se não encontrar
    sugestao = Sugestao.query.get_or_404(id)

    # Exclui o registro do banco de dados
    db.session.delete(sugestao)
    db.session.commit()

    print(f"🗑️ Sugestão com ID {id} excluída.")

    # Redireciona de volta para a página admin
    return redirect(url_for('admin'))

# Rota para excluir uma mensagem de contato
@app.route('/delete/contato/<int:id>', methods=['POST', 'GET']) # Aceita GET e POST para simplicidade, ideal seria POST
@login_required
def delete_contato(id):
    # Busca a mensagem de contato pelo ID ou retorna erro 404 se não encontrar
    mensagem = MensagemContato.query.get_or_404(id)

    # Exclui o registro do banco de dados
    db.session.delete(mensagem)
    db.session.commit()

    print(f"🗑️ Mensagem de contato com ID {id} excluída.")

    # Redireciona de volta para a página admin
    return redirect(url_for('admin'))

# Rota para logout
@app.route('/logout')
@login_required # Opcional: Garante que apenas usuários logados podem acessar esta rota
def logout():
    logout_user() # Função do Flask-Login para deslogar o usuário
    # Redireciona para a página inicial (ou para onde você preferir após o logout)
    return redirect(url_for('home'))

# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver autenticado, redireciona para a página admin
    if current_user.is_authenticated:
        return redirect(url_for('admin'))

    # Cria um formulário de login fictício para exemplo
    # Em aplicações reais, usaria Flask-WTF ou similar para formulários seguros
    # Aqui, vamos apenas acessar request.form diretamente
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Busca o usuário no banco de dados pelo nome de usuário
        user = User.query.filter_by(username=username).first()

        # Verifica se o usuário existe e se a senha está correta
        if user and user.check_password(password):
            # Se as credenciais estiverem corretas, loga o usuário
            login_user(user) # Usa a função do Flask-Login para logar o usuário
            # Redireciona para a página que o usuário tentou acessar antes do login,
            # ou para a página admin por padrão
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        else:
            # Se as credenciais estiverem incorretas, pode exibir uma mensagem de erro (opcional)
            # Por enquanto, vamos apenas renderizar o template novamente
            print("Login falhou: Usuário ou senha incorretos.") # Imprime no console do Flask
            # Em uma aplicação real, passaria uma mensagem de erro para o template

    # Renderiza o template de login se o método for GET ou login falhou
    return render_template('login.html')

#Para a página admin
@app.route('/admin')
@login_required # <--- Agora esta rota exige login!
def admin():
    denuncias = Denuncia.query.order_by(Denuncia.data_envio.desc()).all()
    mensagens = MensagemContato.query.order_by(MensagemContato.data_envio.desc()).all()
    sugestoes = Sugestao.query.order_by(Sugestao.data_envio.desc()).all()
    return render_template('admin.html', denuncias=denuncias, mensagens=mensagens, sugestoes=sugestoes)

if __name__ == '__main__':
    # Cria as tabelas do banco de dados antes de rodar a aplicação
    with app.app_context():
        db.create_all()

        # **Exemplo de como criar um usuário administrador (FAÇA ISSO APENAS UMA VEZ!)**
        # Você pode remover ou comentar este bloco depois de criar o primeiro usuário.
        #if User.query.filter_by(username='admin').first() is None:
            #admin_user = User(username='admin')
            #admin_user.set_password('projeto99admin') # **TROQUE 'sua_senha_admin' por uma senha forte!**
            #db.session.add(admin_user)
            #db.session.commit()
            #print("🔐 Usuário 'admin' criado com sucesso!")

    app.run(debug=True)