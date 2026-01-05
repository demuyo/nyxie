import os, asyncio, discord, requests, re, shutil, time, subprocess, tempfile, sys
from discord.ext import commands

# ==================== GERENCIAMENTO DE COOKIES ====================

def get_cookie_file(platform):
    """
    Cria arquivo de cookie a partir da variável de ambiente.
    Retorna o caminho do arquivo ou None se não encontrar.
    """
    env_var = f'{platform.upper()}_COOKIES'
    cookies_content = os.getenv(env_var)
    
    if not cookies_content:
        print(f"⚠️ Variável {env_var} não encontrada no ambiente")
        return None
    
    print(f"✅ Variável {env_var} encontrada ({len(cookies_content)} caracteres)")
    
    try:
        # Cria arquivo temporário que não será deletado automaticamente
        temp_dir = tempfile.gettempdir()
        cookie_path = os.path.join(temp_dir, f'cookies_{platform}_{os.getpid()}.txt')
        
        # Escreve conteúdo no arquivo
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        
        # Verifica se foi criado corretamente
        if os.path.exists(cookie_path):
            file_size = os.path.getsize(cookie_path)
            print(f"✅ Cookie file criado: {cookie_path} ({file_size} bytes)")
            
            # Debug: mostra primeiras linhas
            with open(cookie_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                print(f"📄 Primeira linha: {first_line[:80]}")
            
            return cookie_path
        else:
            print(f"❌ Erro: arquivo não foi criado em {cookie_path}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao criar cookie file: {e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_cookie_file(cookie_path):
    """Remove arquivo de cookie temporário"""
    if cookie_path and os.path.exists(cookie_path):
        try:
            os.remove(cookie_path)
            print(f"🗑️ Cookie temporário removido: {cookie_path}")
        except Exception as e:
            print(f"⚠️ Não conseguiu remover cookie: {e}")

# ==================== FUNÇÕES AUXILIARES ====================

def nome_seguro(texto, mensagem_id):
    """Gera nome de arquivo seguro removendo caracteres especiais"""
    if not texto:
        texto = "video"
    
    # Remove emojis
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]|"
        "[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|"
        "[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]",
        flags=re.UNICODE
    )
    texto = emoji_pattern.sub('', texto)
    
    # Remove caracteres especiais
    texto = re.sub(r'[^\w\s\-_]', '', texto)
    
    # Remove acentos
    acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c'
    }
    for acento, sem_acento in acentos.items():
        texto = texto.replace(acento, sem_acento)
    
    # Espaços → underscore
    texto = re.sub(r'\s+', '_', texto.strip())
    
    # Limita tamanho
    texto = texto[:80]
    if not texto:
        texto = "video"
    
    return f"{texto}_{mensagem_id}"

def detectar_ffmpeg():
    """Detecta FFmpeg no sistema (Windows e Linux)"""
    ffmpeg_paths = [
        'ffmpeg',  # PATH (Linux/Render)
        '/usr/bin/ffmpeg',  # Linux padrão
        '/usr/local/bin/ffmpeg',  # Linux alternativo
        r'C:\ffmpeg\bin\ffmpeg.exe',  # Windows
    ]
    
    for path in ffmpeg_paths:
        if shutil.which(path) or os.path.exists(path):
            print(f"✅ FFmpeg encontrado: {path}")
            return path
    
    print("⚠️ FFmpeg não encontrado")
    return None

# ==================== DOWNLOAD PRINCIPAL ====================

