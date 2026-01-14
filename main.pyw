import discord, asyncio, os, json, random
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from threading import Thread
from waitress import serve
import traceback

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('DISCORD_TEST_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

def get_prefix(bot, message):
    """Retorna prefix customizado ou padrão"""
    if message.guild:
        owner_cog = bot.get_cog('Owner')
        if owner_cog and str(message.guild.id) in owner_cog.prefixes:
            return owner_cog.prefixes[str(message.guild.id)]
    return '!'

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# ====== COMANDOS QUE SÓ FUNCIONAM EM SERVIDOR ======
COMANDOS_SERVIDOR_ONLY = [
    # ==================== MODERAÇÃO ====================
    'kick',           # expulsa membro
    'ban',            # bane membro
    'unban',          # desbane por ID
    'banlist',        # lista banidos
    'timeout',        # dá timeout
    'removetimeout',  # remove timeout
    'warn',           # adiciona aviso
    'warns',          # mostra avisos
    'clearwarns',     # limpa avisos
    'nick',           # altera apelido
    
    # ==================== CARGOS ====================
    'giverole',       # adiciona cargo
    'takerole',       # remove cargo
    'roles',          # lista cargos
    'createrole',     # cria cargo
    'deleterole',     # deleta cargo
    
    # ==================== CANAIS ====================
    'createchannel',  # cria canal
    'deletechannel',  # deleta canal
    'createcategory', # cria categoria
    'lock',           # bloqueia canal
    'unlock',         # desbloqueia canal
    'slowmode',       # define slowmode
    
    # ==================== MENSAGENS ====================
    'clear',          # limpa mensagens
    'announce',       # envia anúncio
    
    # ==================== INFORMAÇÕES ====================
    'serverinfo',     # info do servidor
    'membercount',    # contagem de membros
    
    # ==================== CHAT EM CANAL ====================
    'forcestop',      # para chat AI
    'chats',          # lista chats ativos
    'chat',           # ajuda moderação
    'stopchat',       # encerra o chat automático
    'talk',           # envia uma mensagem avulsa para nyxie

    # ==================== OUTROS ====================
    'userinfo',       # info do usuário
]

# ====== FLASK APP COM TERMINAL WEB ======
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())

# Referência global para o sistema de conversa
conversation_system = None

# ⬅️ NOVO: Armazena confirmações pendentes da web
web_pending_confirmations = {}

@app.route('/')
def home():
    """Renderiza o terminal web"""
    return render_template('index.html')

