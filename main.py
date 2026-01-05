import discord, asyncio, os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from waitress import serve

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

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
    'userinfo',       # info do usuário (pode ser usado em server/DM mas vamos manter aqui)

]

# ====== KEEP-ALIVE (WAITRESS) ======
app = Flask('')

@app.route('/')
def home():
    return "nyxie online :3"

def run():
    serve(app, host='0.0.0.0', port=8080, threads=4)

def keep_alive():
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
            import traceback
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

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
    await bot.start(TOKEN)

asyncio.run(main())