def baixar_video(url, formato='mp4'):
    """
    Baixa vídeo/áudio usando yt-dlp com cookies do ambiente.
    Suporta YouTube, TikTok e outras plataformas.
    """
    import yt_dlp
    
    os.makedirs('downloads', exist_ok=True)
    
    # Detecta plataforma
    is_tiktok = 'tiktok.com' in url or 'vm.tiktok.com' in url
    is_youtube = 'youtube.com' in url or 'youtu.be' in url
    
    print(f"\n{'='*60}")
    print(f"🎬 Baixando: {url[:80]}")
    print(f"📦 Formato: {formato}")
    print(f"🌐 Plataforma: {'TikTok' if is_tiktok else 'YouTube' if is_youtube else 'Outra'}")
    print(f"{'='*60}\n")
    
    # ====== PREPARA COOKIES ======
    cookie_file = None
    
    if is_youtube:
        print("🍪 Procurando cookies do YouTube...")
        cookie_file = get_cookie_file('youtube')
        if cookie_file:
            print(f"✅ Usando cookies do YouTube: {cookie_file}")
        else:
            print("⚠️ YouTube sem cookies - alguns vídeos podem falhar")
    
    elif is_tiktok:
        print("🍪 Procurando cookies do TikTok...")
        cookie_file = get_cookie_file('tiktok')
        if cookie_file:
            print(f"✅ Usando cookies do TikTok: {cookie_file}")
        else:
            print("⚠️ TikTok sem cookies - pode não funcionar")
    
    # ====== DETECTA FFMPEG ======
    ffmpeg_cmd = detectar_ffmpeg()
    
    if not ffmpeg_cmd and formato in ['mp3', 'wav']:
        print("❌ FFmpeg necessário para conversão de áudio")
        cleanup_cookie_file(cookie_file)
        return False, "ffmpeg_necessario"
    
    # ====== CONFIGURAÇÃO YT-DLP ======
    ydl_opts = {
        'outtmpl': 'downloads/temp_%(title)s.%(ext)s',
        'quiet': False,  # Mostra progresso
        'no_warnings': False,  # Mostra avisos
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 10,
        'extractor_retries': 10,
        'socket_timeout': 30,
    }
    
    # Adiciona FFmpeg location
    if ffmpeg_cmd:
        ffmpeg_dir = os.path.dirname(ffmpeg_cmd) if os.path.dirname(ffmpeg_cmd) else None
        if ffmpeg_dir:
            ydl_opts['ffmpeg_location'] = ffmpeg_dir
            print(f"📂 FFmpeg location: {ffmpeg_dir}")
    
    # ====== ADICIONA COOKIES ======
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        print(f"🍪 Cookies configurados: {cookie_file}")
    
    # ====== HEADERS CUSTOMIZADOS ======
    ydl_opts['http_headers'] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
    }
    
    # ====== CONFIGURAÇÃO POR FORMATO ======
    if formato == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'prefer_ffmpeg': True,
        })
        print("🎵 Modo: Extração de áudio MP3 (192kbps)")
        
    elif formato == "wav":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }],
            'prefer_ffmpeg': True,
        })
        print("🎵 Modo: Extração de áudio WAV")
        
    else:  # mp4
        if is_tiktok:
            ydl_opts.update({
                'format': 'best',
                'merge_output_format': 'mp4',
            })
            print("📱 Modo: TikTok melhor qualidade")
        else:
            ydl_opts.update({
                'format': 'bestvideo[height<=720][vcodec^=avc]+bestaudio/best[height<=720]/best',
                'merge_output_format': 'mp4',
            })
            print("🎬 Modo: Vídeo MP4 (máx 720p, H.264)")
    
    # ====== DOWNLOAD ======
    try:
        print("\n📥 Iniciando download...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'video')
        
        print(f"\n✅ Download completo: {titulo}")
        
        # Aguarda arquivo ser liberado (Windows)
        time.sleep(2)
        
        # Limpa cookies
        cleanup_cookie_file(cookie_file)
        
        return True, titulo
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        print(f"\n❌ Erro de download: {error_msg}")
        
        # Diagnóstico específico
        if 'sign in' in error_msg.lower() or 'bot' in error_msg.lower():
            print("🔴 Erro: YouTube pedindo login - cookies inválidos ou expirados")
            print("💡 Solução: Atualize a variável YOUTUBE_COOKIES no Render")
        elif 'private' in error_msg.lower():
            print("🔴 Erro: Vídeo privado ou deletado")
        elif 'not available' in error_msg.lower():
            print("🔴 Erro: Vídeo não disponível na sua região")
        
        cleanup_cookie_file(cookie_file)
        return False, None
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        cleanup_cookie_file(cookie_file)
        return False, None

# ==================== CATBOX UPLOAD ====================

def upload_catbox_seguro(caminho, max_tentativas=3):
    """Upload pro Catbox com retry"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://catbox.moe/',
        'Origin': 'https://catbox.moe'
    }
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            tamanho = os.path.getsize(caminho) / (1024*1024)
            
            if tamanho > 200:
                print(f"❌ Arquivo muito grande: {tamanho:.1f}MB (limite: 200MB)")
                return None

            print(f"📤 Upload Catbox (tentativa {tentativa}/{max_tentativas})...")

            with open(caminho, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                r = requests.post(
                    'https://catbox.moe/user/api.php',
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=600
                )
            
            if r.status_code == 200:
                link = r.text.strip()
                if link.startswith('https://'):
                    print(f"✅ Upload completo: {link}")
                    return link
            
            print(f"⚠️ Tentativa {tentativa} falhou: HTTP {r.status_code}")
            
            if tentativa < max_tentativas:
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ Erro upload tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                time.sleep(5)
    
    return None

# ==================== DISCORD BOT ====================

class Downloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["dl", "download"],
        usage="[formato] (link)",
        brief="baixa vídeos e áudios",
        help="baixa de YouTube, TikTok e mais. Usa cookies do Render automaticamente."
    )
    async def baixar(self, ctx, formato_ou_url: str = None, *, url: str = None):
        """
        Baixa vídeos e áudios com autenticação via cookies.
        
        Plataformas suportadas:
        • YouTube (com cookies YOUTUBE_COOKIES)
        • TikTok (com cookies TIKTOK_COOKIES)
        • Instagram, Twitter, Reddit, etc
        
        Formatos: mp4, mp3, wav
        
        Uso:
        !baixar (link)
        !baixar mp3 (link)
        !dl wav (link)
        """
        utils = self.bot.get_cog('utils')
        
        # Detecta formato e URL
        formatos_validos = ["mp3", "mp4", "wav"]
        
        if url is None:
            url = formato_ou_url
            formato = "mp4"
        else:
            if formato_ou_url and formato_ou_url.lower() in formatos_validos:
                formato = formato_ou_url.lower()
            else:
                url = f"{formato_ou_url} {url}" if formato_ou_url else url
                formato = "mp4"
        
        if not url:
            embed = utils.base_embed("erro", "você precisa fornecer um link!")
            return await ctx.send(embed=embed)
        
        # ==================== LOADING ====================
        embed_loading = utils.base_embed("baixando", None)
        embed_loading.add_field(name="formato", value=f"`{formato.upper()}`", inline=True)
        embed_loading.add_field(name="cookies", value="✅ ativados", inline=True)
        msg = await ctx.send(embed=embed_loading)
        
        # ==================== DOWNLOAD ====================
        loop = asyncio.get_event_loop()
        sucesso, titulo = await loop.run_in_executor(None, baixar_video, url, formato)
        
        if not sucesso:
            embed_erro = utils.base_embed("erro", "não consegui baixar")
            
            if titulo == "ffmpeg_necessario":
                embed_erro.add_field(
                    name="ffmpeg não encontrado",
                    value="conversão de áudio requer ffmpeg instalado",
                    inline=False
                )
            else:
                embed_erro.add_field(
                    name="possíveis causas",
                    value="• vídeo privado/deletado\n• cookies expirados\n• região bloqueada\n• link inválido",
                    inline=False
                )
            
            return await msg.edit(embed=embed_erro)
        
        # Pega arquivo mais recente
        try:
            arquivos = [f for f in os.listdir('downloads') if os.path.isfile(f'downloads/{f}')]
            if not arquivos:
                raise FileNotFoundError
            arquivo = max(arquivos, key=lambda x: os.path.getctime(f'downloads/{x}'))
        except:
            embed_erro = utils.base_embed("erro", "arquivo não encontrado após download")
            return await msg.edit(embed=embed_erro)
        
        # Renomeia com nome seguro
        caminho_velho = f'downloads/{arquivo}'
        nome_novo = f"{nome_seguro(titulo, ctx.message.id)}.{formato}"
        caminho_novo = f'downloads/{nome_novo}'
        
        # Retry no rename
        for _ in range(3):
            try:
                os.rename(caminho_velho, caminho_novo)
                break
            except:
                await asyncio.sleep(1)
        
        tamanho_mb = round(os.path.getsize(caminho_novo) / (1024*1024), 2)
        
        # ==================== DISCORD (≤10MB) ====================
        LIMITE_DISCORD = 10
        
        if tamanho_mb <= LIMITE_DISCORD:
            try:
                embed_up = utils.base_embed("enviando", None)
                embed_up.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
                await msg.edit(embed=embed_up)
                
                file = discord.File(caminho_novo, filename=nome_novo)
                
                embed_final = utils.base_embed("download completo", f"**{titulo[:100]}**")
                embed_final.add_field(name="arquivo", value=f"`{nome_novo[:50]}`", inline=False)
                embed_final.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
                embed_final.add_field(name="formato", value=f"`{formato.upper()}`", inline=True)
                embed_final.add_field(name="cdn", value="discord", inline=True)
                embed_final.set_footer(text=f"por {ctx.author.name}")
                
                await msg.delete()
                await ctx.send(embed=embed_final, file=file)
                
                os.remove(caminho_novo)
                return
                
            except discord.HTTPException as e:
                print(f"❌ Discord upload falhou ({tamanho_mb}MB): {e}")
                try:
                    await msg.delete()
                except:
                    pass
                msg = await ctx.send(embed=utils.base_embed("enviando pro catbox", "arquivo grande demais pro discord"))
        
        # ==================== CATBOX (>10MB) ====================
        
        if tamanho_mb > 200:
            embed_grande = utils.base_embed("muito grande", f"**{titulo[:100]}**")
            embed_grande.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
            embed_grande.add_field(name="limite", value="`200MB`", inline=True)
            embed_grande.add_field(name="salvo em", value=f"`{caminho_novo}`", inline=False)
            return await msg.edit(embed=embed_grande)
        
        embed_catbox = utils.base_embed("enviando pro catbox", None)
        embed_catbox.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
        embed_catbox.add_field(name="aguarde", value="pode demorar...", inline=True)
        
        try:
            await msg.edit(embed=embed_catbox)
        except discord.NotFound:
            msg = await ctx.send(embed=embed_catbox)
        
        link = await loop.run_in_executor(None, upload_catbox_seguro, caminho_novo)
        
        if not link:
            embed_falha = utils.base_embed("upload falhou", f"**{titulo[:100]}**")
            embed_falha.add_field(name="tentativas", value="`3/3`", inline=True)
            embed_falha.add_field(name="salvo em", value=f"`{caminho_novo}`", inline=False)
            
            try:
                await msg.edit(embed=embed_falha)
            except:
                await ctx.send(embed=embed_falha)
            return
        
        # Embed final Catbox
        embed_final = utils.base_embed("download completo", f"**{titulo[:100]}**")
        embed_final.add_field(name="arquivo", value=f"`{nome_novo[:50]}`", inline=False)
        embed_final.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
        embed_final.add_field(name="formato", value=f"`{formato.upper()}`", inline=True)
        embed_final.add_field(name="cdn", value="catbox", inline=True)
        embed_final.add_field(name="download", value=f"**[CLIQUE AQUI]({link})**", inline=False)
        embed_final.set_footer(text=f"por {ctx.author.name} • catbox.moe")
        
        # Thumbnail YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            try:
                video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else url.split('/')[-1].split('?')[0]
                embed_final.set_thumbnail(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
            except:
                pass
        
        try:
            await msg.edit(embed=embed_final)
        except:
            await ctx.send(embed=embed_final)
        
        # Limpa
        try:
            os.remove(caminho_novo)
        except:
            pass

    @commands.command(usage="", brief="testa cookies configurados")
    @commands.is_owner()
    async def testcookies(self, ctx):
        """Verifica se os cookies estão configurados corretamente"""
        embed = discord.Embed(title="🍪 Status dos Cookies", color=0x00ff00)
        
        # Testa YouTube
        yt_cookie = get_cookie_file('youtube')
        if yt_cookie:
            size = os.path.getsize(yt_cookie)
            with open(yt_cookie, 'r') as f:
                lines = len(f.readlines())
            embed.add_field(
                name="YouTube", 
                value=f"✅ Configurado\n`{size} bytes, {lines} linhas`", 
                inline=False
            )
            cleanup_cookie_file(yt_cookie)
        else:
            embed.add_field(name="YouTube", value="❌ Não encontrado", inline=False)
        
        # Testa TikTok
        tt_cookie = get_cookie_file('tiktok')
        if tt_cookie:
            size = os.path.getsize(tt_cookie)
            with open(tt_cookie, 'r') as f:
                lines = len(f.readlines())
            embed.add_field(
                name="TikTok", 
                value=f"✅ Configurado\n`{size} bytes, {lines} linhas`", 
                inline=False
            )
            cleanup_cookie_file(tt_cookie)
        else:
            embed.add_field(name="TikTok", value="❌ Não encontrado", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(usage="", brief="lista arquivos salvos")
    async def arquivos(self, ctx):
        """Lista arquivos na pasta downloads"""
        utils = self.bot.get_cog('utils')
        
        if not os.path.exists('downloads') or not os.listdir('downloads'):
            embed = utils.base_embed("pasta vazia", "nenhum arquivo salvo")
            return await ctx.send(embed=embed)
        
        arquivos = sorted(os.listdir('downloads'), key=lambda x: os.path.getctime(f'downloads/{x}'), reverse=True)[:20]
        
        embed = utils.base_embed("arquivos", f"últimos {len(arquivos)}")
        lista = "\n".join([f"`{f[:50]}`" for f in arquivos])
        embed.add_field(name="downloads/", value=lista, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(usage="(nome)", brief="deleta um arquivo")
    async def deletar(self, ctx, *, nome):
        """Deleta arquivo específico"""
        caminho = f"downloads/{nome}"
        
        if os.path.exists(caminho):
            os.remove(caminho)
            await ctx.send(f"✅ deletado `{nome}`")
        else:
            await ctx.send("❌ arquivo não encontrado")

    @commands.command(aliases=["clrdl"], usage="", brief="limpa pasta downloads")
    async def limpardownloads(self, ctx):
        """Limpa todos os arquivos baixados"""
        await ctx.send("⚠️ apagar tudo? digite `sim` em 10s")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'sim'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
            shutil.rmtree('downloads')
            os.makedirs('downloads')
            await ctx.send("✅ tudo limpo!")
        except:
            await ctx.send("❌ cancelado")

    @commands.command()
    @commands.is_owner()
    async def debugenv(self, ctx):
        """Mostra variáveis de ambiente (CUIDADO - só owner!)"""
        import os
        
        embed = discord.Embed(title="🔍 Debug Variáveis de Ambiente", color=0xff9900)
        
        # Checa cookies
        yt_exists = 'YOUTUBE_COOKIES' in os.environ
        tt_exists = 'TIKTOK_COOKIES' in os.environ
        
        yt_len = len(os.getenv('YOUTUBE_COOKIES', ''))
        tt_len = len(os.getenv('TIKTOK_COOKIES', ''))
        
        embed.add_field(
            name="YOUTUBE_COOKIES",
            value=f"{'✅ Existe' if yt_exists else '❌ Não existe'}\n{yt_len} caracteres",
            inline=False
        )
        
        embed.add_field(
            name="TIKTOK_COOKIES",
            value=f"{'✅ Existe' if tt_exists else '❌ Não existe'}\n{tt_len} caracteres",
            inline=False
        )
        
        # Lista TODAS as variáveis (sem mostrar valores)
        all_vars = list(os.environ.keys())
        vars_text = "\n".join([f"• {var}" for var in all_vars if 'COOK' in var.upper() or 'YT' in var.upper() or 'TIK' in var.upper()])
        
        if vars_text:
            embed.add_field(name="Variáveis relacionadas", value=f"```{vars_text}```", inline=False)
        else:
            embed.add_field(name="Variáveis relacionadas", value="❌ Nenhuma encontrada", inline=False)
        
        embed.add_field(
            name="Total de variáveis",
            value=f"{len(all_vars)} variáveis no ambiente",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Downloader(bot))