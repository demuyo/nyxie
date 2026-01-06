# web_server.py
from flask import Flask, render_template, request, jsonify
from cogs.conversation import ConversationSystem
import asyncio
import os
import traceback
import secrets
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # ⬅️ ADICIONE ISSO

class MockBot:
    pass

mock_bot = MockBot()
conv_system = ConversationSystem(mock_bot)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        
        print(f"📩 Recebido: {data}")
        
        user_id = data.get('user_id', 'web_user')
        mensagem = data.get('message', '')
        
        if not mensagem:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resposta = loop.run_until_complete(
            conv_system.gerar_resposta(user_id, mensagem)
        )
        loop.close()
        
        print(f"✅ Resposta: {resposta}")
        
        return jsonify({'response': resposta})
    
    except Exception as e:
        print(f"❌ ERRO: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)