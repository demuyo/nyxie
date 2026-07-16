import discord
import os
from discord.ext import commands
import aiohttp
import asyncio

class MonsterHunter(commands.Cog):
    """comandos pra caçar monstros comigo na escuridão"""

    def __init__(self, bot):
        self.bot = bot
        self._utils_cache = None

    @property
    def utils(self):
        """cache utils para gerar os embeds na estética certa"""
        if not self._utils_cache:
            self._utils_cache = self.bot.get_cog('utils')
        return self._utils_cache

    def _make_embed(self, title, description, **kwargs):
        """helper pra criar embeds rapidamente no padrão nyxie"""
        return self.utils.base_embed(title, description, **kwargs)

    async def check_link(self, url):
        """verifica nas sombras se a página existe mesmo"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5, allow_redirects=True) as response:
                    return response.status == 200
        except:
            return False

    async def get_fallback_link_api(self, query, url_base):
        """busca usando a api oficial e impiedosa do google"""
        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_SEARCH_CX")

        if not api_key or not cx:
            print("⚠️ [DEBUG NYXIE] Faltam as credenciais GOOGLE_API_KEY ou GOOGLE_SEARCH_CX no .env!")
            return None

        print(f"\n🔍 [DEBUG NYXIE] Caçando na API oficial do Google por: '{query}'")
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": 3  # puxamos os 3 primeiros resultados
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if not items:
                            print("⚠️ [DEBUG NYXIE] A API retornou sucesso, mas sem nenhum link útil.")
                            return None

                        for item in items:
                            link = item.get("link", "")
                            print(f"🔗 [DEBUG NYXIE] A API cuspiu o link: {link}")
                            if url_base in link:
                                print(f"✅ [DEBUG NYXIE] Link perfeito escolhido: {link}\n")
                                return link
                    else:
                        erro_txt = await response.text()
                        print(f"❌ [DEBUG NYXIE] Erro na API do Google (Status {response.status}): {erro_txt}\n")
        except Exception as e:
            print(f"❌ [DEBUG NYXIE] ERRO FATAL no request da API: {e}\n")
            
        return None

    async def _buscar_wiki(self, ctx, jogo: str, url_base: str, spacer: str, acao: str, termo: str):
        """lógica central que serve para todos os 3 jogos"""
        
        if not acao and not termo:
            embed = self._make_embed(
                f"{jogo} help", 
                f"uso correto:\n`!{jogo} <nome da arma/item>`\n`!{jogo} craft <nome da arma>`\n\n*se não digitar a ação, eu assumo que é wiki...*"
            )
            return await ctx.send(embed=embed)
        
        acao = acao.lower()
        acoes_conhecidas = ["wiki", "craft"]
        
        # mágica pra assumir que é wiki se não digitar
        if acao not in acoes_conhecidas:
            termo = f"{acao} {termo}" if termo else acao
            acao = "wiki" 

        if acao == "craft":
            return await ctx.send(embed=self._make_embed(
                "ainda não...", 
                "eu ainda tô aprendendo a ler as tabelas de craft... \ntenta procurar normal por enquanto, fofuxo 🖤"
            ))

        msg = await ctx.send(embed=self._make_embed("caçando...", "procurando nas sombras da wiki pra você... 🔪"))

        termo_formatado = termo.title()
        termo_url = termo_formatado.replace(" ", spacer)
        link_direto = f"https://{url_base}/{termo_url}"

        link_valido = None
        
        # 1º tentativa: link direto normal com title()
        if await self.check_link(link_direto):
            link_valido = link_direto
            print(f"✅ [DEBUG NYXIE] Link direto funcionou: {link_valido}")
        else:
            # 2º tentativa: link todo minúsculo/sem title() 
            link_alt = f"https://{url_base}/{termo.replace(' ', spacer)}"
            if await self.check_link(link_alt):
                link_valido = link_alt
                print(f"✅ [DEBUG NYXIE] Link alternativo funcionou: {link_valido}")
            else:
                # 3º tentativa: FALLBACK NA API DO GOOGLE
                print("⚠️ [DEBUG NYXIE] Tentativas diretas falharam. Acionando API do Google...")
                query = f"site:{url_base} {termo}"
                link_valido = await self.get_fallback_link_api(query, url_base)

        if link_valido:
            embed = self._make_embed(
                f"{jogo} {acao}", 
                f"achei pra você... \nespero que te ajude a matar uns monstros 🩸\n\n[clicar para abrir a página]({link_valido})"
            )
            embed.add_field(name="termo caçado", value=f"`{termo}`", inline=False)
            await msg.edit(embed=embed)
        else:
            await msg.edit(embed=self._make_embed(
                "não achei...", 
                f"procurei nas sombras mas não encontrei `{termo}` na wiki de {jogo}...\n\ntem certeza do nome?"
            ))

    @commands.command(brief="busca na wiki do mhw")
    async def mhw(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhw", "monsterhunterworld.wiki.fextralife.com", "+", acao, termo)

    @commands.command(brief="busca na wiki do mhr")
    async def mhr(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhr", "monsterhunterrise.wiki.fextralife.com", "+", acao, termo)

    @commands.command(brief="busca na wiki do mhwilds")
    async def mhwilds(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhwilds", "monsterhunterwilds.wiki.fextralife.com", "_", acao, termo)

async def setup(bot):
    await bot.add_cog(MonsterHunter(bot))