import discord
from discord.ext import commands
import subprocess
import sys
import os
import traceback
import io
import contextlib
import textwrap
import json
from datetime import datetime

class Owner(commands.Cog):
    """Comandos exclusivos do dono do bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_file = "blacklist.json"
        self.prefix_file = "prefixes.json"
        self.logs = []  # Armazena últimos 50 logs
        self.max_logs = 50
        
        # Carrega blacklist
        self.blacklist = self.load_json(self.blacklist_file, {"users": [], "guilds": []})
        
        # Carrega prefixes customizados
        self.prefixes = self.load_json(self.prefix_file, {})
    
    def load_json(self, file, default=None):
        """Carrega JSON ou retorna padrão"""
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default or {}
    
    def save_json(self, file, data):
        """Salva JSON"""
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_log(self, message):
        """Adiciona log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        print(log_entry)
    
    async def cog_check(self, ctx):
        """Só o dono pode usar comandos desta cog"""
        return await self.bot.is_owner(ctx.author)
    
    # ==================== EVAL ====================
    
    @commands.command(brief="executa código python (owner only)")
    async def eval(self, ctx, *, code: str):
        """executa código python
        
        uso: !eval (código)
        exemplo: !eval 2 + 2
        exemplo: !eval await ctx.send("oi")
        exemplo: !eval len(self.bot.guilds)
        """
        # Remove ```python se tiver
        code = code.strip('`')
        if code.startswith('python\n'):
            code = code[7:]
        
        # Prepara ambiente
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'discord': discord,
            'commands': commands,
        }
        
        # Captura stdout
        stdout = io.StringIO()
        
        # Prepara código
        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'
        
        try:
            exec(to_compile, env)
            
            func = env['func']
            with contextlib.redirect_stdout(stdout):
                ret = await func()
            
            value = stdout.getvalue()
            
            # Formata resultado
            if ret is None:
                if value:
                    result = f'```\n{value}\n```'
                else:
                    result = 'executado sem retorno'
            else:
                result = f'```py\n{value}{ret}\n```'
            
            # Limita tamanho
            if len(result) > 2000:
                result = result[:1997] + '...'
            
            await ctx.send(result)
            self.add_log(f"EVAL executado por {ctx.author}: {code[:50]}")
            
        except Exception as e:
            error = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await ctx.send(f'```py\n{error}\n```'[:2000])
            self.add_log(f"EVAL erro: {str(e)}")
    
    @commands.command(brief="mostra últimos logs do bot (owner only)")
    async def logs(self, ctx, quantidade: int = 20):
        """mostra os últimos logs do bot
        
        uso: !logs [quantidade]
        exemplo: !logs
        exemplo: !logs 50
        """
        if quantidade < 1 or quantidade > self.max_logs:
            quantidade = 20
        
        recent_logs = self.logs[-quantidade:]
        
        if not recent_logs:
            await ctx.send("```\nNenhum log ainda\n```")
            return
        
        log_text = '\n'.join(recent_logs)
        
        if len(log_text) > 1990:
            # Envia como arquivo se for muito grande
            with open('logs_temp.txt', 'w', encoding='utf-8') as f:
                f.write(log_text)
            
            await ctx.send(file=discord.File('logs_temp.txt'))
            os.remove('logs_temp.txt')
        else:
            await ctx.send(f'```\n{log_text}\n```')
    
    # ==================== RESTART ====================
    
    @commands.command(brief="reinicia o bot (owner only)")
    async def restart(self, ctx):
        """reinicia o bot completamente
        
        uso: !restart
        exemplo: !restart
        """
        await ctx.send("reiniciando...")
        self.add_log(f"Bot reiniciado por {ctx.author}")
        
        # Salva tudo antes de reiniciar
        for cog in self.bot.cogs.values():
            if hasattr(cog, 'save_conversations'):
                cog.save_conversations()
        
        # Restart
        os.execv(sys.executable, ['python'] + sys.argv)
    
    # ==================== UPDATE ====================
    
    @commands.command(brief="atualiza código do github (owner only)")
    async def update(self, ctx):
        """faz git pull e reinicia o bot
        
        uso: !update
        exemplo: !update
        """
        await ctx.send("atualizando código...")
        
        try:
            # Git pull
            result = subprocess.run(
                ['git', 'pull'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                if 'Already up to date' in output:
                    await ctx.send("já está atualizado")
                else:
                    await ctx.send(f"atualizado!\n```\n{output[:1900]}\n```\n🔄 reiniciando...")
                    self.add_log(f"Bot atualizado por {ctx.author}")
                    os.execv(sys.executable, ['python'] + sys.argv)
            else:
                await ctx.send(f"erro ao atualizar:\n```\n{output[:1900]}\n```")
                
        except subprocess.TimeoutExpired:
            await ctx.send("timeout ao fazer git pull")
        except FileNotFoundError:
            await ctx.send("git não está instalado ou não está no PATH")
        except Exception as e:
            await ctx.send(f"erro: `{str(e)}`")
    
    # ==================== BROADCAST ====================
    
    @commands.command(brief="anuncia em todos os servidores (owner only)")
    async def broadcast(self, ctx, *, mensagem: str):
        """envia anúncio em todos os servidores
        
        uso: !broadcast (mensagem)
        exemplo: !broadcast Bot atualizado! Novos comandos disponíveis.
        """
        await ctx.send(f"enviando pra {len(self.bot.guilds)} servidores...")
        
        enviados = 0
        falhas = 0
        
        embed = discord.Embed(
            title="anúncio do dono",
            description=mensagem,
            color=0x1a1a1a,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"enviado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        for guild in self.bot.guilds:
            try:
                # Tenta enviar no canal de sistema ou primeiro canal de texto
                channel = guild.system_channel or guild.text_channels[0]
                
                await channel.send(embed=embed)
                enviados += 1
                
            except discord.Forbidden:
                falhas += 1
            except Exception as e:
                falhas += 1
                self.add_log(f"Erro broadcast em {guild.name}: {e}")
        
        await ctx.send(f"✅ enviado: {enviados}\n❌ falhas: {falhas}")
        self.add_log(f"Broadcast enviado por {ctx.author}: {enviados}/{len(self.bot.guilds)}")
    
    # ==================== BLACKLIST ====================
    
    @commands.command(brief="bloqueia user/servidor (owner only)")
    async def blacklist(self, ctx, tipo: str, id: int, *, motivo: str = "sem motivo"):
        """adiciona user ou servidor à blacklist
        
        uso: !blacklist (user/guild) (id) [motivo]
        exemplo: !blacklist user 123456789 spam
        exemplo: !blacklist guild 987654321 raid
        """
        tipo = tipo.lower()
        
        if tipo not in ['user', 'guild']:
            await ctx.send("❌ tipo inválido. use `user` ou `guild`")
            return
        
        key = 'users' if tipo == 'user' else 'guilds'
        
        # Verifica se já está na blacklist
        for entry in self.blacklist[key]:
            if entry['id'] == id:
                await ctx.send(f"❌ já está na blacklist desde {entry['added_at']}")
                return
        
        # Adiciona
        self.blacklist[key].append({
            'id': id,
            'reason': motivo,
            'added_by': ctx.author.id,
            'added_at': datetime.utcnow().isoformat()
        })
        
        self.save_json(self.blacklist_file, self.blacklist)
        
        await ctx.send(f"{tipo} `{id}` adicionado à blacklist\nmotivo: {motivo}")
        self.add_log(f"Blacklist: {tipo} {id} por {ctx.author}")
        
        # Se for servidor, sai dele
        if tipo == 'guild':
            guild = self.bot.get_guild(id)
            if guild:
                try:
                    await guild.leave()
                    await ctx.send(f"saí do servidor `{guild.name}`")
                except:
                    pass
    
    @commands.command(brief="remove da blacklist (owner only)")
    async def unblacklist(self, ctx, tipo: str, id: int):
        """remove user ou servidor da blacklist
        
        uso: !unblacklist (user/guild) (id)
        exemplo: !unblacklist user 123456789
        exemplo: !unblacklist guild 987654321
        """
        tipo = tipo.lower()
        
        if tipo not in ['user', 'guild']:
            await ctx.send("❌ tipo inválido. use `user` ou `guild`")
            return
        
        key = 'users' if tipo == 'user' else 'guilds'
        
        # Remove
        original_len = len(self.blacklist[key])
        self.blacklist[key] = [e for e in self.blacklist[key] if e['id'] != id]
        
        if len(self.blacklist[key]) == original_len:
            await ctx.send(f"{tipo} `{id}` não está na blacklist")
            return
        
        self.save_json(self.blacklist_file, self.blacklist)
        
        await ctx.send(f"{tipo} `{id}` removido da blacklist")
        self.add_log(f"Unblacklist: {tipo} {id} por {ctx.author}")
    
    @commands.command(brief="lista blacklist (owner only)")
    async def blacklisted(self, ctx):
        """mostra todos bloqueados
        
        uso: !blacklisted
        exemplo: !blacklisted
        """
        embed = discord.Embed(title="blacklist", color=0x1a1a1a)
        
        # Users
        if self.blacklist['users']:
            users_text = '\n'.join([
                f"`{e['id']}` - {e['reason']}"
                for e in self.blacklist['users']
            ])
            embed.add_field(name="usuários", value=users_text[:1024], inline=False)
        
        # Guilds
        if self.blacklist['guilds']:
            guilds_text = '\n'.join([
                f"`{e['id']}` - {e['reason']}"
                for e in self.blacklist['guilds']
            ])
            embed.add_field(name="servidores", value=guilds_text[:1024], inline=False)
        
        if not self.blacklist['users'] and not self.blacklist['guilds']:
            embed.description = "nenhum bloqueio ativo"
        
        await ctx.send(embed=embed)
    
    # ==================== PREFIX CUSTOMIZADO ====================
    
    @commands.command(brief="muda prefix do servidor (owner only)")
    async def setprefix(self, ctx, prefix: str):
        """define prefix customizado pra um servidor
        
        uso: !setprefix (prefix)
        exemplo: !setprefix ?
        exemplo: !setprefix nyxie!
        """
        if not ctx.guild:
            await ctx.send("só funciona em servidor")
            return
        
        if len(prefix) > 5:
            await ctx.send("prefix muito longo (máx 5 caracteres)")
            return
        
        self.prefixes[str(ctx.guild.id)] = prefix
        self.save_json(self.prefix_file, self.prefixes)
        
        await ctx.send(f"prefix alterado para `{prefix}`")
        self.add_log(f"Prefix alterado em {ctx.guild.name}: {prefix}")
    
    @commands.command(brief="reseta prefix (owner only)")
    async def resetprefix(self, ctx):
        """volta pro prefix padrão
        
        uso: !resetprefix
        exemplo: !resetprefix
        """
        if not ctx.guild:
            await ctx.send("só funciona em servidor")
            return
        
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.prefixes:
            del self.prefixes[guild_id]
            self.save_json(self.prefix_file, self.prefixes)
            await ctx.send("prefix resetado para `!`")
        else:
            await ctx.send("servidor já usa prefix padrão")
    
    # ==================== EVENTOS ====================
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Bloqueia usuários/servidores da blacklist"""
        if message.author.bot:
            return
        
        # Bloqueia usuário
        if message.author.id in [e['id'] for e in self.blacklist['users']]:
            return
        
        # Bloqueia servidor
        if message.guild and message.guild.id in [e['id'] for e in self.blacklist['guilds']]:
            return
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sai de servidores na blacklist"""
        if guild.id in [e['id'] for e in self.blacklist['guilds']]:
            self.add_log(f"Saindo de servidor blacklistado: {guild.name}")
            await guild.leave()

async def setup(bot):
    await bot.add_cog(Owner(bot))