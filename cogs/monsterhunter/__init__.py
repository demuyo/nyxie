from .cog import MonsterHunter

async def setup(bot):
    await bot.add_cog(MonsterHunter(bot))