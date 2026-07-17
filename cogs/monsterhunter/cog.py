"""
🩸 Orquestração: rede, preferências de fonte por servidor e comandos do Discord.
"""

import os
import json
import aiohttp
import asyncio
from discord.ext import commands

from ..views import Paginator
from . import parser
from .data import WIKI_SOURCES, DEFAULT_SOURCE, PREF_FILE, SHORTCUTS


class MonsterHunter(commands.Cog):
    """comandos pra caçar monstros comigo na escuridão"""

    def __init__(self, bot):
        self.bot = bot
        self._utils_cache = None
        self._preferences = self._load_preferences()

    @property
    def utils(self):
        """cache utils para gerar os embeds na estética certa"""
        if not self._utils_cache:
            self._utils_cache = self.bot.get_cog('utils')
        return self._utils_cache

    def _make_embed(self, title, description, **kwargs):
        """helper pra criar embeds rapidamente no padrão nyxie"""
        return self.utils.base_embed(title, description, **kwargs)

    # ────────────────────────────────────────────────────────────────
    # 💾  PREFERÊNCIA DE FONTE POR SERVIDOR
    # ────────────────────────────────────────────────────────────────

    def _load_preferences(self):
        try:
            with open(PREF_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_preferences(self):
        os.makedirs(os.path.dirname(PREF_FILE), exist_ok=True)
        with open(PREF_FILE, "w", encoding="utf-8") as f:
            json.dump(self._preferences, f, indent=2, ensure_ascii=False)

    def _get_fonte_atual(self, jogo, guild_id):
        chave = f"{jogo}:{guild_id}"
        fonte = self._preferences.get(chave, DEFAULT_SOURCE)
        if fonte not in WIKI_SOURCES.get(jogo, {}):
            fonte = DEFAULT_SOURCE
        return fonte

    async def _trocar_fonte(self, ctx, jogo, fonte):
        fontes_disponiveis = WIKI_SOURCES.get(jogo, {})

        if len(fontes_disponiveis) <= 1:
            return await ctx.send(embed=self._make_embed(
                "sem opções...",
                f"o `!{jogo}` só tem uma fonte disponível por enquanto: **Fextralife** 🖤"
            ))

        guild_id = ctx.guild.id if ctx.guild else 0

        if not fonte:
            atual = self._get_fonte_atual(jogo, guild_id)
            lista = "\n".join(
                f"{'➤' if chave == atual else ' '} `{chave}` — {cfg['label']}"
                for chave, cfg in fontes_disponiveis.items()
            )
            return await ctx.send(embed=self._make_embed(
                f"fontes do {jogo}",
                f"fonte atual: `{atual}`\n\n{lista}\n\nuso: `!{jogo} wiki <fonte>`"
            ))

        fonte = fonte.lower().strip()
        if fonte not in fontes_disponiveis:
            opcoes = ", ".join(f"`{k}`" for k in fontes_disponiveis.keys())
            return await ctx.send(embed=self._make_embed(
                "fonte desconhecida...",
                f"não conheço a fonte `{fonte}`... as opções são: {opcoes}"
            ))

        chave = f"{jogo}:{guild_id}"
        self._preferences[chave] = fonte
        self._save_preferences()

        await ctx.send(embed=self._make_embed(
            "fonte alterada 🖤",
            f"a partir de agora, `!{jogo}` vai caçar informações direto da **{fontes_disponiveis[fonte]['label']}**..."
        ))

    # ────────────────────────────────────────────────────────────────
    # 🌐  REDE
    # ────────────────────────────────────────────────────────────────

    async def check_link(self, url):
        """verifica nas sombras se a página existe mesmo"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5, allow_redirects=True) as response:
                    return response.status == 200
        except Exception:
            return False

    async def get_fallback_link_api(self, query, url_base):
        """busca usando a api oficial e higieniza as chaves"""
        api_key = os.getenv("GOOGLE_API_KEY", "").strip(' "[]')
        cx = os.getenv("GOOGLE_SEARCH_CX", "").strip(' "[]')

        if not api_key or not cx:
            print("⚠️ [DEBUG NYXIE] Faltam as credenciais GOOGLE_API_KEY ou GOOGLE_SEARCH_CX no .env!")
            return None

        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cx, "q": query, "num": 3}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get("items", []):
                            link = item.get("link", "")
                            if url_base in link:
                                return link
        except Exception as e:
            print(f"❌ [DEBUG NYXIE] ERRO FATAL no request da API: {e}")

        return None

    def _build_url_candidates(self, termo, fonte_cfg):
        """gera as URLs candidatas a tentar direto, na ordem de prioridade.
        retorna lista vazia se a fonte não permitir adivinhação (ex: kiranico)."""
        if not fonte_cfg.get("guess_direct_url", True):
            return []

        domain = fonte_cfg["domain"]
        path_prefix = fonte_cfg.get("path_prefix", "")
        spacer = fonte_cfg["spacer"]

        if fonte_cfg.get("preserve_case"):
            base_termo = termo[:1].upper() + termo[1:] if termo else termo
        else:
            base_termo = termo.title()

        termo_url = base_termo.replace(" ", spacer)
        candidatos = [f"https://{domain}/{path_prefix}{termo_url}"]

        for sufixo in fonte_cfg.get("page_suffixes", []):
            candidatos.append(f"https://{domain}/{path_prefix}{termo_url}{sufixo}")

        termo_alt = termo.replace(" ", spacer)
        alt_url = f"https://{domain}/{path_prefix}{termo_alt}"
        if alt_url not in candidatos:
            candidatos.append(alt_url)

        return candidatos

    async def _dissecar_pagina_assincrono(self, url, acao, termo, parser_name, fonte_label):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    return None
                html = await response.text()

        return await asyncio.to_thread(
            parser.parse_page, html, url, acao, termo, parser_name, fonte_label, self._make_embed
        )

    # ────────────────────────────────────────────────────────────────
    # 🩸  ORQUESTRADOR DE COMANDOS
    # ────────────────────────────────────────────────────────────────

    async def _buscar_wiki(self, ctx, jogo: str, acao: str, termo: str):
        # 🕯️ intercepta o "wiki" ANTES de qualquer coisa — resolve na hora,
        # sem passar pelo fluxo de busca (era isso que tava travando em "caçando...")
        if acao and acao.lower() == "wiki":
            return await self._trocar_fonte(ctx, jogo, termo)

        acoes_conhecidas = {"scan"} | set(SHORTCUTS.keys())

        if not acao and not termo:
            lista_atalhos = " / ".join(f"`{nome}`" for nome in sorted(SHORTCUTS.keys()))
            fontes = WIKI_SOURCES.get(jogo, {})
            linha_fontes = ""
            if len(fontes) > 1:
                opcoes = " / ".join(f"`{k}`" for k in fontes.keys())
                linha_fontes = f"\nfontes disponíveis: {opcoes} — troque com `!{jogo} wiki <fonte>`"

            embed = self._make_embed(
                f"{jogo} help",
                f"uso correto:\n"
                f"`!{jogo} <nome da arma/item/monstro>` — dossiê completo direto das sombras\n"
                f"atalhos rápidos: {lista_atalhos}{linha_fontes}\n"
                f"exemplo: `!{jogo} rathalos` ou `!{jogo} weak rathalos`"
            )
            return await ctx.send(embed=embed)

        acao = acao.lower()

        if acao not in acoes_conhecidas:
            termo = f"{acao} {termo}" if termo else acao
            acao = "scan"

        if not termo:
            return await ctx.send(embed=self._make_embed(
                "cadê o alvo?",
                f"você pediu pra eu fazer um `{acao}`, mas esqueceu de me dar o **nome** da presa...\n"
                f"tenta assim, fofuxo: `!{jogo} {acao} rathalos` 🔪"
            ))

        guild_id = ctx.guild.id if ctx.guild else 0
        fonte_key = self._get_fonte_atual(jogo, guild_id)
        fonte_cfg = WIKI_SOURCES[jogo][fonte_key]

        msg = await ctx.send(embed=self._make_embed(
            "caçando...",
            f"injetando tentáculos na {fonte_cfg['label']} para extrair os segredos... 🩸"
        ))

        link_valido = None
        for candidato in self._build_url_candidates(termo, fonte_cfg):
            if await self.check_link(candidato):
                link_valido = candidato
                break

        if not link_valido:
            query = f"site:{fonte_cfg['domain']} {termo}"
            if fonte_cfg.get("search_hint"):
                query += f" {fonte_cfg['search_hint']}"
            link_valido = await self.get_fallback_link_api(query, fonte_cfg["domain"])

        if not link_valido:
            return await msg.edit(embed=self._make_embed(
                "não achei...",
                f"procurei nas sombras mas não encontrei `{termo}` na {fonte_cfg['label']}...\n\n"
                f"tem certeza do nome? (ou tenta outra fonte com `!{jogo} wiki`)"
            ))

        paginas = await self._dissecar_pagina_assincrono(
            link_valido, acao, termo, fonte_cfg["parser"], fonte_cfg["label"]
        )

        if isinstance(paginas, str) and paginas.startswith("categoria_errada::"):
            categorias_validas = paginas.split("::", 1)[1]
            return await msg.edit(embed=self._make_embed(
                "esquisito...",
                f"fofuxo, `{termo}` não parece se encaixar em: **{categorias_validas}**...\n"
                f"eu preciso disso pra usar o `{acao}` 🖤"
            ))

        if not paginas:
            return await msg.edit(embed=self._make_embed(
                "página vazia...",
                "achei o link, mas não consegui devorar nenhuma informação...\nos monstros devem ter comido tudo."
            ))

        view = Paginator(paginas)
        await msg.edit(embed=paginas[0], view=view)

    # ────────────────────────────────────────────────────────────────
    # 🎮  COMANDOS
    # ────────────────────────────────────────────────────────────────

    @commands.command(brief="busca na wiki do mhw")
    async def mhw(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhw", acao, termo)

    @commands.command(brief="busca na wiki do mhr")
    async def mhr(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhr", acao, termo)

    @commands.command(brief="busca na wiki do mhwilds")
    async def mhwilds(self, ctx, acao: str = None, *, termo: str = None):
        await self._buscar_wiki(ctx, "mhwilds", acao, termo)