from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Rota para a página principal
@app.route('/')
def home():
    return render_template('index.html')

# Rota para receber interações via AJAX do script.js
@app.route('/api/mensagem', methods=['POST'])
def receber_mensagem():
    data = request.json
    mensagem = data.get('mensagem', '')
    resposta = f"Mensagem recebida: {mensagem}"
    return jsonify({'resposta': resposta})

if __name__ == '__main__':
    app.run(debug=True)
