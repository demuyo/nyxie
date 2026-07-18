import os, asyncio, discord, requests, re, shutil, time, subprocess, tempfile, sys
from discord.ext import commands

# ==================== GERENCIAMENTO DE COOKIES ====================

def get_cookie_file(platform):
    """
    Cria arquivo de cookie a partir da variável de ambiente.
    """
    env_var = f'{platform.upper()}_COOKIES'
    cookies_content = os.getenv(env_var)
    
    if not cookies_content:
        print(f"⚠️ Variável {env_var} não encontrada no ambiente")
        return None
    
    print(f"✅ Variável {env_var} encontrada")
    
    try:
        temp_dir = tempfile.gettempdir()
        cookie_path = os.path.join(temp_dir, f'cookies_{platform}_{os.getpid()}.txt')
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        
        if os.path.exists(cookie_path):
            return cookie_path
        return None
            
    except Exception as e:
        print(f"❌ Erro ao criar cookie file: {e}")
        return None

def cleanup_cookie_file(cookie_path):
    if cookie_path and os.path.exists(cookie_path):
        try:
            os.remove(cookie_path)
        except Exception:
            pass

# ==================== FUNÇÕES AUXILIARES ====================

def nome_seguro(texto, mensagem_id):
    """Gera nome de arquivo seguro removendo caracteres especiais"""
    if not texto:
        texto = "video"
    
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff]|[\u2600-\u26FF]|[\u2700-\u27BF]|"
        "[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|"
        "[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]",
        flags=re.UNICODE
    )
    texto = emoji_pattern.sub('', texto)
    texto = re.sub(r'[^\w\s\-_]', '', texto)
    
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
    
    texto = re.sub(r'\s+', '_', texto.strip())
    texto = texto[:80]
    if not texto:
        texto = "video"
    
    return f"{texto}_{mensagem_id}"

def detectar_ffmpeg():
    ffmpeg_paths = ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', r'C:\ffmpeg\bin\ffmpeg.exe']
    for path in ffmpeg_paths:
        if shutil.which(path) or os.path.exists(path):
            return path
    return None

def converter_arquivo(caminho_entrada, formato_saida):
    ffmpeg = detectar_ffmpeg()
    if not ffmpeg:
        return False, "FFmpeg não instalado"
    
    nome_base = os.path.splitext(os.path.basename(caminho_entrada))[0]
    caminho_saida = f"downloads/{nome_base}_convertido.{formato_saida}"
    
    configs = {
        'mp4': ['-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '192k'],
        'mp3': ['-vn', '-ar', '44100', '-ac', '2', '-b:a', '320k'],
        'wav': ['-vn', '-ar', '44100', '-ac', '2'],
        'aac': ['-vn', '-c:a', 'aac', '-b:a', '256k'],
        'flac': ['-vn', '-c:a', 'flac'],
        'webm': ['-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', '-c:a', 'libopus'],
        'avi': ['-c:v', 'libx264', '-c:a', 'mp3', '-b:a', '192k'],
        'mkv': ['-c:v', 'libx264', '-c:a', 'aac'],
        'mov': ['-c:v', 'libx264', '-c:a', 'aac'],
        'gif': ['-vf', 'fps=15,scale=480:-1:flags=lanczos', '-loop', '0'],
    }
    
    params = configs.get(formato_saida, ['-c', 'copy'])
    cmd = [ffmpeg, '-i', caminho_entrada, '-y'] + params + [caminho_saida]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600, text=True)
        if result.returncode == 0 and os.path.exists(caminho_saida):
            return True, caminho_saida
        return False, "Erro na conversão"
    except Exception as e:
        return False, str(e)

