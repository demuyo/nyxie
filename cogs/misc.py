import discord, random
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # d20
    @commands.command(aliases=["dado"], brief="rola dados no formato xdy")
    async def roll(self, ctx, dice: str = "1d6"):
        """rola dados no formato xdy
        
        uso: !roll [quantidade]d[lados]
        exemplo: !roll
        exemplo: !roll 1d6
        exemplo: !roll 2d20
        exemplo: !roll 3d10
        """
        try:
            amount, sides = map(int, dice.lower().split('d'))
            results = [random.randint(1, sides) for _ in range(amount)]
            total = sum(results)
            await ctx.send(f"{results} = **{total}**")
        except:
            await ctx.send("❌ Formato: `1d6`, `2d20`...")

    # Escolher entre opções aleatórias
    @commands.command(aliases=["escolha", "escolher"], brief="escolhe aleatoriamente entre opções")
    async def choose(self, ctx, *opcoes):
        """escolhe aleatoriamente entre as opções fornecidas
        
        uso: !choose (opção1) (opção2) [opção3...]
        exemplo: !choose pizza hamburguer
        exemplo: !choose sim não talvez
        exemplo: !choose "opção 1" "opção 2"
        """
        if not opcoes:
            await ctx.send("Preciso de opções para poder escolher!")
        else:
            resultado = random.choice(opcoes)
            await ctx.send(f"⛧ {resultado}")
    
    # .
    @commands.command(name="8ball", brief="faça uma pergunta para a bola 8 mágica")
    async def eightball(self, ctx, *, pergunta=None):
        """faça uma pergunta para a bola 8 mágica
        
        uso: !8ball (pergunta)
        exemplo: !8ball vou passar no vestibular?
        exemplo: !8ball devo sair hoje?
        exemplo: !8ball ela gosta de mim?
        """
        if not pergunta:
            await ctx.send("❌ Faça uma pergunta!")
            return
        
        respostas = [
            "sim", "não", "talvez", "definitivamente",
            "sem dúvida", "não conte com isso",
            "as estrelas dizem que não", "melhor não te dizer agora",
            "⛧ the void says yes", "☾ the moon is uncertain"
        ]
        await ctx.send(f"{random.choice(respostas)}")

    # coinflip
    @commands.command(aliases=["moeda", "coinflip"], brief="joga uma moeda")
    async def coin(self, ctx):
        """joga uma moeda (cara ou coroa)
        
        uso: !coin
        exemplo: !coin
        exemplo: !moeda
        exemplo: !coinflip
        """
        resultado = random.choice(["☿️ cara", "⛧ coroa"])
        await ctx.send(f"{resultado}")

async def setup(bot):
    await bot.add_cog(Misc(bot))