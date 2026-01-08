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
            'quote': '⛧ close the world, open the nExt',
            'ascii_name': 'fallback',
            'ascii_art': '> NYXIE.TERMINAL',
            'is_mobile': False
        })

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para conversação web"""
    try:
        global conversation_system
        
        if conversation_system is None:
            conversation_system = bot.get_cog('ConversationSystem')
        
        if conversation_system is None:
            return jsonify({'error': 'Sistema de conversa não disponível'}), 503
        
        data = request.json
        
        print(f"📩 Recebido: {data}")
        
        user_id = data.get('user_id', 'web_user')
        mensagem = data.get('message', '')
        history_frontend = data.get('history', [])
        user_model = data.get('model', None)  # ⬅️ NOVO: recebe modelo
        
        if not mensagem:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # ⬅️ NOVO: Gera resposta ISOLADA com modelo
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
    """Retorna lista de modelos disponíveis"""
    try:
        global conversation_system
        
        if conversation_system is None:
            conversation_system = bot.get_cog('ConversationSystem')
        
        if conversation_system is None:
            return jsonify({'error': 'Sistema não disponível'}), 503
        
        models = conversation_system.get_models_list()
        default = conversation_system.default_model
        
        return jsonify({
            'models': models,
            'default': default
        })
    
    except Exception as e:
        print(f"❌ Erro ao buscar modelos: {e}")
        return jsonify({'error': str(e)}), 500

async def gerar_resposta_web(conv_system, mensagem, history, user_model=None):
    """Gera resposta usando APENAS o histórico do frontend (chat isolado)"""
    
    # ⬅️ NOVO: Define modelo (padrão se não especificado)
    if not user_model or user_model not in conv_system.models_config:
        user_model = conv_system.default_model
    
    max_tokens = conv_system.get_model_tokens(user_model)
    
    # Monta mensagens para a API
    messages = [
        {"role": "system", "content": conv_system.personalidades["misteriosa"]}
    ]
    
    # ⬅️ USA O HISTÓRICO DO FRONTEND (não do backend)
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Adiciona mensagem atual
    messages.append({"role": "user", "content": mensagem})
    
    # Chama Groq API
    try:
        response = await asyncio.to_thread(
            conv_system.groq_client.chat.completions.create,
            model=user_model,  # ⬅️ MODELO DINÂMICO
            messages=messages,
            temperature=0.85,
            max_tokens=max_tokens,  # ⬅️ TOKENS DINÂMICOS
            top_p=0.88,
        )
        
        resposta = response.choices[0].message.content
        
        # Limpeza
        resposta = conv_system.limpar_resposta_cringe(resposta)
        resposta = conv_system.filtrar_emoticons_excessivos(resposta)
        
        # Remove reticências excessivas
        if resposta.count('...') > 1:
            partes = resposta.split('...')
            if len(partes) > 2:
                resposta = '. '.join(partes[:-1]) + '...' + partes[-1]
        
        # Remove "né?" duplicado
        import re
        resposta = re.sub(r',?\s*né\?.*né\?', ', né?', resposta, flags=re.IGNORECASE)
        resposta = re.sub(r'!+', '!', resposta)
        resposta = re.sub(r'né!', 'né?', resposta, flags=re.IGNORECASE)
        resposta = re.sub(r'\.\.\.\s*,', ',', resposta)
        
        return resposta
        
    except Exception as e:
        print(f"❌ Erro Groq Web: {e}")
        return f"erro: {e}"
    
def run():
    """Roda o servidor Flask com Waitress"""
    # ⬇️ MUDANÇA: Pega porta do ambiente (Render define automaticamente)
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
        "cogs.conversation",
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
    
    await ctx.send(embed=embed, delete_after=5)

async def main():
    keep_alive() 
    await load_cogs()
    await bot.start(TEST_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())