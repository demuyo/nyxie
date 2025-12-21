# moderation.py
import discord
from discord.ext import commands
from datetime import timedelta
import asyncio
import json
import os
from datetime import datetime

class Moderation(commands.Cog):
    """Sistema completo de moderação"""
    
    def __init__(self, bot):
        self.bot = bot
        self.warns_file = "warns.json"
        self.mutes_file = "mutes.json"
        self.load_data()
    
    def load_data(self):
        """Carrega warns e mutes"""
        if os.path.exists(self.warns_file):
            with open(self.warns_file, 'r', encoding='utf-8') as f:
                self.warns = json.load(f)
        else:
            self.warns = {}
        
        if os.path.exists(self.mutes_file):
            with open(self.mutes_file, 'r', encoding='utf-8') as f:
                self.mutes = json.load(f)
        else:
            self.mutes = {}
    
    def save_warns(self):
        """Salva warns"""
        with open(self.warns_file, 'w', encoding='utf-8') as f:
            json.dump(self.warns, f, indent=2, ensure_ascii=False)
    
    def save_mutes(self):
        """Salva mutes"""
        with open(self.mutes_file, 'w', encoding='utf-8') as f:
            json.dump(self.mutes, f, indent=2, ensure_ascii=False)
    
    # ==================== MEMBROS ====================
    
    @commands.command(brief="expulsa um membro do servidor")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "sem motivo"):
        """expulsa um membro do servidor
        
        uso: kick (user) [motivo]
        
        exemplos:
        - kick @joão fazendo spam no chat
        - kick @maria comportamento inadequado
        """
        utils = self.bot.get_cog('utils')
        
        if member.top_role >= ctx.author.top_role:
            embed = utils.base_embed("sem permissão", "você não pode kickar alguém com cargo igual ou superior")
            return await ctx.send(embed=embed)
        
        if member.top_role >= ctx.guild.me.top_role:
            embed = utils.base_embed("sem permissão", "não posso kickar alguém com cargo superior ao meu")
            return await ctx.send(embed=embed)
        
        try:
            # DM pro usuário
            try:
                dm_embed = utils.base_embed("você foi expulso", None)
                dm_embed.add_field(name="servidor", value=ctx.guild.name, inline=False)
                dm_embed.add_field(name="moderador", value=ctx.author.name, inline=True)
                dm_embed.add_field(name="motivo", value=reason, inline=True)
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.kick(reason=f"{ctx.author} | {reason}")
            
            embed = utils.base_embed("membro expulso", None)
            embed.add_field(name="usuário", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="motivo", value=reason, inline=True)
            embed.set_footer(text=f"por {ctx.author.name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"não consegui expulsar: `{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="bane um membro permanentemente")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "sem motivo"):
        """bane um membro permanentemente do servidor
        
        uso: ban (user) [motivo]
        
        exemplos:
        - ban @joão raid no servidor
        - ban @maria múltiplas infrações
        """
        utils = self.bot.get_cog('utils')
        
        if member.top_role >= ctx.author.top_role:
            embed = utils.base_embed("sem permissão", "você não pode banir alguém com cargo igual ou superior")
            return await ctx.send(embed=embed)
        
        if member.top_role >= ctx.guild.me.top_role:
            embed = utils.base_embed("sem permissão", "não posso banir alguém com cargo superior ao meu")
            return await ctx.send(embed=embed)
        
        try:
            # DM pro usuário
            try:
                dm_embed = utils.base_embed("você foi banido", None)
                dm_embed.add_field(name="servidor", value=ctx.guild.name, inline=False)
                dm_embed.add_field(name="moderador", value=ctx.author.name, inline=True)
                dm_embed.add_field(name="motivo", value=reason, inline=True)
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.ban(reason=f"{ctx.author} | {reason}", delete_message_days=1)
            
            embed = utils.base_embed("membro banido", None)
            embed.add_field(name="usuário", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="motivo", value=reason, inline=True)
            embed.set_footer(text=f"por {ctx.author.name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"não consegui banir: `{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="desbane um usuário pelo id")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "sem motivo"):
        """desbane um usuário usando o id
        
        uso: unban (id) [motivo]
        
        exemplos:
        - unban 123456789012345678 apelo aceito
        - unban 987654321098765432
        """
        utils = self.bot.get_cog('utils')
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author} | {reason}")
            
            embed = utils.base_embed("usuário desbanido", None)
            embed.add_field(name="usuário", value=f"{user.name} (`{user.id}`)", inline=False)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="motivo", value=reason, inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            embed = utils.base_embed("erro", "usuário não está banido")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="lista usuários banidos")
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        """lista usuários banidos do servidor
        
        uso: banlist
        
        exemplos:
        - banlist
        """
        utils = self.bot.get_cog('utils')
        
        bans = [entry async for entry in ctx.guild.bans(limit=20)]
        
        if not bans:
            embed = utils.base_embed("banimentos", "ninguém banido")
            return await ctx.send(embed=embed)
        
        embed = utils.base_embed("banimentos", f"total: {len(bans)}")
        
        for i, ban_entry in enumerate(bans[:10], 1):
            user = ban_entry.user
            reason = ban_entry.reason or "sem motivo"
            embed.add_field(
                name=f"{i}. {user.name}",
                value=f"`{user.id}`\nmotivo: {reason[:50]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(brief="dá timeout em um membro")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duracao: int, unidade: str = "m", *, reason: str = "sem motivo"):
        """dá timeout em um membro por tempo determinado
        
        uso: timeout (user) (tempo) [s/m/h/d] [motivo]
        
        exemplos:
        - timeout @joão 10 m flood no chat
        - timeout @maria 2 h comportamento inadequado
        - timeout @pedro 1 d spam repetitivo
        """
        utils = self.bot.get_cog('utils')
        
        if member.top_role >= ctx.author.top_role:
            embed = utils.base_embed("sem permissão", "você não pode dar timeout em alguém com cargo igual ou superior")
            return await ctx.send(embed=embed)
        
        # Converte pra segundos
        unidades = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        if unidade not in unidades:
            embed = utils.base_embed("erro", "unidade inválida\nuse: s, m, h, d")
            return await ctx.send(embed=embed)
        
        segundos = duracao * unidades[unidade]
        
        if segundos > 2419200:  # 28 dias
            embed = utils.base_embed("erro", "máximo: 28 dias")
            return await ctx.send(embed=embed)
        
        try:
            timeout_ate = discord.utils.utcnow() + timedelta(seconds=segundos)
            await member.timeout(timeout_ate, reason=f"{ctx.author} | {reason}")
            
            # Formata duração
            if unidade == 's':
                duracao_str = f"{duracao} segundo(s)"
            elif unidade == 'm':
                duracao_str = f"{duracao} minuto(s)"
            elif unidade == 'h':
                duracao_str = f"{duracao} hora(s)"
            else:
                duracao_str = f"{duracao} dia(s)"
            
            embed = utils.base_embed("timeout aplicado", None)
            embed.add_field(name="usuário", value=member.mention, inline=False)
            embed.add_field(name="duração", value=duracao_str, inline=True)
            embed.add_field(name="motivo", value=reason, inline=True)
            embed.add_field(name="termina", value=f"<t:{int(timeout_ate.timestamp())}:R>", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["untimeout"], brief="remove timeout de um membro")
    @commands.has_permissions(moderate_members=True)
    async def removetimeout(self, ctx, member: discord.Member):
        """remove timeout de um membro
        
        uso: removetimeout (user)
        
        exemplos:
        - removetimeout @joão
        - untimeout @maria
        """
        utils = self.bot.get_cog('utils')
        
        try:
            await member.timeout(None)
            
            embed = utils.base_embed("timeout removido", None)
            embed.add_field(name="usuário", value=member.mention, inline=True)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    # ==================== WARNS ====================
    
    @commands.command(brief="adiciona um aviso a um membro")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "sem motivo"):
        """adiciona um aviso a um membro
        
        uso: warn (user) [motivo]
        
        exemplos:
        - warn @joão desrespeito no chat
        - warn @maria linguagem inadequada
        """
        utils = self.bot.get_cog('utils')
        
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warns:
            self.warns[guild_id] = {}
        
        if user_id not in self.warns[guild_id]:
            self.warns[guild_id][user_id] = []
        
        warn_data = {
            'moderador': str(ctx.author.id),
            'motivo': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.warns[guild_id][user_id].append(warn_data)
        self.save_warns()
        
        total_warns = len(self.warns[guild_id][user_id])
        
        # DM pro usuário
        try:
            dm_embed = utils.base_embed("você recebeu um aviso", None)
            dm_embed.add_field(name="servidor", value=ctx.guild.name, inline=False)
            dm_embed.add_field(name="moderador", value=ctx.author.name, inline=True)
            dm_embed.add_field(name="motivo", value=reason, inline=True)
            dm_embed.add_field(name="total de avisos", value=total_warns, inline=False)
            await member.send(embed=dm_embed)
        except:
            pass
        
        embed = utils.base_embed("aviso aplicado", None)
        embed.add_field(name="usuário", value=member.mention, inline=False)
        embed.add_field(name="motivo", value=reason, inline=True)
        embed.add_field(name="total", value=f"`{total_warns}` aviso(s)", inline=True)
        embed.set_footer(text=f"por {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["avisos"], brief="mostra avisos de um membro")
    @commands.has_permissions(moderate_members=True)
    async def warns(self, ctx, member: discord.Member):
        """mostra todos os avisos de um membro
        
        uso: warns (user)
        
        exemplos:
        - warns @joão
        - avisos @maria
        """
        utils = self.bot.get_cog('utils')
        
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warns or user_id not in self.warns[guild_id]:
            embed = utils.base_embed("avisos", f"{member.name} não tem avisos")
            return await ctx.send(embed=embed)
        
        user_warns = self.warns[guild_id][user_id]
        
        embed = utils.base_embed(f"avisos: {member.name}", f"total: {len(user_warns)}")
        
        for i, warn in enumerate(reversed(user_warns[-5:]), 1):
            moderador = ctx.guild.get_member(int(warn['moderador']))
            mod_name = moderador.name if moderador else "desconhecido"
            
            timestamp = datetime.fromisoformat(warn['timestamp'])
            
            embed.add_field(
                name=f"{i}. {warn['motivo'][:50]}",
                value=f"moderador: {mod_name}\n<t:{int(timestamp.timestamp())}:R>",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["limparavisos"], brief="limpa todos os avisos de um membro")
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """limpa todos os avisos de um membro
        
        uso: clearwarns (user)
        
        exemplos:
        - clearwarns @joão
        - limparavisos @maria
        """
        utils = self.bot.get_cog('utils')
        
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.warns and user_id in self.warns[guild_id]:
            total = len(self.warns[guild_id][user_id])
            del self.warns[guild_id][user_id]
            self.save_warns()
            
            embed = utils.base_embed("avisos limpos", None)
            embed.add_field(name="usuário", value=member.mention, inline=True)
            embed.add_field(name="removidos", value=f"`{total}` aviso(s)", inline=True)
            
            await ctx.send(embed=embed)
        else:
            embed = utils.base_embed("avisos", f"{member.name} não tem avisos")
            await ctx.send(embed=embed)
    
    # ==================== CARGOS ====================
    
    @commands.command(aliases=["addrole"], brief="adiciona um cargo a um membro")
    @commands.has_permissions(manage_roles=True)
    async def giverole(self, ctx, member: discord.Member, *, role: discord.Role):
        """adiciona um cargo a um membro
        
        uso: giverole (user) (cargo)
        
        exemplos:
        - giverole @joão @moderador
        - addrole @maria @vip
        """
        utils = self.bot.get_cog('utils')
        
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = utils.base_embed("sem permissão", "você não pode dar um cargo igual ou superior ao seu")
            return await ctx.send(embed=embed)
        
        if role >= ctx.guild.me.top_role:
            embed = utils.base_embed("sem permissão", "não posso dar um cargo superior ao meu")
            return await ctx.send(embed=embed)
        
        if role in member.roles:
            embed = utils.base_embed("erro", f"{member.mention} já tem esse cargo")
            return await ctx.send(embed=embed)
        
        try:
            await member.add_roles(role, reason=f"{ctx.author} | comando giverole")
            
            embed = utils.base_embed("cargo adicionado", None)
            embed.add_field(name="usuário", value=member.mention, inline=True)
            embed.add_field(name="cargo", value=role.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["removerole"], brief="remove um cargo de um membro")
    @commands.has_permissions(manage_roles=True)
    async def takerole(self, ctx, member: discord.Member, *, role: discord.Role):
        """remove um cargo de um membro
        
        uso: takerole (user) (cargo)
        
        exemplos:
        - takerole @joão @moderador
        - removerole @maria @vip
        """
        utils = self.bot.get_cog('utils')
        
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = utils.base_embed("sem permissão", "você não pode remover um cargo igual ou superior ao seu")
            return await ctx.send(embed=embed)
        
        if role >= ctx.guild.me.top_role:
            embed = utils.base_embed("sem permissão", "não posso remover um cargo superior ao meu")
            return await ctx.send(embed=embed)
        
        if role not in member.roles:
            embed = utils.base_embed("erro", f"{member.mention} não tem esse cargo")
            return await ctx.send(embed=embed)
        
        try:
            await member.remove_roles(role, reason=f"{ctx.author} | comando takerole")
            
            embed = utils.base_embed("cargo removido", None)
            embed.add_field(name="usuário", value=member.mention, inline=True)
            embed.add_field(name="cargo", value=role.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["cargos"], brief="lista todos os cargos do servidor")
    @commands.has_permissions(manage_roles=True)
    async def roles(self, ctx):
        """lista todos os cargos do servidor
        
        uso: roles
        
        exemplos:
        - roles
        - cargos
        """
        utils = self.bot.get_cog('utils')
        
        roles = sorted(ctx.guild.roles[1:], key=lambda r: r.position, reverse=True)[:20]
        
        embed = utils.base_embed("cargos", f"total: {len(ctx.guild.roles)-1}")
        
        lista = "\n".join([f"{r.mention} - `{len(r.members)}` membros" for r in roles])
        embed.add_field(name="cargos principais", value=lista or "nenhum", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(brief="cria um novo cargo no servidor")
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, *, nome: str):
        """cria um novo cargo no servidor
        
        uso: createrole (nome)
        
        exemplos:
        - createrole moderador
        - createrole vip premium
        """
        utils = self.bot.get_cog('utils')
        
        try:
            role = await ctx.guild.create_role(name=nome, reason=f"{ctx.author} | comando createrole")
            
            embed = utils.base_embed("cargo criado", None)
            embed.add_field(name="nome", value=role.mention, inline=True)
            embed.add_field(name="id", value=f"`{role.id}`", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    

    ##############

    @commands.command(brief="deleta um cargo do servidor")
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx, *, role: discord.Role):
        """deleta um cargo do servidor (pede confirmação)
        
        uso: !deleterole (cargo)
        exemplo: !deleterole @Moderador
        exemplo: !deleterole @VIP
        """
        utils = self.bot.get_cog('utils')
        
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = utils.base_embed("sem permissão", "você não pode deletar um cargo igual ou superior ao seu")
            return await ctx.send(embed=embed)
        
        if role >= ctx.guild.me.top_role:
            embed = utils.base_embed("sem permissão", "não posso deletar um cargo superior ao meu")
            return await ctx.send(embed=embed)
        
        await ctx.send(f"⚠️ deletar **{role.name}**? digite `sim` em 10s")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'sim'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
            
            nome = role.name
            await role.delete(reason=f"{ctx.author} | comando deleterole")
            
            embed = utils.base_embed("cargo deletado", None)
            embed.add_field(name="nome", value=f"`{nome}`", inline=True)
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("❌ cancelado")
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    # ==================== CANAIS ====================
    
    @commands.command(aliases=["cc"], brief="cria um novo canal no servidor")
    @commands.has_permissions(manage_channels=True)
    async def createchannel(self, ctx, tipo: str, *, nome: str):
        """cria um novo canal no servidor
        
        uso: !createchannel (tipo) (nome)
        exemplo: !createchannel text geral
        exemplo: !createchannel voice Música
        exemplo: !createchannel stage Palco Principal
        """
        utils = self.bot.get_cog('utils')
        
        tipos = {
            'text': discord.ChannelType.text,
            'voice': discord.ChannelType.voice,
            'stage': discord.ChannelType.stage_voice,
            'forum': discord.ChannelType.forum
        }
        
        if tipo not in tipos:
            embed = utils.base_embed("erro", f"tipos válidos: `{', '.join(tipos.keys())}`")
            return await ctx.send(embed=embed)
        
        try:
            channel = await ctx.guild.create_text_channel(
                name=nome,
                reason=f"{ctx.author} | comando createchannel"
            ) if tipo == 'text' else await ctx.guild.create_voice_channel(
                name=nome,
                reason=f"{ctx.author} | comando createchannel"
            )
            
            embed = utils.base_embed("canal criado", None)
            embed.add_field(name="nome", value=channel.mention if tipo == 'text' else f"`{nome}`", inline=True)
            embed.add_field(name="tipo", value=tipo, inline=True)
            embed.add_field(name="id", value=f"`{channel.id}`", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["dc"], brief="deleta um canal")
    @commands.has_permissions(manage_channels=True)
    async def deletechannel(self, ctx, channel: discord.TextChannel = None):
        """deleta um canal (pede confirmação)
        
        uso: !deletechannel [canal]
        exemplo: !deletechannel #spam
        exemplo: !deletechannel (deleta o canal atual)
        """
        utils = self.bot.get_cog('utils')
        
        channel = channel or ctx.channel
        
        await ctx.send(f"⚠️ deletar {channel.mention}? digite `sim` em 10s")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'sim'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
            
            nome = channel.name
            
            if channel == ctx.channel:
                await ctx.send("✅ deletando canal...")
                await asyncio.sleep(1)
            
            await channel.delete(reason=f"{ctx.author} | comando deletechannel")
            
            if channel != ctx.channel:
                embed = utils.base_embed("canal deletado", None)
                embed.add_field(name="nome", value=f"`{nome}`", inline=True)
                await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("❌ cancelado")
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="cria uma nova categoria")
    @commands.has_permissions(manage_channels=True)
    async def createcategory(self, ctx, *, nome: str):
        """cria uma nova categoria
        
        uso: !createcategory (nome)
        exemplo: !createcategory Moderação
        exemplo: !createcategory Canais VIP
        """
        utils = self.bot.get_cog('utils')
        
        try:
            category = await ctx.guild.create_category(
                name=nome,
                reason=f"{ctx.author} | comando createcategory"
            )
            
            embed = utils.base_embed("categoria criada", None)
            embed.add_field(name="nome", value=f"`{nome}`", inline=True)
            embed.add_field(name="id", value=f"`{category.id}`", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="bloqueia um canal")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """bloqueia um canal (ninguém pode enviar mensagens)
        
        uso: !lock [canal]
        exemplo: !lock #geral
        exemplo: !lock (bloqueia o canal atual)
        """
        utils = self.bot.get_cog('utils')
        
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=False,
                reason=f"{ctx.author} | comando lock"
            )
            
            embed = utils.base_embed("canal bloqueado", None)
            embed.add_field(name="canal", value=channel.mention, inline=True)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="desbloqueia um canal")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """desbloqueia um canal
        
        uso: !unlock [canal]
        exemplo: !unlock #geral
        exemplo: !unlock (desbloqueia o canal atual)
        """
        utils = self.bot.get_cog('utils')
        
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                send_messages=None,
                reason=f"{ctx.author} | comando unlock"
            )
            
            embed = utils.base_embed("canal desbloqueado", None)
            embed.add_field(name="canal", value=channel.mention, inline=True)
            embed.add_field(name="moderador", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    # ==================== MENSAGENS ====================
    
    @commands.command(aliases=["limpar"], brief="limpa mensagens do canal")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, quantidade: int):
        """limpa mensagens do canal
        
        uso: !clear (quantidade)
        exemplo: !clear 10
        exemplo: !clear 50
        exemplo: !clear 100
        """
        utils = self.bot.get_cog('utils')
        
        if quantidade < 1 or quantidade > 100:
            embed = utils.base_embed("erro", "quantidade entre 1 e 100")
            return await ctx.send(embed=embed)
        
        try:
            deleted = await ctx.channel.purge(limit=quantidade + 1)
            
            embed = utils.base_embed("mensagens limpas", None)
            embed.add_field(name="quantidade", value=f"`{len(deleted)-1}` mensagens", inline=True)
            embed.add_field(name="canal", value=ctx.channel.mention, inline=True)
            
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="define slowmode em um canal")
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, segundos: int, channel: discord.TextChannel = None):
        """define slowmode em um canal
        
        uso: !slowmode (segundos) [canal]
        exemplo: !slowmode 10
        exemplo: !slowmode 30 #geral
        exemplo: !slowmode 0 (desativa slowmode)
        """
        utils = self.bot.get_cog('utils')
        
        channel = channel or ctx.channel
        
        if segundos < 0 or segundos > 21600:
            embed = utils.base_embed("erro", "slowmode entre 0 e 21600 segundos (6h)")
            return await ctx.send(embed=embed)
        
        try:
            await channel.edit(slowmode_delay=segundos, reason=f"{ctx.author} | comando slowmode")
            
            if segundos == 0:
                embed = utils.base_embed("slowmode desativado", None)
            else:
                embed = utils.base_embed("slowmode ativado", None)
                embed.add_field(name="delay", value=f"`{segundos}` segundo(s)", inline=True)
            
            embed.add_field(name="canal", value=channel.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    # ==================== INFORMAÇÕES ====================
    
    @commands.command(brief="mostra informações do servidor")
    @commands.has_permissions(moderate_members=True)
    async def serverinfo(self, ctx):
        """mostra informações completas do servidor
        
        uso: !serverinfo
        exemplo: !serverinfo
        """
        utils = self.bot.get_cog('utils')
        
        guild = ctx.guild
        
        embed = utils.base_embed(f"{guild.name}", None)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="dono", value=guild.owner.mention, inline=True)
        embed.add_field(name="id", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="criado", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        embed.add_field(name="membros", value=guild.member_count, inline=True)
        embed.add_field(name="canais", value=len(guild.channels), inline=True)
        embed.add_field(name="cargos", value=len(guild.roles), inline=True)
        
        embed.add_field(name="voice", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="categorias", value=len(guild.categories), inline=True)
        embed.add_field(name="boost", value=f"nível {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["membros"], brief="mostra contagem de membros")
    @commands.has_permissions(moderate_members=True)
    async def membercount(self, ctx):
        """mostra contagem detalhada de membros
        
        uso: !membercount
        exemplo: !membercount
        """
        utils = self.bot.get_cog('utils')
        
        total = ctx.guild.member_count
        humanos = len([m for m in ctx.guild.members if not m.bot])
        bots = len([m for m in ctx.guild.members if m.bot])
        online = len([m for m in ctx.guild.members if m.status != discord.Status.offline])
        
        embed = utils.base_embed("membros", None)
        embed.add_field(name="total", value=f"`{total}`", inline=True)
        embed.add_field(name="humanos", value=f"`{humanos}`", inline=True)
        embed.add_field(name="bots", value=f"`{bots}`", inline=True)
        embed.add_field(name="online", value=f"`{online}`", inline=True)
        
        await ctx.send(embed=embed)
    
    # ==================== UTILIDADES ====================
    
    @commands.command(brief="altera o apelido de um membro")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        """altera o apelido de um membro
        
        uso: !nick (user) [apelido]
        exemplo: !nick @João JoãoMod
        exemplo: !nick @Maria (remove apelido)
        """
        utils = self.bot.get_cog('utils')
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = utils.base_embed("sem permissão", "você não pode alterar o nick de alguém com cargo igual ou superior")
            return await ctx.send(embed=embed)
        
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname, reason=f"{ctx.author} | comando nick")
            
            embed = utils.base_embed("apelido alterado", None)
            embed.add_field(name="usuário", value=member.mention, inline=False)
            embed.add_field(name="anterior", value=f"`{old_nick}`", inline=True)
            embed.add_field(name="novo", value=f"`{nickname or member.name}`", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = utils.base_embed("erro", f"`{str(e)}`")
            await ctx.send(embed=embed)
    
    @commands.command(brief="envia um anúncio em um canal")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, mensagem: str):
        """envia um anúncio em formato embed em um canal
        
        uso: !announce (canal) (mensagem)
        exemplo: !announce #geral Servidor atualizado para v2.0!
        exemplo: !announce #anuncios Novo evento começando hoje às 20h
        """
        utils = self.bot.get_cog('utils')
        
        embed = utils.base_embed("anúncio", mensagem)
        embed.set_footer(text=f"por {ctx.author.name}")
        
        await channel.send(embed=embed)
        
        confirm = utils.base_embed("anúncio enviado", None)
        confirm.add_field(name="canal", value=channel.mention, inline=True)
        await ctx.send(embed=confirm)
    
    @commands.command(brief="lista comandos de moderação")
    @commands.has_permissions(moderate_members=True)
    async def modhelp(self, ctx):
        """lista todos os comandos de moderação
        
        uso: !modhelp
        exemplo: !modhelp
        """
        utils = self.bot.get_cog('utils')
        
        embed = utils.base_embed("comandos de moderação", None)
        
        # Membros
        membros = (
            "`!kick` - expulsa membro\n"
            "`!ban` - bane membro\n"
            "`!unban` - desbane pelo ID\n"
            "`!banlist` - lista banidos\n"
            "`!timeout` - dá timeout\n"
            "`!removetimeout` - remove timeout\n"
            "`!warn` - avisa membro\n"
            "`!warns` - vê avisos\n"
            "`!clearwarns` - limpa avisos\n"
            "`!nick` - altera apelido"
        )
        embed.add_field(name="membros", value=membros, inline=False)
        
        # Cargos
        cargos = (
            "`!giverole` - dá cargo\n"
            "`!takerole` - remove cargo\n"
            "`!roles` - lista cargos\n"
            "`!createrole` - cria cargo\n"
            "`!deleterole` - deleta cargo"
        )
        embed.add_field(name="cargos", value=cargos, inline=False)
        
        # Canais
        canais = (
            "`!createchannel` - cria canal\n"
            "`!deletechannel` - deleta canal\n"
            "`!createcategory` - cria categoria\n"
            "`!lock` - bloqueia canal\n"
            "`!unlock` - desbloqueia canal\n"
            "`!slowmode` - define slowmode"
        )
        embed.add_field(name="canais", value=canais, inline=False)
        
        # Mensagens
        msgs = (
            "`!clear` - limpa mensagens\n"
            "`!announce` - faz anúncio"
        )
        embed.add_field(name="mensagens", value=msgs, inline=False)
        
        # Info
        info = (
            "`!serverinfo` - info do servidor\n"
            "`!membercount` - contagem de membros"
        )
        embed.add_field(name="informações", value=info, inline=False)
        
        embed.set_footer(text="use !help [comando] pra ver detalhes completos")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
    print("✅ Sistema de Moderação carregado! 🛡️")