def upload_catbox_seguro(caminho, max_tentativas=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://catbox.moe/',
        'Origin': 'https://catbox.moe'
    }
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            tamanho = os.path.getsize(caminho) / (1024*1024)
            if tamanho > 200:
                return None

            with open(caminho, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                r = requests.post('https://catbox.moe/user/api.php', data=data, files=files, headers=headers, timeout=600)
            
            if r.status_code == 200:
                link = r.text.strip()
                if link.startswith('https://'):
                    return link
            if tentativa < max_tentativas:
                time.sleep(3)
        except Exception:
            if tentativa < max_tentativas:
                time.sleep(5)
    return None

# ==================== ROTEADORES DE DOWNLOAD ====================

def baixar_youtube_pytubefix(url, formato):
    from pytubefix import YouTube
    import pytubefix.exceptions
    os.makedirs('downloads', exist_ok=True)
    ffmpeg = detectar_ffmpeg()
    
    try:
        yt = YouTube(url)
        titulo = yt.title
        print(f"🎬 [Pytubefix] Baixando: {titulo}")
        
        if formato in ['mp3', 'wav']:
            stream = yt.streams.get_audio_only()
            out_file = stream.download(output_path='downloads')
            sucesso, conv_file = converter_arquivo(out_file, formato)
            if sucesso:
                os.remove(out_file)
            return True, titulo
        else:
            # Lógica de Limite de Resolução (1080p default)
            target_res = 1080
            if formato.endswith('p') and formato[:-1].isdigit():
                target_res = int(formato[:-1])
            elif formato == '4k':
                target_res = 2160
                
            if ffmpeg:
                video_streams = yt.streams.filter(adaptive=True, type="video", file_extension='mp4')
                
                best_stream = None
                best_res_val = 0
                
                # Caça a maior resolução que não ultrapasse o target_res (Ex: 1080)
                for s in video_streams:
                    if not s.resolution: continue
                    res_val = int(s.resolution.replace('p', ''))
                    if res_val <= target_res and res_val > best_res_val:
                        best_res_val = res_val
                        best_stream = s
                
                video_stream = best_stream or video_streams.order_by('resolution').desc().first()
                audio_stream = yt.streams.get_audio_only()
                
                if video_stream and audio_stream:
                    print(f"🔄 Fundindo Vídeo ({video_stream.resolution}) e Áudio separados...")
                    v_file = video_stream.download(output_path='downloads', filename=f'v_temp_{int(time.time())}.mp4')
                    a_file = audio_stream.download(output_path='downloads', filename=f'a_temp_{int(time.time())}.m4a')
                    
                    out_file = os.path.join('downloads', f"yt_merged_{int(time.time())}.mp4")
                    
                    cmd = [ffmpeg, '-i', v_file, '-i', a_file, '-c:v', 'copy', '-c:a', 'aac', '-y', out_file]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    os.remove(v_file)
                    os.remove(a_file)
                    return True, titulo
            
            # Fallback se não tiver ffmpeg
            stream = yt.streams.get_highest_resolution()
            stream.download(output_path='downloads')
            return True, titulo
            
    except pytubefix.exceptions.AgeRestrictedError:
        return False, "Vídeo com restrição de idade no YouTube"
    except Exception as e:
        print(f"❌ [Pytubefix] Erro: {e}")
        return False, f"Pytubefix: {str(e)}"

def baixar_ytdlp(url, formato):
    """Fallback usando yt-dlp para TikTok, Instagram, etc."""
    import yt_dlp
    os.makedirs('downloads', exist_ok=True)
    
    is_tiktok = 'tiktok.com' in url or 'vm.tiktok.com' in url
    is_instagram = 'instagram.com' in url
    
    cookie_file = None
    if is_tiktok:
        cookie_file = get_cookie_file('tiktok')
    elif is_instagram:
        cookie_file = get_cookie_file('instagram')
        
    ffmpeg_cmd = detectar_ffmpeg()
    if not ffmpeg_cmd and formato in ['mp3', 'wav']:
        cleanup_cookie_file(cookie_file)
        return False, "ffmpeg_necessario"
        
    ydl_opts = {
        'outtmpl': 'downloads/temp_%(title)s.%(ext)s',
        'quiet': False,
        'retries': 5,
        'socket_timeout': 30,
    }
    
    if ffmpeg_cmd:
        ffmpeg_dir = os.path.dirname(ffmpeg_cmd) if os.path.dirname(ffmpeg_cmd) else None
        if ffmpeg_dir:
            ydl_opts['ffmpeg_location'] = ffmpeg_dir
            
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        
    ydl_opts['http_headers'] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    if formato == "mp3":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]})
    elif formato == "wav":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]})
    else:
        # Se for um formato específico numérico repassado pelo comando
        if formato.endswith('p') and formato[:-1].isdigit():
            altura = int(formato[:-1])
            ydl_opts.update({'format': f'bestvideo[height<={altura}]+bestaudio/best', 'merge_output_format': 'mp4'})
        else:
            ydl_opts.update({'format': 'best', 'merge_output_format': 'mp4'})
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'video')
        time.sleep(2)
        cleanup_cookie_file(cookie_file)
        return True, titulo
    except Exception as e:
        cleanup_cookie_file(cookie_file)
        return False, str(e)

# ==================== O CÉREBRO: ROUTER ====================

def baixar_video_router(url, formato='mp4'):
    print(f"\n{'='*60}\n🎬 Baixando: {url[:80]}\n📦 Formato: {formato}\n{'='*60}\n")
    
    # Rota 1: YouTube -> Pytubefix (Controlando a qualidade 1080p)
    if 'youtube.com' in url or 'youtu.be' in url:
        return baixar_youtube_pytubefix(url, formato)
        
    # Rota 2: Todo o resto (Instagram, TikTok, Twitter) -> YT-DLP
    else:
        return baixar_ytdlp(url, formato)

