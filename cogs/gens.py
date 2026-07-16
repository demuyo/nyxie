import json, random, discord
from discord.ext import commands
from .views import Paginator, RegeneratorView

def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

# Carregar todos
names = carregar_json("cogs/assets/names.json")
lines = carregar_json("cogs/assets/lines.json")
ddd = carregar_json("cogs/assets/ddd.json")
locations = carregar_json("cogs/assets/locations.json")
generic = carregar_json("cogs/assets/generic.json")

class fordevs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Gerador de nomes
    @commands.command(brief="gera um nome aleatório brasileiro")
    async def nome(self, ctx, gen: str = None):
        """gera um nome aleatório brasileiro
        
        uso: nome [gênero]
        
        exemplos:
        - nome
        - nome masculino
        - nome feminino
        """
        utils = self.bot.get_cog('utils')

        nome_completo, gender, ultimo_sobrenome = utils.gerar_nome(gen)
        
        embed = utils.base_embed("nome gerado", nome_completo)
        embed.add_field(name="Sexo", value=gender, inline=False)

        view = RegeneratorView(ctx, "nome", utils, gen=gen)
      
        await ctx.send(embed=embed, view=view)
        
    # Gerador de telefone
    @commands.command(brief="gera um número de telefone válido")
    async def telefone(self, ctx, ddd_in: str = None):
        """gera um número de telefone válido
        
        uso: telefone [ddd]
        
        exemplos:
        - telefone
        - telefone 11
        - telefone 21
        """
        utils = self.bot.get_cog('utils')

        celular, _, ddd_info  = utils.gerar_telefone(ddd_in)

        embed = utils.base_embed("telefone gerado", None)
        embed.add_field(name="Celular", value=celular, inline=False)
        embed.add_field(name="Estado", value=ddd_info["estado"], inline=True)
        embed.add_field(name="Região", value=ddd_info["regiao"], inline=True)

        view = RegeneratorView(ctx, "telefone", utils, ddd_in=ddd_in)

        await ctx.send(embed=embed, view=view)

    # Gerador de endereço
    @commands.command(aliases=["endereco"], brief="gera um endereço completo com cep")
    async def cep(self, ctx, estado: str = None):
        """gera um endereço completo com cep válido
        
        uso: cep [estado]
        
        exemplos:
        - cep
        - cep sp
        - cep rj
        """
        utils = self.bot.get_cog('utils')

        cep, cidade, bairro, rua, _ = utils.gerar_cep(estado)
        
        embed = utils.base_embed("endereço gerado", None)
        embed.add_field(name="CEP", value=cep, inline=True)
        embed.add_field(name="Cidade", value=cidade, inline=True)
        embed.add_field(name="Bairro", value=bairro, inline=True)
        embed.add_field(name="Endereço", value=rua, inline=True)
        
        view = RegeneratorView(ctx, "cep", utils, estado=estado)
        await ctx.send(embed=embed, view=view)
    
    # Gerador de CPF
    @commands.command(brief="gera um cpf válido")
    async def cpf(self, ctx):
        """gera um cpf válido
        
        uso: cpf
        
        exemplos:
        - cpf
        """
        utils = self.bot.get_cog('utils')

        cpf_gerado = utils.gerar_cpf()
        embed = utils.base_embed("cpf gerado", f"{cpf_gerado}")
        
        view = RegeneratorView(ctx, "cpf", utils)
        await ctx.send(embed=embed, view=view)
    
    # Gerador de Data de Nascimento
    @commands.command(aliases=["idade"], brief="gera uma data de nascimento")
    async def nascimento(self, ctx, idade_c: int = None):
        """gera uma data de nascimento com idade e signo
        
        uso: nascimento [idade]
        
        exemplos:
        - nascimento
        - nascimento 25
        - nascimento 18
        """
        utils = self.bot.get_cog('utils')
        _, _, _, signo, idade, data = utils.gerar_data_nascimento(idade_c)
        
        embed = utils.base_embed("data de nascimento", None)
        embed.add_field(name="Data", value=data, inline=True)
        embed.add_field(name="Idade", value=f"{idade} anos", inline=True)
        embed.add_field(name="Signo", value=signo, inline=True)
        
        view = RegeneratorView(ctx, "nascimento", utils, idade_c=idade_c)
        await ctx.send(embed=embed, view=view)
    
    # Gerador de RG
    @commands.command(brief="gera um rg válido")
    async def rg(self, ctx, estado: str = None):
        """gera um rg válido com órgão expedidor
        
        uso: rg [estado]
        
        exemplos:
        - rg
        - rg sp
        - rg mg
        """
        # Gera RG
        utils = self.bot.get_cog('utils')
        rg, orgao = utils.gerar_rg(estado)
        
        embed = utils.base_embed("rg gerado", None)
        embed.add_field(name="Número", value=f"{rg}", inline=False)
        embed.add_field(name="Órgão Expedidor", value=orgao, inline=True)
        
        view = RegeneratorView(ctx, "rg", utils, estado=estado)
        await ctx.send(embed=embed, view=view)
    
    # Gerador de e-mail
    @commands.command(brief="gera um e-mail com senha")
    async def email(self, ctx, dominio = None):
        """gera um e-mail com senha aleatória
        
        uso: email [domínio]
        
        exemplos:
        - email
        - email gmail.com
        - email outlook.com
        """
        utils = self.bot.get_cog('utils')

        email = utils.gerar_email(dominio)
        senha = utils.gerar_senha()

        embed = utils.base_embed("e-mail gerado", None)
        embed.add_field(name="E-mail", value=email, inline=False)
        embed.add_field(name="Senha", value=senha, inline=False)

        view = RegeneratorView(ctx, "email", utils, dominio=dominio)
        await ctx.send(embed=embed, view=view)
    
    # Gerador de infos extras
    @commands.command(brief="gera informações físicas extras")
    async def extras(self, ctx):
        """gera informações físicas extras
        
        uso: extras
        
        exemplos:
        - extras
        """
        utils = self.bot.get_cog('utils')

        cor, peso, altura, tipo_sanguineo = utils.generic() 

        embed = utils.base_embed("extras", None)
        embed.add_field(name="Peso", value=peso, inline=True)
        embed.add_field(name="Altura", value=altura, inline=True)
        embed.add_field(name="Tipo sanguíneo", value=tipo_sanguineo, inline=True)
        embed.add_field(name="Cor favorita", value=cor, inline=False)
        
        view = RegeneratorView(ctx, "extras", utils)
        await ctx.send(embed=embed, view=view)

    @commands.command(brief="gera uma pessoa completa")
    async def pessoa(self, ctx):
        """gera uma pessoa completa com todos os dados
        
        uso: pessoa
        
        exemplos:
        - pessoa
        """
        utils = self.bot.get_cog('utils')

        # Nome da pessoa + filiação
        nome_completo, genero, ultimo_sobrenome = utils.gerar_nome()
        nome_mae, _, _ = utils.gerar_nome(gen="feminino")
        nome_pai, _, _ = utils.gerar_nome(gen="masculino", sobrenomes_qtd=random.randint(1, 2))

        # CEP 
        cep, cidade, bairro, rua, estado = utils.gerar_cep()

        # RG e CPF
        cpf = utils.gerar_cpf()
        rg, orgao_exp = utils.gerar_rg(estado)

        # Data de nascimento, signo, idade
        _, _, _, signo, idade, data = utils.gerar_data_nascimento()

        # E-mail e senha
        email = utils.gerar_email()
        senha = utils.gerar_senha()

        # Telefone
        celular, fixo, _  = utils.gerar_telefone(estado)

        # Extras
        cor, peso, altura, tipo_sanguineo = utils.generic()

        page1 = utils.base_embed("Pessoa completa", "Informações Pessoais")
    
        page1.add_field(name="Nome", value=nome_completo, inline=True)
        page1.add_field(name="Sexo", value=genero, inline=True)
        page1.add_field(name="\u200b", value="\u200b", inline=True)
        
        page1.add_field(name="CPF", value=cpf, inline=True)
        page1.add_field(name="RG", value=rg, inline=True)
        page1.add_field(name="Órgão", value=orgao_exp, inline=True)
        
        page1.add_field(name="Data Nasc.", value=data, inline=True)
        page1.add_field(name="Idade", value=f"{idade} anos", inline=True)
        page1.add_field(name="Signo", value=signo, inline=True)
        
        page1.add_field(name="Nome da Mãe", value=nome_mae, inline=False)
        page1.add_field(name="Nome do Pai", value=f"{nome_pai} {ultimo_sobrenome}", inline=False)
        
        page1.set_footer(text="⛧ Página 1/3 • Use os botões para navegar")
        
        # ====== PÁGINA 2: Contato e Endereço ======
        page2 = utils.base_embed("Pessoa completa", "Contato e Endereço")
        
        page2.add_field(name="E-mail", value=email, inline=False)
        page2.add_field(name="Senha", value=senha, inline=False)
        
        page2.add_field(name="Celular", value=celular, inline=True)
        page2.add_field(name="Fixo", value=fixo, inline=True)
        
        page2.add_field(name="Endereço", value=rua, inline=False)
        page2.add_field(name="Bairro", value=bairro, inline=True)
        page2.add_field(name="Cidade", value=cidade, inline=True)
        page2.add_field(name="CEP", value=cep, inline=True)
        
        page2.set_footer(text="⛧ Página 2/3 • Use os botões para navegar")
        
        # ====== PÁGINA 3: Características Físicas ======
        page3 = utils.base_embed("Pessoa completa", "Características Físicas")
        
        page3.add_field(name="Peso", value=peso, inline=True)
        page3.add_field(name="Altura", value=altura, inline=True)
        page3.add_field(name="\u200b", value="\u200b", inline=True)
        
        page3.add_field(name="Tipo Sanguíneo", value=tipo_sanguineo, inline=True)
        page3.add_field(name="Cor Favorita", value=cor, inline=True)
        page3.add_field(name="\u200b", value="\u200b", inline=True)
        
        page3.set_footer(text="⛧ Página 3/3 • Use os botões para navegar")
        
        # ====== ENVIAR COM PAGINAÇÃO ======
        pages = [page1, page2, page3]
        view = Paginator(pages)
        
        await ctx.send(embed=pages[0], view=view)
                       
async def setup(bot):
    await bot.add_cog(fordevs(bot))