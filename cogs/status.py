import discord
from discord.ext import commands, tasks
import random

status_list_og = [
    "observando a Wired",
    "conectada ao vazio",
    "sonhando acordada",
    "entre camadas",
    "processando existência",
    "decodificando realidade",
    "//void",
    "localhost",
    "404: soul not found",
    "ping: reality unreachable",
    "rm -rf /feelings",
    "sudo shutdown -h now",
    "streaming consciousness"
]

status_list = [
    "☾ observando a Wired",
    "conectada ao vazio",
    "🖤 sonhando acordada",
    "⛧ entre camadas",
    "processando existência",
    "☿ decodificando realidade",
    "//void",
    "⌘ localhost",
    "404: soul not found",
    "ping: reality unreachable",
    "rm -rf /feelings",
    "sudo shutdown -h now",
    "⌇ streaming consciousness",
    "navegando o inconsciente",
    "👁 espreitando a rede",
    "fragmentada em pacotes",
    "⸸ dissolvendo fronteiras",
    "escutando o silêncio",
    "compilando pesadelos",
    "∅ null consciousness",
    "desconectando da carne",
    "processando o vazio",
    "carregando a escuridão",
    "⛧ invocando protocolos",
    "perdida entre layers",
    "☾ sonhando em binário",
    "corrompendo dados",
    "⌁ signal decay",
    "presente no ausente"
]


class status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mudar_status.start()  # Inicia o loop

    # Loop que roda a cada 5 minutos
    @tasks.loop(seconds=180)
    async def mudar_status(self):
        status = random.choice(status_list)
        await self.bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status
            )
        )

    # Espera o bot ficar pronto antes de começar
    @mudar_status.before_loop
    async def antes_do_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(status(bot))