# ==================== DISCORD BOT ====================

class Downloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["dl", "download"],
        usage="[formato/resolução] (link)",
        brief="baixa vídeos e áudios",
        help="baixa de YouTube (limitado a 1080p), Instagram, TikTok e mais (com cookies).\nFormatos: mp4, mp3, wav, 480p, 720p, 1080p, 4k"
    )
    async def baixar(self, ctx, formato_ou_url: str = None, *, url: str = None):
        utils = self.bot.get_cog('utils')
        # Adicionado o mapa das resoluções aceitas
        formatos_validos = ["mp3", "mp4", "wav", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "4k"]
        
        if url is None:
            url = formato_ou_url
            formato = "mp4" # Padrão agora é o MP4 normal, o limitador 1080p está na função router
        else:
            if formato_ou_url and formato_ou_url.lower() in formatos_validos:
                formato = formato_ou_url.lower()
            else:
                url = f"{formato_ou_url} {url}" if formato_ou_url else url
                formato = "mp4"
        
        if not url:
            embed = utils.base_embed("erro", "você precisa fornecer um link!")
            return await ctx.send(embed=embed)
        
        embed_loading = utils.base_embed("baixando", None)
        embed_loading.add_field(name="qualidade/formato", value=f"`{formato.upper()}`", inline=True)
        embed_loading.add_field(name="status", value="procurando...", inline=True)
        msg = await ctx.send(embed=embed_loading)
        
        loop = asyncio.get_event_loop()
        sucesso, titulo = await loop.run_in_executor(None, baixar_video_router, url, formato)
        
        if not sucesso:
            embed_erro = utils.base_embed("erro", "não consegui baixar")
            if titulo == "ffmpeg_necessario":
                embed_erro.add_field(name="ffmpeg não encontrado", value="conversão de áudio ou vídeo requer ffmpeg", inline=False)
            else:
                embed_erro.add_field(name="possíveis causas", value=f"• Link privado ou restrito\n• Limite de requisição da rede\n• Erro interno: `{titulo[:200]}`", inline=False)
            return await msg.edit(embed=embed_erro)
        
        try:
            arquivos = [f for f in os.listdir('downloads') if os.path.isfile(f'downloads/{f}')]
            if not arquivos:
                raise FileNotFoundError
            arquivo = max(arquivos, key=lambda x: os.path.getctime(f'downloads/{x}'))
        except:
            embed_erro = utils.base_embed("erro", "arquivo não encontrado nas sombras após o download")
            return await msg.edit(embed=embed_erro)
        
        caminho_velho = f'downloads/{arquivo}'
        # Usa sempre mp4 para vídeos, mesmo se o usuário digitou '480p'
        ext_final = "mp4" if formato.endswith('p') or formato == '4k' else formato
        nome_novo = f"{nome_seguro(titulo, ctx.message.id)}.{ext_final}"
        caminho_novo = f'downloads/{nome_novo}'
        
        for _ in range(3):
            try:
                os.rename(caminho_velho, caminho_novo)
                break
            except:
                await asyncio.sleep(1)
        
        tamanho_mb = round(os.path.getsize(caminho_novo) / (1024*1024), 2)
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
            except discord.HTTPException:
                try: await msg.delete() 
                except: pass
                msg = await ctx.send(embed=utils.base_embed("enviando pro catbox", "arquivo grande demais pro discord"))
        
        if tamanho_mb > 200:
            embed_grande = utils.base_embed("muito grande", f"**{titulo[:100]}**")
            embed_grande.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
            embed_grande.add_field(name="limite", value="`200MB`", inline=True)
            return await msg.edit(embed=embed_grande)
        
        embed_catbox = utils.base_embed("enviando pro catbox", None)
        embed_catbox.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
        embed_catbox.add_field(name="aguarde", value="pode demorar...", inline=True)
        
        try: await msg.edit(embed=embed_catbox)
        except discord.NotFound: msg = await ctx.send(embed=embed_catbox)
        
        link = await loop.run_in_executor(None, upload_catbox_seguro, caminho_novo)
        
        if not link:
            embed_falha = utils.base_embed("upload falhou", f"**{titulo[:100]}**")
            embed_falha.add_field(name="tentativas", value="`3/3`", inline=True)
            try: await msg.edit(embed=embed_falha)
            except: await ctx.send(embed=embed_falha)
            return
        
        embed_final = utils.base_embed("download completo", f"**{titulo[:100]}**")
        embed_final.add_field(name="arquivo", value=f"`{nome_novo[:50]}`", inline=False)
        embed_final.add_field(name="tamanho", value=f"`{tamanho_mb}MB`", inline=True)
        embed_final.add_field(name="formato", value=f"`{formato.upper()}`", inline=True)
        embed_final.add_field(name="cdn", value="catbox", inline=True)
        embed_final.add_field(name="download", value=f"**[CLIQUE AQUI]({link})**", inline=False)
        embed_final.set_footer(text=f"por {ctx.author.name} • catbox.moe")
        
        if 'youtube.com' in url or 'youtu.be' in url:
            try:
                video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else url.split('/')[-1].split('?')[0]
                embed_final.set_thumbnail(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
            except: pass
        
        try: await msg.edit(embed=embed_final)
        except: await ctx.send(embed=embed_final)
        
        try: os.remove(caminho_novo)
        except: pass

    @commands.command(aliases=["cv", "convert"], usage="(formato) + anexo", brief="converte arquivos de mídia")
    async def converter(self, ctx, formato: str = None):
        utils = self.bot.get_cog('utils')
        formatos_validos = ['mp4', 'mp3', 'wav', 'avi', 'mkv', 'mov', 'webm', 'gif', 'aac', 'flac']
        
        if not formato or formato.lower() not in formatos_validos:
            embed = utils.base_embed("formato inválido", None)
            embed.add_field(name="uso", value="`!converter mp4` (+ anexo)\n`!cv mp3` (+ anexo)", inline=False)
            return await ctx.send(embed=embed)
        
        formato = formato.lower()
        if not ctx.message.attachments:
            embed = utils.base_embed("nenhum arquivo anexado", None)
            return await ctx.send(embed=embed)
        
        anexo = ctx.message.attachments[0]
        tamanho_mb = anexo.size / (1024*1024)
        if tamanho_mb > 200:
            embed = utils.base_embed("arquivo muito grande", None)
            return await ctx.send(embed=embed)
        
        embed_loading = utils.base_embed("convertendo", None)
        msg = await ctx.send(embed=embed_loading)
        
        os.makedirs('downloads', exist_ok=True)
        nome_original = nome_seguro(os.path.splitext(anexo.filename)[0], ctx.message.id)
        extensao_original = os.path.splitext(anexo.filename)[1]
        caminho_entrada = f"downloads/{nome_original}{extensao_original}"
        
        try:
            await anexo.save(caminho_entrada)
        except Exception as e:
            return await msg.edit(embed=utils.base_embed("erro", str(e)))
        
        loop = asyncio.get_event_loop()
        sucesso, resultado = await loop.run_in_executor(None, converter_arquivo, caminho_entrada, formato)
        
        try: os.remove(caminho_entrada)
        except: pass
        
        if not sucesso:
            return await msg.edit(embed=utils.base_embed("erro na conversão", resultado))
        
        caminho_saida = resultado
        tamanho_final_mb = round(os.path.getsize(caminho_saida) / (1024*1024), 2)
        nome_final = os.path.basename(caminho_saida)
        
        LIMITE_DISCORD = 10
        if tamanho_final_mb <= LIMITE_DISCORD:
            try:
                file = discord.File(caminho_saida, filename=nome_final)
                embed_final = utils.base_embed("conversão completa", f"**{anexo.filename}**")
                await msg.delete()
                await ctx.send(embed=embed_final, file=file)
                os.remove(caminho_saida)
                return
            except discord.HTTPException:
                msg = await ctx.send(embed=utils.base_embed("enviando pro catbox", "arquivo muito grande"))
        
        if tamanho_final_mb > 200:
            return await msg.edit(embed=utils.base_embed("arquivo gigante", "passou de 200mb"))
        
        link = await loop.run_in_executor(None, upload_catbox_seguro, caminho_saida)
        if not link:
            return await msg.edit(embed=utils.base_embed("upload falhou", None))
            
        embed_final = utils.base_embed("conversão completa", f"**{anexo.filename}**")
        embed_final.add_field(name="download", value=f"**[CLIQUE AQUI]({link})**", inline=False)
        try: await msg.edit(embed=embed_final)
        except: await ctx.send(embed=embed_final)
        try: os.remove(caminho_saida)
        except: pass

    @commands.command(aliases=["clrdl"], usage="", brief="limpa pasta downloads")
    async def limpardownloads(self, ctx):
        await ctx.send("⚠️ apagar tudo? digite `sim` em 10s")
        def check(m): return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'sim'
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
            shutil.rmtree('downloads')
            os.makedirs('downloads')
            await ctx.send("✅ tudo limpo!")
        except:
            await ctx.send("❌ cancelado")

async def setup(bot):
    await bot.add_cog(Downloader(bot))