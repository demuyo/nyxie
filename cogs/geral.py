from discord.ext import commands
from .views import Helper
import discord

class Geral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="mostra a lista de comandos")
    async def help(self, ctx, *, comando: str = None):
        """mostra a lista de comandos ou detalhes de um comando específico
        
        uso: !help [comando]
        exemplo: !help
        exemplo: !help ban
        exemplo: !help personalidade
        """
        utils = self.bot.get_cog('utils')
        
        # ====== SEU ID DE DONO ======
        OWNER_ID = 1331049456371630150  # <-- coloca seu ID aqui
        
        # ====== SE PASSOU UM COMANDO ESPECÍFICO ======
        if comando:
            comando = comando.lstrip('!')
            
            # ====== PÁGINA SECRETA DO DONO ======
            if comando.lower() in ['dev', 'owner', 'dono', 'admin']:
                if ctx.author.id != OWNER_ID:
                    # Finge que não existe
                    embed = utils.base_embed(
                        "comando não encontrado",
                        f"o comando `!{comando}` não existe.\nuse `!help` para ver todos os comandos."
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Mostra página secreta NA DM
                embed = utils.base_embed("comandos do dono", "comandos exclusivos para você")
                
                # Downloads privados
                downloads = (
                    "`!arquivos` - lista arquivos salvos na pasta downloads\n"
                    "`!deletar` `(arquivo)` - deleta arquivo específico\n"
                    "`!clrdl` - limpa pasta de downloads"
                )
                embed.add_field(name="downloads", value=downloads, inline=False)

                # Gerenciamento do bot
                bot_cmds = (
                    "`!restart` - reinicia o bot\n"
                    "`!update` - git pull e reinicia\n"
                    "`!logs` `[quantidade]` - mostra últimos logs"
                )
                embed.add_field(name="bot", value=bot_cmds, inline=False)

                # Debug/Dev
                debug = (
                    "`!eval` `(código)` - executa código python\n"
                    "`!broadcast` `(msg)` - anuncia em todos servidores"
                )
                embed.add_field(name="debug", value=debug, inline=False)

                # Blacklist/Config
                config = (
                    "`!blacklist` `(user/guild)` `(id)` `[motivo]` - bloqueia user/servidor\n"
                    "`!unblacklist` `(user/guild)` `(id)` - remove da blacklist\n"
                    "`!blacklisted` - lista bloqueados\n"
                    "`!setprefix` `(prefix)` - muda prefix do servidor\n"
                    "`!resetprefix` - reseta prefix"
                )
                embed.add_field(name="config", value=config, inline=False)
                    
                embed.set_footer(text="esses comandos são só seus <3")
                    # ====== ENVIA NA DM ======
                try:
                    await ctx.author.send(embed=embed)
                    
                    # Deleta a mensagem original do chat pra não deixar rastro
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                    
                    # Opcional: manda confirmação sutil no chat (ou não manda nada)
                    # await ctx.send("📩", delete_after=2)
                    
                except discord.Forbidden:
                    # DM fechada - manda no chat mesmo mas avisa
                    await ctx.send("❌ sua dm tá fechada, abre lá que eu mando", delete_after=5)
            
                return
            
            # Comando normal
            cmd = self.bot.get_command(comando)
            
            if cmd is None:
                embed = utils.base_embed(
                    "comando não encontrado",
                    f"o comando `!{comando}` não existe.\nuse `!help` para ver todos os comandos."
                )
                await ctx.send(embed=embed)
                return
            
            embed = utils.comando_help_embed(cmd)
            
            if embed is None:
                embed = utils.base_embed(
                    f"!{cmd.name}",
                    "este comando não possui documentação ainda."
                )
            
            await ctx.send(embed=embed)
            return

        # ====== FUNÇÃO HELPER PARA FORMATAR COMANDOS ======
        def format_cmd(cmd_name):
            """formata um comando com seu brief"""
            cmd = self.bot.get_command(cmd_name)
            if cmd:
                brief = cmd.brief or "sem descrição"
                params = []
                for param_name, param in cmd.clean_params.items():
                    if param.default == param.empty:
                        params.append(f"`({param_name})`")
                    else:
                        params.append(f"`[{param_name}]`")
                
                param_str = " ".join(params) if params else ""
                
                if param_str:
                    return f"`!{cmd.name}` {param_str} - {brief}"
                else:
                    return f"`!{cmd.name}` - {brief}"
            return f"`!{cmd_name}` - comando não encontrado"

        # ====== PÁGINA 1: SUMÁRIO ======
        page1 = utils.base_embed("sumário", None)
        page1.add_field(name="🛡️ moderação", value="kick, ban, warn, timeout, cargos, canais...", inline=False)
        page1.add_field(name="🤖 ia", value="chat com ia, gerar imagens, personalidades...", inline=False)
        page1.add_field(name="⚙️ utilitários", value="userinfo, avatar, baixar...", inline=False)
        page1.add_field(name="🔮 geradores", value="cpf, rg, pessoa, email, telefone...", inline=False)
        page1.add_field(name="🎲 diversos", value="comandos bobos e divertidos", inline=False)
        
        # ====== HINT SECRETO PRO DONO ======
        if ctx.author.id == OWNER_ID:
            page1.add_field(name="⛧", value="`!help dev`", inline=False)
        
        page1.set_footer(text="use os botões para navegar")

        # ====== PÁGINA 2: MODERAÇÃO ======
        page2 = utils.base_embed("moderação", None)

        # Membros
        membros_cmds = ['kick', 'ban', 'unban', 'banlist', 'timeout', 'removetimeout', 'warn', 'warns', 'clearwarns', 'nick']
        membros = "\n".join([format_cmd(c) for c in membros_cmds])
        page2.add_field(name="membros", value=membros, inline=False)

        # Cargos
        cargos_cmds = ['giverole', 'takerole', 'roles', 'createrole', 'deleterole']
        cargos = "\n".join([format_cmd(c) for c in cargos_cmds])
        page2.add_field(name="cargos", value=cargos, inline=False)

        # Canais
        canais_cmds = ['createchannel', 'deletechannel', 'createcategory', 'lock', 'unlock', 'slowmode']
        canais = "\n".join([format_cmd(c) for c in canais_cmds])
        page2.add_field(name="canais", value=canais, inline=False)

        # Mensagens
        msgs_cmds = ['clear', 'announce']
        msgs = "\n".join([format_cmd(c) for c in msgs_cmds])
        page2.add_field(name="mensagens", value=msgs, inline=False)

        # Info
        info_cmds = ['serverinfo', 'membercount']
        info = "\n".join([format_cmd(c) for c in info_cmds])
        page2.add_field(name="informações", value=info, inline=False)

        page2.set_footer(text="(obrigatório) [opcional] ⛧ !help [comando] pra detalhes")

        # ====== PÁGINA 3: IA / CONVERSAÇÃO ======
        page3 = utils.base_embed("ia e conversação", None)

        # Chat
        chat_cmds = ['chat', 'stopchat', 'forcestop', 'chats', 'talk']
        chat = "\n".join([format_cmd(c) for c in chat_cmds])
        page3.add_field(name="chat", value=chat, inline=False)

        # Histórico
        hist_cmds = ['reset', 'history', 'export']
        hist = "\n".join([format_cmd(c) for c in hist_cmds])
        page3.add_field(name="histórico", value=hist, inline=False)

        # Personalidade
        persona_cmds = ['personalidade', 'vibe']
        persona = "\n".join([format_cmd(c) for c in persona_cmds])
        page3.add_field(name="personalidade", value=persona, inline=False)

        page3.set_footer(text="(obrigatório) [opcional] ⛧ !help [comando] pra detalhes")

        # ====== PÁGINA 4: UTILITÁRIOS ======
        page4 = utils.base_embed("utilitários", None)

        # Adicione seus comandos de utilitários aqui
        util_cmds = ['ping', 'avatar', 'userinfo']  # exemplo
        util = "\n".join([format_cmd(c) for c in util_cmds if self.bot.get_command(c)])

        plataformas_cmds = ['download', 'search']  # ajuste conforme seus comandos
        plataformas = "\n".join([format_cmd(c) for c in plataformas_cmds if self.bot.get_command(c)])
        page4.add_field(name="plataformas", value=plataformas, inline=False)

        if util:
            page4.add_field(name="geral", value=util, inline=False)
        else:
            page4.add_field(name="geral", value="*comandos em breve*", inline=False)

        page4.set_footer(text="(obrigatório) [opcional] ⛧ !help [comando] pra detalhes")

        # ====== PÁGINA 5: GERADORES ======
        page5 = utils.base_embed("geradores", None)

        gen_cmds = ['pessoa', 'nome', 'cpf', 'rg', 'telefone', 'email', 'nascimento', 'cep', 'extras']
        gen = "\n".join([format_cmd(c) for c in gen_cmds if self.bot.get_command(c)])
        if gen:
            page5.add_field(name="dados", value=gen, inline=False)
        else:
            page5.add_field(name="dados", value="*comandos em breve*", inline=False)

        page5.set_footer(text="(obrigatório) [opcional] ⛧ !help [comando] pra detalhes")

        # ====== PÁGINA 6: DIVERSOS ======
        page6 = utils.base_embed("diversos", None)

        div_cmds = ['say', 'embed', '8ball', 'coinflip', 'roll']  # ajuste conforme seus comandos
        div = "\n".join([format_cmd(c) for c in div_cmds if self.bot.get_command(c)])
        if div:
            page6.add_field(name="fun", value=div, inline=False)
        else:
            page6.add_field(name="fun", value="*comandos em breve*", inline=False)

        page6.set_footer(text="(obrigatório) [opcional] ⛧ !help [comando] pra detalhes")

        # ====== ENVIAR COM PAGINAÇÃO ======
        pages = [page1, page2, page3, page4, page5, page6]
        view = Helper(pages)

        await ctx.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(Geral(bot))