@app.route('/quotes')
def get_quotes():
    """Retorna quotes e ASCII art aleatórios baseado no dispositivo"""
    try:
        # Detecta se é mobile pelo User-Agent
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        
        # Carrega o JSON
        with open('cogs/assets/lines.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Escolhe quote aleatória
        quote = random.choice(data['frases'])
        
        # Escolhe ASCII baseado no dispositivo
        if is_mobile:
            # Mobile: só pode usar ascii_both
            ascii_item = random.choice(data['ascii_both'])
        else:
            # Desktop: pode usar desktop_only + both (todos)
            all_desktop_ascii = data['ascii_desktop_only'] + data['ascii_both']
            ascii_item = random.choice(all_desktop_ascii)
        
        return jsonify({
            'quote': quote,
            'ascii_name': ascii_item['name'],
            'ascii_art': ascii_item['art'],
            'is_mobile': is_mobile
        })
    except Exception as e:
        print(f"❌ Erro ao carregar quotes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'quote': 'close the world, open the nExt',
            'ascii_name': 'fallback',
            'ascii_art': '> NYXIE.TERMINAL',
            'is_mobile': False
        })

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para conversação web com sistema de confirmação de modelo"""
    try:
        global conversation_system, web_pending_confirmations
        
        if conversation_system is None:
            conversation_system = bot.get_cog('ConversationSystem')
        
        if conversation_system is None:
            return jsonify({'error': 'Sistema de conversa não disponível'}), 503
        
        data = request.json
        
        print(f"📩 Recebido: {data}")
        
        user_id = data.get('user_id', 'web_user')
        mensagem = data.get('message', '')
        history_frontend = data.get('history', [])
        user_model = data.get('model', None)
        
        if not mensagem:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # ⬅️ NOVO: Verifica se precisa recomendar modelo
        if user_model and user_model != 'openai/gpt-oss-120b':
            recomendacao = conversation_system.deve_recomendar_modelo_forte(
                user_id, 
                mensagem, 
                user_model
            )
            
            if recomendacao:
                # Salva confirmação pendente
                web_pending_confirmations[user_id] = {
                    'mensagem_original': mensagem,
                    'modelo_recomendado': recomendacao['modelo_recomendado'],
                    'razao': recomendacao['razao']
                }
                
                modelo_rec_info = conversation_system.models_config[recomendacao['modelo_recomendado']]
                
                return jsonify({
                    'response': f"ó, {recomendacao['razao']}\n\nquer trocar pro modelo mais forte?",
                    'model_recommendation': {
                        'model_id': recomendacao['modelo_recomendado'],
                        'model_name': modelo_rec_info['name'],
                        'reason': recomendacao['razao']
                    }
                })
        
        # Gera resposta
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resposta = loop.run_until_complete(
            gerar_resposta_web(conversation_system, mensagem, history_frontend, user_model)
        )
        loop.close()
        
        print(f"✅ Resposta: {resposta}")
        
        return jsonify({'response': resposta})
    
    except Exception as e:
        print(f"❌ ERRO: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def get_models():
    """Retorna lista de modelos disponíveis com informações detalhadas"""
    try:
        global conversation_system
        
        if conversation_system is None:
            conversation_system = bot.get_cog('ConversationSystem')
        
        if conversation_system is None:
            return jsonify({'error': 'Sistema não disponível'}), 503
        
        # ⬅️ NOVO: Retorna modelos com descrições
        models_list = []
        for idx, (model_id, config) in enumerate(conversation_system.models_config.items(), 1):
            model_info = {
                'id': idx,
                'model_id': model_id,
                'name': config['name'],
                'tokens': config['tokens']
            }
            
            # Adiciona descrições personalizadas
            if 'llama-3.1-8b' in model_id:
                model_info['description'] = 'rápido e leve'
                model_info['best_for'] = 'conversas simples, respostas rápidas'
            elif 'llama-3.3-70b' in model_id:
                model_info['description'] = 'balanceado'
                model_info['best_for'] = 'conversas gerais, código simples'
            elif 'gpt-oss-20b' in model_id:
                model_info['description'] = 'potente'
                model_info['best_for'] = 'código médio, explicações detalhadas'
            elif 'gpt-oss-120b' in model_id:
                model_info['description'] = 'modelo forte'
                model_info['best_for'] = 'código complexo, projetos completos'
            
            models_list.append(model_info)
        
        return jsonify({
            'models': models_list,
            'default': conversation_system.default_model
        })
    
    except Exception as e:
        print(f"❌ Erro ao buscar modelos: {e}")
        return jsonify({'error': str(e)}), 500

async def gerar_resposta_web(conv_system, mensagem, history, user_model=None):
    """Gera resposta usando APENAS o histórico do frontend (chat isolado)"""
    
    # Define modelo (padrão se não especificado)
    if not user_model or user_model not in conv_system.models_config:
        user_model = conv_system.default_model
    
    max_tokens = conv_system.get_model_tokens(user_model)
    
    # Monta mensagens para a API
    messages = [
        {"role": "system", "content": conv_system.personalidades["misteriosa"]}
    ]
    
    # Usa o histórico do frontend (não do backend)
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Adiciona mensagem atual
    messages.append({"role": "user", "content": mensagem})
    
    # Chama Groq API
    try:
        print(f"🔄 Chamando Groq [{conv_system.models_config[user_model]['name']}]...")
        
        response = await asyncio.to_thread(
            conv_system.groq_client.chat.completions.create,
            model=user_model,
            messages=messages,
            temperature=0.85,
            max_tokens=max_tokens,
            top_p=0.88,
            timeout=60.0  # ⬅️ TIMEOUT CONFIGURÁVEL
        )
        
        # ⬅️ VALIDAÇÃO: Verifica se resposta existe
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Resposta vazia da API")
        
        resposta = response.choices[0].message.content.strip()
        
        # ⬅️ VALIDAÇÃO: Verifica se não está vazio após strip
        if not resposta:
            raise ValueError("Conteúdo vazio após strip()")
        
        # Formata código com syntax highlight
        resposta = conv_system.formatar_codigo_discord(resposta)
        
        # Limpeza
        resposta_limpa = conv_system.limpar_resposta(resposta)
        
        # ⬅️ VALIDAÇÃO: Se limpeza deixou vazio, usa original
        if not resposta_limpa or len(resposta_limpa.strip()) == 0:
            print(f"⚠️ Resposta vazia após limpeza. Original tinha {len(resposta)} chars")
            resposta_limpa = resposta
        
        # ⬅️ GARANTIA FINAL: Nunca retorna vazio
        if not resposta_limpa or len(resposta_limpa.strip()) == 0:
            resposta_limpa = "desculpa, tive um problema ao gerar a resposta. tenta de novo?"
        
        print(f"⚡ Groq Web [{conv_system.models_config[user_model]['name']}]: {response.usage.completion_tokens} tokens")
        
        return resposta_limpa
        
    except asyncio.TimeoutError:
        print(f"⏱️ Timeout no modelo {user_model}")
        return (f"o modelo `{conv_system.models_config[user_model]['name']}` demorou demais\n\n"
               f"tenta reformular ou usar um modelo mais rápido")
    
    except Exception as e:
        print(f"❌ Erro Groq Web: {type(e).__name__}: {e}")
        
        # Erro 400 ou rate limit
        if "400" in str(e) or "rate_limit" in str(e).lower():
            return (f"o modelo tá sobrecarregado agora\n\n"
                   f"aguarda uns segundos ou usa outro modelo")
        
        # Erro genérico
        return f"erro ao gerar resposta: {e}\n\ntenta reformular a pergunta"

def run():
    """Roda o servidor Flask com Waitress"""
    port = int(os.getenv('PORT', 8080))
    print(f"🌐 Servidor web iniciado em http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port, threads=4)

def keep_alive():
    """Mantém o servidor web rodando em thread separada"""
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ====== CHECK GLOBAL ======
@bot.check
async def check_servidor_only(ctx):
    """Check global: bloqueia comandos de servidor na DM"""
    
    # Se tá em servidor, libera tudo
    if ctx.guild is not None:
        return True
    
    # Se tá na DM e comando precisa de servidor
    cmd_name = ctx.command.name
    cmd_aliases = ctx.command.aliases or []
    
    if cmd_name in COMANDOS_SERVIDOR_ONLY or any(alias in COMANDOS_SERVIDOR_ONLY for alias in cmd_aliases):
        await ctx.send("esse comando só funciona em servidor")
        return False
    
    return True

# ====== LOAD COGS ======
async def load_cogs():
    cogs = [
        "cogs.geral",           # !help
        "cogs.gens",            # Fordevs
        "cogs.status",          # Cuida do status do bot
        "cogs.utils",           # defs pra usar nas cogs
        "cogs.utilities",       # !baixar, !search
        "cogs.misc",
        "cogs.conversation",    # ⬅️ Sistema principal de conversa
        "cogs.chatcommands",
        "cogs.downloader",
        "cogs.aiactions",
        "cogs.owner",        
        "cogs.moderation",
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog}")
        except Exception as e:
            print(f"❌ {cog}: {e}")
            traceback.print_exc()

@bot.event
async def on_ready():
    global conversation_system
    print(f"🤖 Bot online como {bot.user}")
    
    # Pega referência do sistema de conversa
    conversation_system = bot.get_cog('ConversationSystem')
    if conversation_system:
        print("💬 Sistema de conversa carregado")
        print(f"📊 Modelos disponíveis: {len(conversation_system.models_config)}")
        for model_id, config in conversation_system.models_config.items():
            print(f"   • {config['name']} ({config['tokens']} tokens)")
    else:
        print("⚠️  Sistema de conversa não encontrado")

@bot.event
async def on_command_error(ctx, error):
    # Ignora erro de check (já mandou mensagem no check)
    if isinstance(error, commands.CheckFailure):
        return
    
    embed = discord.Embed(
        title="erro",
        color=0x1a1a1a
    )
    
    if isinstance(error, commands.CommandNotFound):
        embed.description = "esse comando não existe"
        embed.set_footer(text="use !help para ver os comandos")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        embed.description = f"faltou o argumento: `{error.param.name}`"
    
    elif isinstance(error, commands.BadArgument):
        embed.description = "argumento inválido"
    
    elif isinstance(error, commands.MissingPermissions):
        embed.description = "você não tem permissão"
    
    else:
        embed.description = f"`{error}`"
        embed.set_footer(text="something went wrong")
        print(f"❌ Erro não tratado: {error}")
        traceback.print_exc()
    
    await ctx.send(embed=embed, delete_after=5)

async def main():
    keep_alive() 
    await load_cogs()
    
    token = TOKEN if TOKEN else TEST_TOKEN
    if not token:
        print("❌ ERRO: Nenhum token configurado!")
        return
    
    print(f"🔑 Usando token: {'PRODUCTION' if token == TOKEN else 'TEST'}")
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())