from discord.ext import commands
from .views import Helper
import discord

class Geral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="mostra a lista de comandos")
    async def help(self, ctx, *, comando: str = None):
        """
        mostra a lista de comandos ou detalhes de um comando específico
        
        uso: !help [comando]
        exemplo: !help
        exemplo: !help ban
        exemplo: !help personalidade
        """
        utils = self.bot.get_cog('utils')
        
        # ====== SEU ID DE DONO ======
        OWNER_ID = 1331049456371630150  # <-- seu ID
        
        # ====== SE PASSOU UM COMANDO ESPECÍFICO ======
        if comando:
            comando = comando.lstrip('!')
            
            # ====== PÁGINA SECRETA DO DONO ======
            if comando.lower() in ['dev', 'owner', 'dono', 'admin']:
                if ctx.author.id != OWNER_ID:
                    embed = utils.base_embed(
                        "comando não encontrado",
                        f"o comando `!{comando}` não existe.\nuse `!help` para ver todos os comandos."
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = utils.base_embed("comandos do dono", "comandos exclusivos para você")
                
                downloads = (
                    "`!arquivos` - lista arquivos salvos na pasta downloads\n"
                    "`!deletar [arquivo]` - deleta arquivo específico\n"
                    "`!clrdl` - limpa pasta de downloads"
                )
                embed.add_field(name="downloads", value=downloads, inline=False)
                
                bot_cmds = (
                    "`!restart` - reinicia o bot\n"
                    "`!update` - git pull e reinicia\n"
                    "`!logs [quantidade]` - mostra últimos logs\n"
                    "`!debugenv` - mostra variáveis de ambiente"
                )
                embed.add_field(name="bot", value=bot_cmds, inline=False)
                
                debug = (
                    "`!eval [código]` - executa código python\n"
                    "`!broadcast [msg]` - anuncia em todos servidores"
                )
                embed.add_field(name="debug", value=debug, inline=False)
                
                config = (
                    "`!blacklist [user/guild] [id] [motivo]` - bloqueia user/servidor\n"
                    "`!unblacklist [user/guild] [id]` - remove da blacklist\n"
                    "`!blacklisted` - lista bloqueados\n"
                    "`!setprefix [prefix]` - muda prefix do servidor\n"
                    "`!resetprefix` - reseta prefix"
                )
                embed.add_field(name="config", value=config, inline=False)
                    
                embed.set_footer(text="esses comandos são só seus <3")
                
                try:
                    await ctx.author.send(embed=embed)
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                except discord.Forbidden:
                    await ctx.send("sua dm tá fechada, abre lá que eu mando", delete_after=5)
                return

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
            """formata um comando no padrão limpo: !comando [args] - descrição"""
            cmd = self.bot.get_command(cmd_name)
            if cmd:
                brief = cmd.brief or "sem descrição"
                
                # Se o comando tiver usage manual, usa ele
                if cmd.usage:
                    param_str = cmd.usage
                else:
                    # Monta os argumentos lendo a função
                    params = []
                    for param_name, param in cmd.clean_params.items():
                        if param.default == param.empty:
                            params.append(f"({param_name})") # Obrigatório
                        else:
                            params.append(f"[{param_name}]") # Opcional
                    param_str = " ".join(params)
                
                if param_str:
                    return f"`!{cmd.name} {param_str}` - {brief}"
                else:
                    return f"`!{cmd.name}` - {brief}"
            return f"`!{cmd_name}` - comando não encontrado"

        # ====== PÁGINA 1: SUMÁRIO ======
        page1 = utils.base_embed("sumário", "aqui estão meus comandos...\nuse os botões para navegar pelas categorias.")
        page1.add_field(name="moderação", value="kick, ban, warn, timeout, cargos, canais...", inline=False)
        page1.add_field(name="ia e conversação", value="chat com ia, gerar imagens, personalidades...", inline=False)
        page1.add_field(name="utilitários", value="userinfo, avatar, baixar, wiki monster hunter...", inline=False)
        page1.add_field(name="geradores", value="cpf, rg, pessoa, email, telefone...", inline=False)
        page1.add_field(name="diversos", value="comandos de diversão e rolagem de dados", inline=False)
        
        if ctx.author.id == OWNER_ID:
            page1.add_field(name="secreto", value="`!help dev`", inline=False)
            
        page1.set_footer(text="use os botões para navegar")

        # ====== PÁGINA 2: MODERAÇÃO ======
        page2 = utils.base_embed("moderação", "comandos administrativos")
        
        membros_cmds = ['kick', 'ban', 'unban', 'banlist', 'timeout', 'removetimeout', 'warn', 'warns', 'clearwarns', 'nick']
        page2.add_field(name="membros", value="\n".join([format_cmd(c) for c in membros_cmds if self.bot.get_command(c)]), inline=False)
        
        cargos_cmds = ['giverole', 'takerole', 'roles', 'createrole', 'deleterole']
        page2.add_field(name="cargos", value="\n".join([format_cmd(c) for c in cargos_cmds if self.bot.get_command(c)]), inline=False)
        
        canais_cmds = ['createchannel', 'deletechannel', 'createcategory', 'lock', 'unlock', 'slowmode']
        page2.add_field(name="canais", value="\n".join([format_cmd(c) for c in canais_cmds if self.bot.get_command(c)]), inline=False)
        
        msgs_cmds = ['clear', 'announce']
        page2.add_field(name="mensagens", value="\n".join([format_cmd(c) for c in msgs_cmds if self.bot.get_command(c)]), inline=False)
        
        info_cmds = ['serverinfo', 'membercount']
        page2.add_field(name="informações", value="\n".join([format_cmd(c) for c in info_cmds if self.bot.get_command(c)]), inline=False)
        
        page2.set_footer(text="(obrigatório) [opcional] | !help [comando] pra detalhes")

        # ====== PÁGINA 3: IA / CONVERSAÇÃO ======
        page3 = utils.base_embed("ia e conversação", "meu núcleo de inteligência")
        
        chat_cmds = ['startchat', 'stopchat', 'talk', 'reset']
        page3.add_field(name="interação", value="\n".join([format_cmd(c) for c in chat_cmds if self.bot.get_command(c)]), inline=False)
        
        # Removi 'personalidade' e 'vibe' daqui pois eles foram removidos do novo conversation.py e chatcommands.py
        # Se você os recriar no conversation.py novo, nós adicionamos de volta.
        
        img_cmds = ['gerar']
        page3.add_field(name="materialização", value="\n".join([format_cmd(c) for c in img_cmds if self.bot.get_command(c)]), inline=False)
        
        page3.set_footer(text="(obrigatório) [opcional] | !help [comando] pra detalhes")

        # ====== PÁGINA 4: UTILITÁRIOS ======
        page4 = utils.base_embed("utilitários", "ferramentas úteis do dia a dia")
        
        plataformas_cmds = ['baixar', 'converter', 'search']
        page4.add_field(name="plataformas e mídia", value="\n".join([format_cmd(c) for c in plataformas_cmds if self.bot.get_command(c)]), inline=False)
        
        mh_cmds = ['mhw', 'mhr', 'mhwilds']
        page4.add_field(name="monster hunter", value="\n".join([format_cmd(c) for c in mh_cmds if self.bot.get_command(c)]), inline=False)

        util_cmds = ['ping', 'uptime', 'avatar', 'userinfo', 'calc', 'caracteres', 'reverse']
        page4.add_field(name="geral", value="\n".join([format_cmd(c) for c in util_cmds if self.bot.get_command(c)]), inline=False)
        
        page4.set_footer(text="(obrigatório) [opcional] | !help [comando] pra detalhes")

        # ====== PÁGINA 5: GERADORES ======
        page5 = utils.base_embed("geradores", "criação de dados fictícios")
        
        gen_cmds = ['pessoa', 'nome', 'cpf', 'rg', 'telefone', 'email', 'nascimento', 'cep', 'extras']
        page5.add_field(name="dados", value="\n".join([format_cmd(c) for c in gen_cmds if self.bot.get_command(c)]), inline=False)
        
        page5.set_footer(text="(obrigatório) [opcional] | !help [comando] pra detalhes")

        # ====== PÁGINA 6: DIVERSOS ======
        page6 = utils.base_embed("diversos", "aleatoriedades e brincadeiras")
        
        div_cmds = ['8ball', 'coin', 'roll', 'choose']
        page6.add_field(name="fun", value="\n".join([format_cmd(c) for c in div_cmds if self.bot.get_command(c)]), inline=False)
        
        page6.set_footer(text="(obrigatório) [opcional] | !help [comando] pra detalhes")

        # ====== ENVIAR COM PAGINAÇÃO ======
        pages = [page1, page2, page3, page4, page5, page6]
        view = Helper(pages)
        await ctx.send(embed=pages[0], view=view)

async def setup(bot):
    await bot.add_cog(Geral(bot))