from discord.ext import commands
import discord
from datetime import datetime
import os
import hashlib

class ChatCommands(commands.Cog):
    """Comandos de chat otimizados"""
    
    # ==================== RESPOSTAS YANDERE ====================
    PERSONALITY_RESPONSES = {
        "misteriosa": "...voltando às sombras",
        "seria": "modo profissional ativado",
        "inteligente": "vamos explorar o conhecimento",
        "divertida": "bora dar risada kkkkk",
        "realista": "papo reto agora",
        "fofa": "awn, vou ser carinhosa <3",
        "cynical": "modo sarcasmo ativado",
        "yandere": "que bom... agora você é só meu :)"
    }
    
    VIBE_DESCRIPTIONS = {
        'fofo': "super fofinho! vou ser fofa também",
        'zoeira': "modo zoeira! bora rir",
        'formal': "formal, vou ser séria",
        'dark': "vibe dark... vamos filosofar",
        None: "neutro/misterioso"
    }
    
    def __init__(self, bot):
        self.bot = bot
        self._conv_sys_cache = None
        self._utils_cache = None
    
    @property
    def conv_sys(self):
        """Cache ConversationSystem"""
        if not self._conv_sys_cache:
            self._conv_sys_cache = self.bot.get_cog('ConversationSystem')
        return self._conv_sys_cache
    
    @property
    def utils(self):
        """Cache Utils"""
        if not self._utils_cache:
            self._utils_cache = self.bot.get_cog('utils')
        return self._utils_cache
    
    def _make_embed(self, title, description, **kwargs):
        """Helper pra criar embeds rapidamente"""
        return self.utils.base_embed(title, description, **kwargs)
    
    # ==================== COMANDOS DE CHAT ====================
    
    @commands.command(aliases=["iniciar", "startchat", "sc"], brief="inicia chat automático")
    async def chat(self, ctx):
        """Inicia chat automático no canal"""
        canal_id, user_id, guild_id = ctx.channel.id, ctx.author.id, ctx.guild.id
        
        # Verifica se já existe chat
        if canal_id in self.conv_sys.active_chats:
            msg = "já estamos conversando aqui" if self.conv_sys.active_chats[canal_id] == user_id else "esse canal já tem um chat ativo"
            return await ctx.send(embed=self._make_embed("chat ativo" if self.conv_sys.active_chats[canal_id] == user_id else "canal ocupado", msg))
        
        # Verifica limite de chats
        chats_ativos = self.conv_sys.get_guild_chat_count(guild_id)
        if chats_ativos >= self.conv_sys.max_chats_per_guild:
            guild_chats = self.conv_sys.get_guild_chats(guild_id)
            canais = "\n".join(f"• #{c.name} ({u.name})" 
                              for cid, uid in guild_chats 
                              if (c := self.bot.get_channel(cid)) and (u := self.bot.get_user(uid)))
            
            embed = self._make_embed(
                "limite atingido",
                f"servidor com {chats_ativos}/{self.conv_sys.max_chats_per_guild} chats ativos\n\naguarde alguém encerrar com `!stopchat`"
            )
            embed.add_field(name="chats ativos", value=canais or "nenhum", inline=False)
            return await ctx.send(embed=embed)
        
        # Inicia chat
        self.conv_sys.active_chats[canal_id] = user_id
        
        embed = self._make_embed(
            "chat iniciado",
            f"ouvindo tudo aqui, {ctx.author.name}...\n\ndigite e eu respondo automaticamente\n`!stopchat` pra parar"
        )
        embed.add_field(name="servidor", value=f"{chats_ativos + 1}/{self.conv_sys.max_chats_per_guild} chats", inline=True)
        embed.add_field(name="engine", value="Groq", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["parar", "endchat"], brief="encerra chat automático")
    async def stopchat(self, ctx):
        """Encerra chat automático"""
        canal_id, user_id = ctx.channel.id, ctx.author.id
        
        if canal_id not in self.conv_sys.active_chats:
            return await ctx.send(embed=self._make_embed("sem chat", "não tem chat ativo aqui"))
        
        if self.conv_sys.active_chats[canal_id] != user_id:
            return await ctx.send(embed=self._make_embed("não autorizado", "esse chat não é seu"))
        
        del self.conv_sys.active_chats[canal_id]
        
        conv = self.conv_sys.get_conversation(user_id)
        intensity = self.conv_sys.get_yandere_intensity(user_id)
        msg_extra = "\n*...você vai voltar, né?*" if intensity >= 5 else "\n*até a próxima*"
        
        embed = self._make_embed("chat encerrado", f"{conv['message_count']} mensagens{msg_extra}")
        await ctx.send(embed=embed)
    
    @commands.command(brief="força encerramento de chat")
    @commands.has_permissions(manage_channels=True)
    async def forcestop(self, ctx, canal: discord.TextChannel = None):
        """Força encerramento de chat em qualquer canal"""
        canal = canal or ctx.channel
        
        if canal.id not in self.conv_sys.active_chats:
            return await ctx.send(embed=self._make_embed("sem chat", f"sem chat em #{canal.name}"))
        
        user_id = self.conv_sys.active_chats.pop(canal.id)
        user = self.bot.get_user(user_id)
        
        embed = self._make_embed("chat encerrado", f"chat de {user.name if user else 'usuário'} encerrado")
        await ctx.send(embed=embed)
    
    @commands.command(brief="lista chats ativos")
    async def chats(self, ctx):
        """Lista todos os chats ativos do servidor"""
        guild_chats = self.conv_sys.get_guild_chats(ctx.guild.id)
        
        if not guild_chats:
            return await ctx.send(embed=self._make_embed("chats ativos", "nenhum chat ativo"))
        
        embed = self._make_embed("chats ativos", f"{len(guild_chats)}/{self.conv_sys.max_chats_per_guild} slots")
        
        for canal_id, user_id in guild_chats:
            canal = self.bot.get_channel(canal_id)
            user = self.bot.get_user(user_id)
            embed.add_field(
                name=f"#{canal.name if canal else 'desconhecido'}", 
                value=user.name if user else "desconhecido", 
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["conversar", "ask"], brief="mensagem avulsa")
    async def talk(self, ctx, *, mensagem=None):
        """Envia mensagem avulsa pra Nyxie"""
        if not mensagem:
            conv = self.conv_sys.get_conversation(ctx.author.id)
            embed = self._make_embed(
                "conversação com nyxie",
                "`!talk [mensagem]` ou me mencione\n`!chat` pra chat automático"
            )
            embed.add_field(name="msgs", value=str(conv['message_count']), inline=True)
            embed.add_field(name="engine", value="Groq", inline=True)
            return await ctx.send(embed=embed)
        
        async with ctx.typing():
            try:
                resposta = await self.conv_sys.gerar_resposta(ctx.author.id, mensagem)
                await ctx.send(resposta[:2000])
            except Exception as e:
                await ctx.send(f"erro: {e}")
    
    @commands.command(brief="reseta histórico")
    async def reset(self, ctx):
        """Reseta todo histórico de conversa"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.conv_sys.conversations:
            return await ctx.send(embed=self._make_embed("sem histórico", "você não conversou comigo ainda"))
        
        msg_count = self.conv_sys.conversations[user_id]['message_count']
        del self.conv_sys.conversations[user_id]
        self.conv_sys.save_conversations()
        
        # Limpa yandere e cache
        self.conv_sys.yandere_intensity.pop(user_id, None)
        
        # Cache cleanup otimizado
        hash_prefix = hashlib.md5(f"{user_id}:".encode()).hexdigest()[:8]
        self.conv_sys.response_cache = {
            k: v for k, v in self.conv_sys.response_cache.items()
            if not k.startswith(hash_prefix)
        }
        
        embed = self._make_embed("resetado", f"{msg_count} mensagens apagadas\n*mas nunca esqueço*")
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["historico"], brief="mostra histórico")
    async def history(self, ctx):
        """Mostra informações do histórico"""
        conv = self.conv_sys.get_conversation(ctx.author.id)
        started = datetime.fromisoformat(conv['started_at'])
        days = (datetime.now() - started).days
        
        intensity = self.conv_sys.get_yandere_intensity(ctx.author.id)
        current_model = conv.get('model', self.conv_sys.default_model)
        model_name = self.conv_sys.models_config[current_model]['name']
        
        embed = self._make_embed(
            f"histórico: {ctx.author.name}",
            f"personalidade: `{conv.get('personality', 'misteriosa')}`\n"
            f"modelo: `{model_name}`\n"
            f"mensagens: {conv['message_count']}\n"
            f"iniciado: <t:{int(started.timestamp())}:R>\n"
            f"dias: {days if days > 0 else 'hoje'}\n"
            f"intensidade: {'>' * min(intensity, 10)} {intensity}/10"
        )
        
        # Últimas mensagens (otimizado)
        recent = [m for m in conv['history'][-6:] if m['role'] in ('user', 'assistant')]
        if recent:
            last_msgs = "\n".join(
                f"**{'você' if m['role'] == 'user' else 'nyxie'}:** {m['content'][:50]}..."
                for m in recent
            )
            embed.add_field(name="últimas msgs", value=last_msgs or "nenhuma", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(brief="exporta histórico")
    async def export(self, ctx):
        """Exporta histórico em arquivo txt"""
        conv = self.conv_sys.get_conversation(ctx.author.id)
        
        # Geração otimizada de texto
        lines = [f"Conversa com Nyxie - {ctx.author.name}", "=" * 50, ""]
        
        for msg in conv['history'][1:]:
            if msg['role'] in ('user', 'assistant'):
                nome = "Você" if msg['role'] == 'user' else "Nyxie"
                lines.append(f"{nome}: {msg['content']}\n")
        
        filename = f"conversa_{ctx.author.id}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        embed = self._make_embed("exportado", "sua história comigo")
        await ctx.send(embed=embed, file=discord.File(filename))
        os.remove(filename)
    
    @commands.command(aliases=["persona", "mood"], brief="altera personalidade")
    async def personalidade(self, ctx, tipo: str = None):
        """Altera personalidade da Nyxie"""
        if not tipo:
            atual = self.conv_sys.get_user_personality(ctx.author.id)
            
            personas = "\n".join([
                "• `misteriosa` - dark, adaptativa (padrão)",
                "• `seria` - profissional",
                "• `inteligente` - sábia",
                "• `divertida` - engraçada",
                "• `realista` - usuária discord",
                "• `fofa` - carinhosa",
                "• `cynical` - sarcástica",
                "• `yandere` - possessiva"
            ])
            
            embed = self._make_embed(
                "personalidades",
                f"**atual:** `{atual}`\n\n**disponíveis:**\n{personas}\n\n`!personalidade [tipo]`"
            )
            embed.add_field(name="nota", value="não apaga histórico", inline=False)
            return await ctx.send(embed=embed)
        
        tipo = tipo.lower()
        
        if tipo not in self.conv_sys.personalidades:
            opcoes = ', '.join(f'`{p}`' for p in self.conv_sys.personalidades.keys())
            return await ctx.send(embed=self._make_embed("inválida", f"escolha: {opcoes}"))
        
        antiga = self.conv_sys.get_user_personality(ctx.author.id)
        self.conv_sys.set_user_personality(ctx.author.id, tipo)
        
        # Reseta yandere se mudar de personalidade
        if tipo != "yandere":
            self.conv_sys.yandere_intensity.pop(str(ctx.author.id), None)
        
        resposta = self.PERSONALITY_RESPONSES.get(tipo, '...')
        embed = self._make_embed("alterada", f"`{antiga}` → `{tipo}`\n\n{resposta}")
        await ctx.send(embed=embed)
    
    @commands.command(brief="mostra vibe detectada")
    async def vibe(self, ctx):
        """Mostra vibe detectada das mensagens"""
        personality = self.conv_sys.get_user_personality(ctx.author.id)
        
        if personality != "misteriosa":
            return await ctx.send(embed=self._make_embed(
                "vibe check", 
                f"você usa `{personality}` (fixa)\ndetecção só funciona em `misteriosa`"
            ))
        
        vibe = self.conv_sys.detectar_vibe(ctx.author.id)
        intensity = self.conv_sys.get_yandere_intensity(ctx.author.id)
        
        description = f"**detectado:** {vibe or 'neutro'}\n{self.VIBE_DESCRIPTIONS.get(vibe, '...')}"
        
        if intensity > 0:
            description += f"\n\n**intensidade yandere:** {'>' * intensity} {intensity}/10"
            if intensity >= 8:
                description += "\n*...você é tão especial pra mim...*"
            elif intensity >= 5:
                description += "\n*gosto quando você tá aqui :)*"
        
        description += "\n\n*me adapto ao seu jeito*"
        
        embed = self._make_embed("vibe check", description)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["modelo", "ai"], brief="gerencia modelos de IA")
    async def model(self, ctx, escolha: str = None):
        """Seleciona modelo de IA"""
        if not escolha:
            current_model = self.conv_sys.get_user_model(ctx.author.id)
            current_name = self.conv_sys.models_config[current_model]['name']
            
            lista = [f"**modelo atual:** `{current_name}`\n\n**disponíveis:**\n"]
            
            for model in self.conv_sys.get_models_list():
                marker = "→" if self.conv_sys.get_user_model(ctx.author.id) == model['model_id'] else " "
                lista.append(f"{marker} **{model['id']}.** `{model['name']}`")
                lista.append(f"   {model['tokens']} tokens\n")
            
            lista.append("\n`!model [1-4]` para selecionar")
            
            return await ctx.send(embed=self._make_embed("modelos de ia", "\n".join(lista)))
        
        # Seleciona modelo
        if escolha.isdigit():
            escolha_num = int(escolha)
            if not 1 <= escolha_num <= 4:
                return await ctx.send(embed=self._make_embed("inválido", "escolha entre 1-4"))
            model_id = list(self.conv_sys.models_config.keys())[escolha_num - 1]
        elif escolha in self.conv_sys.models_config:
            model_id = escolha
        else:
            return await ctx.send(embed=self._make_embed("inválido", "use !model para ver opções"))
        
        self.conv_sys.set_user_model(ctx.author.id, model_id)
        config = self.conv_sys.models_config[model_id]
        
        embed = self._make_embed(
            "modelo alterado",
            f"**{config['name']}**\ntokens: {config['tokens']}\n"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChatCommands(bot))