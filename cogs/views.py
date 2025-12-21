import discord
from discord.ui import View, Button

class Paginator(View):
    def __init__(self, pages):
        super().__init__(timeout=180)
        self.pages = pages
        self.current = 0
        self.update_buttons()
    
    def update_buttons(self):
        self.prev_button.disabled = (self.current == 0)
        self.next_button.disabled = (self.current == len(self.pages) - 1)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.current -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()

class Helper(View):
    def __init__(self, pages):
        super().__init__(timeout=180)
        self.pages = pages
        self.current = 0
        self.update_buttons()
    
    def update_buttons(self):
        # ← AQUI: substitui essa função
        # Deixa todos cinza
        self.home_button.style = discord.ButtonStyle.secondary

        self.mods_button.style = discord.ButtonStyle.secondary
        self.ia_button.style = discord.ButtonStyle.secondary
        self.utils_button.style = discord.ButtonStyle.secondary
        self.gens_button.style = discord.ButtonStyle.secondary
        self.random_button.style = discord.ButtonStyle.secondary
        
        # Destaca o ativo em azul
        botoes = [
            self.home_button,      # 0 - página 1 (sumário)
            self.mods_button,      # 1 - página 2 (moderação)
            self.ia_button,        # 2 - página 3 (ia)
            self.utils_button,     # 3 - página 4 (utils)
            self.gens_button,      # 4 - página 5 (gens)
            self.random_button,    # 5 - página 6 (diversos)
        ]
        botoes[self.current].style = discord.ButtonStyle.primary
    
    # Home
    @discord.ui.button(emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="home")
    async def home_button(self, interaction: discord.Interaction, button: Button):
        self.current = 0
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    # Mods
    @discord.ui.button(emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id="mods")
    async def mods_button(self, interaction: discord.Interaction, button: Button):
        self.current = 1
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    # IA
    @discord.ui.button(emoji="🤖", style=discord.ButtonStyle.secondary, custom_id="ia")
    async def ia_button(self, interaction: discord.Interaction, button: Button):
        self.current = 2
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    # Utils
    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.secondary, custom_id="utils")
    async def utils_button(self, interaction: discord.Interaction, button: Button):
        self.current = 3
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    # Geradores
    @discord.ui.button(emoji="🔮", style=discord.ButtonStyle.secondary, custom_id="gens")
    async def gens_button(self, interaction: discord.Interaction, button: Button):
        self.current = 4
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    # Diversos
    @discord.ui.button(emoji="🎲", style=discord.ButtonStyle.secondary, custom_id="random")
    async def random_button(self, interaction: discord.Interaction, button: Button):
        self.current = 5
        self.update_buttons()  # ← Chama aqui
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()


class RegeneratorView(View):
    def __init__(self, ctx, tipo, utils, **kwargs):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.tipo = tipo
        self.utils = utils
        self.kwargs = kwargs  # Parâmetros extras
    
    @discord.ui.button(label="Regenerar", emoji="🔄", style=discord.ButtonStyle.primary)
    async def regen_button(self, interaction: discord.Interaction, button: Button):
        if self.tipo == "nome":
            gen = self.kwargs.get("gen")  # Pega gênero se foi passado
            nome, genero, _ = self.utils.gerar_nome(gen)
            
            embed = self.utils.base_embed("Nome Gerado", None)
            embed.add_field(name="Nome", value=nome, inline=False)
            embed.add_field(name="Gênero", value=genero, inline=True)
        
        elif self.tipo == "telefone":
            ddd_in = self.kwargs.get("ddd_in")  # Mantém o DDD escolhido
            celular, fixo, ddd_info = self.utils.gerar_telefone(ddd_in)
            
            embed = self.utils.base_embed("Telefone Gerado", None)
            embed.add_field(name="Celular", value=celular, inline=False)
            embed.add_field(name="Estado", value=ddd_info["estado"], inline=True)
            embed.add_field(name="Região", value=ddd_info["regiao"], inline=True)
        
        elif self.tipo == "cep":
            estado = self.kwargs.get("estado")
            cep, cidade, bairro, rua, _ = self.utils.gerar_cep(estado)

            embed = self.utils.base_embed("Endereço gerado", None)
            embed.add_field(name="CEP", value=cep, inline=True)
            embed.add_field(name="Cidade", value=cidade, inline=True)
            embed.add_field(name="Bairro", value=bairro, inline=True)
            embed.add_field(name="Endereço", value=rua, inline=True)

        elif self.tipo == "cpf":
            cpf_gerado = self.utils.gerar_cpf()
            embed = self.utils.base_embed("CPF gerado", f"{cpf_gerado}")

        elif self.tipo == "nascimento":
            idade_c = self.kwargs.get("idade_c")
            _, _, _, signo, idade, data = self.utils.gerar_data_nascimento(idade_c)


            embed = self.utils.base_embed("Data de Nascimento", None)
            embed.add_field(name="Data", value=data, inline=True)
            embed.add_field(name="Idade", value=f"{idade} anos", inline=True)
            embed.add_field(name="Signo", value=signo, inline=True)
        
        elif self.tipo == "rg":
            estado = self.kwargs.get("estado")
            rg, orgao = self.utils.gerar_rg(estado)
            
            embed = self.utils.base_embed("RG gerado", None)
            embed.add_field(name="Número", value=f"{rg}", inline=False)
            embed.add_field(name="Órgão Expedidor", value=orgao, inline=True)

        elif self.tipo == "email":
            dominio = self.kwargs.get("dominio")
            email = self.utils.gerar_email(dominio)
            senha = self.utils.gerar_senha()

            embed = self.utils.base_embed("E-mail gerado", None)
            embed.add_field(name="E-mail", value=email, inline=False)
            embed.add_field(name="Senha", value=senha, inline=False)
        
        elif self.tipo == "extras":
            cor, peso, altura, tipo_sanguineo = self.utils.generic() 

            embed = self.utils.base_embed("Extras", None)
            embed.add_field(name="Peso", value=peso, inline=True)
            embed.add_field(name="Altura", value=altura, inline=True)
            embed.add_field(name="Tipo sanguíneo", value=tipo_sanguineo, inline=True)
            embed.add_field(name="Cor favorita", value=cor, inline=False)


        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
