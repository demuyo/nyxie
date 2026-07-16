import discord, random
from discord.ext import commands
from datetime import datetime  

class Utilities(commands.Cog):
    
    def __init__(self, bot):
        self.start_time = datetime.now()
        self.bot = bot
    
    @commands.command(
        usage="",
        brief="mostra a latência do bot",
        help="exibe o tempo de resposta do bot em milissegundos. útil para verificar a conexão."
    )
    async def ping(self, ctx):
        """
        mostra a latência do bot.
        
        exibe o tempo de resposta entre o bot e os servidores do discord.
        quanto menor, melhor a conexão.
        
        uso:
        !ping
        
        exemplo:
        !ping
        """
        await ctx.send(f"`{round(self.bot.latency * 1000)}ms`")

    @commands.command(
        aliases=["icone"],
        usage="[usuário]",
        brief="mostra o avatar de um usuário",
        help="exibe o avatar em tamanho grande. se não especificar usuário, mostra o seu."
    )
    async def avatar(self, ctx, user: discord.Member = None):
        """
        mostra o avatar de um usuário.
        
        exibe a imagem de perfil em alta resolução.
        se não mencionar ninguém, mostra seu próprio avatar.
        
        uso:
        !avatar [usuário]
        
        exemplo:
        !avatar
        !avatar @fulano
        !icone @fulano
        """
        utils = self.bot.get_cog('utils')
        user = user or ctx.author

        embed = utils.base_embed(f"{user.name}", None)
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["ui"],
        usage="[usuário]",
        brief="mostra informações de um usuário",
        help="exibe id, data de criação, entrada no servidor e quantidade de cargos."
    )
    async def userinfo(self, ctx, user: discord.Member = None):
        """
        mostra informações detalhadas de um usuário.
        
        exibe dados como id, quando a conta foi criada, quando entrou no servidor
        e quantos cargos possui. se não mencionar ninguém, mostra suas informações.
        
        uso:
        !userinfo [usuário]
        
        exemplo:
        !userinfo
        !userinfo @fulano
        !ui @fulano
        """
        user = user or ctx.author
        utils = self.bot.get_cog('utils')
        
        embed = utils.base_embed(f"{user.name}", None)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(name="id", value=f"`{user.id}`", inline=False)
        embed.add_field(
            name="created",
            value=f"<t:{int(user.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="joined",
            value=f"<t:{int(user.joined_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="roles",
            value=len(user.roles) - 1,
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        aliases=["calculadora", "calcular"],
        usage="(expressão)",
        brief="calculadora matemática",
        help="resolve expressões matemáticas. suporta +, -, *, /, ** (potência) e parênteses."
    )
    async def calc(self, ctx, *, expressao):
        """
        calculadora matemática.
        
        resolve expressões com operações básicas e avançadas.
        operadores: + - * / ** (potência) % (resto) // (divisão inteira)
        também suporta parênteses para controlar a ordem.
        
        uso:
        !calc (expressão)
        
        exemplo:
        !calc 2 + 2
        !calc 5 * (3 + 2)
        !calculadora 2 ** 8
        !calc 100 / 3
        """
        try:
            resultado = eval(expressao)
            await ctx.send(f"`{expressao}` = **{resultado}**")
        except:
            await ctx.send("expressão inválida")
    
    @commands.command(
        usage="",
        brief="mostra há quanto tempo o bot está online",
        help="exibe o tempo desde a última reinicialização do bot em dias, horas, minutos e segundos."
    )
    async def uptime(self, ctx):
        """
        mostra há quanto tempo o bot está online.
        
        exibe o tempo desde a última vez que o bot foi iniciado.
        útil para verificar estabilidade e tempo de atividade.
        
        uso:
        !uptime
        
        exemplo:
        !uptime
        """
        uptime = datetime.now() - self.start_time
        dias = uptime.days
        horas, resto = divmod(uptime.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        
        await ctx.send(f"estou online há: **{dias}d {horas}h {minutos}m {segundos}s**")

    @commands.command(
        aliases=["inverter", "inverte"],
        usage="(texto)",
        brief="inverte um texto",
        help="reverte a ordem dos caracteres de uma palavra ou frase."
    )
    async def reverse(self, ctx, texto):
        """
        inverte um texto.
        
        reverte completamente a ordem dos caracteres.
        útil para criar palavras espelhadas ou texto invertido.
        
        uso:
        !reverse (texto)
        
        exemplo:
        !reverse hello
        !inverter discord
        !inverte teste123
        """
        if not texto: 
            await ctx.send("digite algo!")
        else:
            texto_invertido = texto[::-1]
            await ctx.send(f"`{texto_invertido}`")
    
    @commands.command(
        aliases=["contar", "conta", "palavras"],
        usage="(texto)",
        brief="conta caracteres e palavras",
        help="mostra quantidade de caracteres (com e sem espaços) e número de palavras."
    )
    async def caracteres(self, ctx, *texto):
        """
        conta caracteres e palavras de um texto.
        
        exibe três contagens:
        - caracteres totais (com espaços)
        - caracteres sem contar espaços
        - número de palavras
        
        uso:
        !caracteres (texto)
        
        exemplo:
        !caracteres hello world
        !contar este é um teste
        !palavras discord bot legal
        """
        utils = self.bot.get_cog('utils')

        texto_sem_espaco = ''.join(texto)
        texto_com_espaco = ' '.join(texto)
        n_palavras = len(texto)
        
        if not texto: 
            await ctx.send("digite algo!")
        else:
            n_caracteres_sem_espaco = len(texto_sem_espaco)
            n_caracteres_espaco = len(texto_com_espaco)
            

        embed = utils.base_embed(texto_com_espaco[:16], None)
        embed.add_field(name="nº de caracteres", value=n_caracteres_espaco, inline=False)
        embed.add_field(name="nº de caracteres (sem contar espaço)", value=n_caracteres_sem_espaco, inline=False)
        embed.add_field(name="nº de palavras", value=n_palavras, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utilities(bot))