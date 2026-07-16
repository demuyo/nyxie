from discord.ext import commands
import re, asyncio, aiohttp, os, json, discord
from googlesearch import search
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AIActions(commands.Cog):
    """Sistema de ações inteligentes da IA"""
    
    def __init__(self, bot):
        self.bot = bot
        self.search_cache = {}
        self.cache_ttl = 3600  
        
        self.intencoes = {
            'pesquisar': [
                r'(?:pesquis[ae]|procur[ae]|busca)(?:.*?(?:sobre|no google|pra mim)?)?[\s:]+(.+)',
                r' (?:mostra|fala|diz) (?:sobre )?(.+)',
                r'(?:que|quem|o que|oque) (?:é|e|foi|fez|são|sao) (.+)',
            ],
            'baixar': [
                # Captura URL + detecta formato de áudio
                r'(?:baixa|download).*?(?:audio|som|musica|música).*?(https?://[^\s]+)',
                r'(?:baixa|download).*?(https?://[^\s]+).*?(?:audio|som|musica|música)',
                # Padrão normal
                r'(?:baixa|download).*?(https?://[^\s]+)',
            ],
            'lembrar': [
                r'(?:lembra|anota|salva|guarda)(?:.*?)(?:de |que )?(.+)',
            ],
            'comandos_bot': [
                r'(?:mostra|lista|quais)(?:.*?)comandos',
            ],
            'clima': [
                r'(?:qual|como|quantos)(?:.*?)(?:está|hoje|tá)(?:clima|temperatura|tempo)(?:.*?)(em |de )?(.+)',
            ]
        }
    
    def detectar_intencao(self, mensagem):
        """Detecta intenção preservando case do link"""
        
        for intencao, padroes in self.intencoes.items():
            for padrao in padroes:
                match = re.search(padrao, mensagem, re.IGNORECASE)
                if match:
                    try:
                        conteudo = match.group(1).strip() if match.lastindex and match.group(1) else ""
                    except:
                        conteudo = ""
                    
                    if intencao != 'baixar':
                        conteudo = conteudo.replace('pra mim', '').replace('no google', '').strip()
                    
                    return intencao, conteudo
        
        return None, None
    
    def detectar_formato_audio(self, mensagem):
        """Detecta se quer WAV ou MP3"""
        msg_lower = mensagem.lower()
        
        if 'wav' in msg_lower:
            return 'wav'
        
        # Padrão: MP3
        return 'mp3'
    
    async def acao_pesquisar(self, ctx, query):
        """Pesquisa Google Custom Search"""
        if not query or len(query) < 3:
            return "pesquisar o que? fala direito po"
        
        # ====== CACHE ======
        cache_key = query.lower().strip()
        from time import time
        
        if cache_key in self.search_cache:
            resultado, timestamp = self.search_cache[cache_key]
            if time() - timestamp < self.cache_ttl:
                print(f"⚡ Cache hit: '{query}'")
                return resultado
        
        try:
            print(f"🔍 Pesquisando: '{query}'")
            
            from googleapiclient.discovery import build
            
            API_KEY = os.getenv('GOOGLE_API_KEY')
            CSE_ID = os.getenv('GOOGLE_CSE_ID')
            
            loop = asyncio.get_event_loop()
            
            def buscar():
                service = build("customsearch", "v1", developerKey=API_KEY)
                result = service.cse().list(q=query, cx=CSE_ID, num=5, lr='lang_pt').execute()
                return result.get('items', [])
            
            resultados = await loop.run_in_executor(None, buscar)
            
            if resultados:
                links = []
                for r in resultados[:5]:
                    titulo = r.get('title', 'Sem título')[:50]
                    url = r.get('link', '')
                    snippet = r.get('snippet', '')[:80]
                    links.append(f"• **{titulo}**\n  {snippet}...\n  <{url}>")
                
                resposta = f"achei isso sobre **{query}**:\n\n" + "\n\n".join(links)
                
                # ====== SALVA NO CACHE ======
                self.search_cache[cache_key] = (resposta, time())
                
                return resposta
            else:
                return f"não achei nada sobre '{query}'"
                    
        except Exception as e:
            print(f"❌ Erro: {e}")
            return "deu erro na pesquisa"
        
    async def acao_baixar(self, ctx, url_e_contexto):
        """Baixa vídeo/áudio detectando formato automaticamente"""
        
        # Extrai só a URL (remove texto ao redor)
        url_match = re.search(r'(https?://[^\s]+)', url_e_contexto)
        if not url_match:
            return "manda o link direto po"
        
        url = url_match.group(1)
        
        downloader = self.bot.get_cog('Downloader')
        if not downloader:
            return "sistema offline, usa `!dl [link]`"
        
        try:
            # Detecta se quer áudio
            mensagem_original = ctx.message.content.lower()
            
            if any(palavra in mensagem_original for palavra in ['audio', 'som', 'musica', 'música', 'mp3', 'wav']):
                # Detecta WAV ou MP3
                formato = self.detectar_formato_audio(mensagem_original)
                print(f"🎵 Detectado: áudio {formato.upper()}")
                await downloader.baixar(ctx, formato, url=url)
            else:
                # Vídeo padrão
                print(f"🎬 Detectado: vídeo MP4")
                await downloader.baixar(ctx, url)
            
            return None
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            
            erro_str = str(e)
            if "Video unavailable" in erro_str:
                return "vídeo indisponível ou privado"
            elif "Private video" in erro_str:
                return "vídeo é privado"
            else:
                return "deu erro ao baixar"
        
    async def acao_lembrar(self, ctx, conteudo):
        """Salva lembrete"""
        if not conteudo or len(conteudo) < 3:
            return "lembrar de que?"
        
        user_id = str(ctx.author.id)
        lembretes_file = "lembretes.json"
        
        if os.path.exists(lembretes_file):
            with open(lembretes_file, 'r', encoding='utf-8') as f:
                lembretes = json.load(f)
        else:
            lembretes = {}
        
        if user_id not in lembretes:
            lembretes[user_id] = []
        
        lembretes[user_id].append({
            'conteudo': conteudo,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        with open(lembretes_file, 'w', encoding='utf-8') as f:
            json.dump(lembretes, f, indent=2, ensure_ascii=False)
        
        return f"anotado! '{conteudo}'\n\nvocê tem {len(lembretes[user_id])} lembrete(s)"
    
    async def acao_comandos_bot(self, ctx, filtro):
        """Lista comandos"""
        comandos = []
        for cmd in self.bot.commands:
            if not cmd.hidden and not cmd.name.startswith('_'):
                aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                comandos.append(f"`!{cmd.name}`{aliases}")
        
        if filtro:
            comandos = [c for c in comandos if filtro.lower() in c.lower()]
        
        if comandos:
            lista = ", ".join(comandos[:20])
            extra = f"\n\n...e mais {len(comandos) - 20}" if len(comandos) > 20 else ""
            return f"**comandos:**\n{lista}{extra}\n\nusa `!help [comando]`"
        else:
            return "não achei esse comando"
    
    async def acao_clima(self, ctx, cidade):
        """Busca clima"""
        if not cidade or len(cidade) < 2:
            return "clima de onde?"
        
        cidade = cidade.replace('em ', '').replace('de ', '').strip()
        
        try:
            url = f"https://wttr.in/{cidade}?format=%l:+%C+%t+(sensação:+%f)+|+umidade:+%h"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        texto = await resp.text()
                        texto = texto.strip()
                        
                        if "Unknown location" in texto or not texto:
                            return f"não achei '{cidade}'"
                        
                        return f"**clima:** {texto}"
                    else:
                        return "erro ao buscar clima"
                        
        except Exception as e:
            print(f"❌ Erro clima: {e}")
            return "erro ao buscar clima"
    
    @commands.command(aliases=["lembretes"])
    async def minhasnotas(self, ctx):
        """Mostra lembretes"""
        utils = self.bot.get_cog('utils')
        user_id = str(ctx.author.id)
        lembretes_file = "lembretes.json"
        
        if not os.path.exists(lembretes_file):
            return await ctx.send(embed=utils.base_embed("sem lembretes", "você não tem nada anotado"))
        
        with open(lembretes_file, 'r', encoding='utf-8') as f:
            lembretes = json.load(f)
        
        if user_id not in lembretes or not lembretes[user_id]:
            return await ctx.send(embed=utils.base_embed("sem lembretes", "você não tem nada anotado"))
        
        notas = lembretes[user_id][-10:]
        embed = utils.base_embed(f"lembretes", f"total: {len(lembretes[user_id])}")
        
        for i, nota in enumerate(reversed(notas), 1):
            timestamp = datetime.fromisoformat(nota['timestamp'])
            embed.add_field(
                name=f"{i}. {nota['conteudo'][:50]}",
                value=f"<t:{int(timestamp.timestamp())}:R>",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def apagarlembretes(self, ctx):
        """Apaga todos os lembretes"""
        user_id = str(ctx.author.id)
        lembretes_file = "lembretes.json"
        
        if not os.path.exists(lembretes_file):
            return await ctx.send("você não tem lembretes")
        
        with open(lembretes_file, 'r', encoding='utf-8') as f:
            lembretes = json.load(f)
        
        if user_id in lembretes:
            total = len(lembretes[user_id])
            del lembretes[user_id]
            
            with open(lembretes_file, 'w', encoding='utf-8') as f:
                json.dump(lembretes, f, indent=2, ensure_ascii=False)
            
            await ctx.send(f"✅ apaguei {total} lembrete(s)")
        else:
            await ctx.send("você não tem lembretes")
    
    async def executar_acao(self, message, intencao, conteudo):
        """Executa ação"""
        ctx = await self.bot.get_context(message)
        
        acoes = {
            'pesquisar': self.acao_pesquisar,
            'baixar': self.acao_baixar,
            'lembrar': self.acao_lembrar,
            'comandos_bot': self.acao_comandos_bot,
            'clima': self.acao_clima,
        }
        
        if intencao in acoes:
            return await acoes[intencao](ctx, conteudo)
        
        return None
    
    async def processar_mensagem(self, message, mensagem_texto):
        """Processa mensagem"""
        intencao, conteudo = self.detectar_intencao(mensagem_texto)
        
        if intencao:
            print(f"🎯 {intencao} | '{conteudo}'")
            resultado = await self.executar_acao(message, intencao, conteudo)
            return intencao, resultado
        
        return None, None
    
    @commands.command(
        aliases=["pesquisar", "google", "buscar"],
        usage="(termo)",
        brief="pesquisa algo no google",
        help="faz uma pesquisa no google e retorna os primeiros resultados."
    )
    async def search(self, ctx, *, query: str = None):
        """
        pesquisa algo no google.
        
        faz uma busca e retorna os 5 primeiros resultados
        com título, descrição e link.
        
        uso:
        !search (termo)
        
        exemplo:
        !search python discord bot
        !pesquisar como fazer bolo
        !google bad apple touhou
        !buscar notícias do dia
        """
        if not query or len(query) < 3:
            await ctx.send("pesquisar o que? fala direito po")
            return
        
        async with ctx.typing():
            resultado = await self.acao_pesquisar(ctx, query)
            await ctx.send(resultado)

async def setup(bot):
    await bot.add_cog(AIActions(bot))