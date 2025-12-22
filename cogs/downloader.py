import yt_dlp, os, asyncio, discord, requests, re, shutil, time, subprocess, tempfile
from discord.ext import commands

def get_cookie_path(platform):
    """Retorna caminho do cookie (env ou local)"""
    env_var = f'{platform.upper()}_COOKIES'
    cookies_env = os.getenv(env_var)
    
    if cookies_env:
        temp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp.write(cookies_env)
        temp.close()
        return temp.name
    
    local_path = f'cookies/cookies_{platform}.txt'
    if os.path.exists(local_path):
        return local_path
    
    return None

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

def verificar_codec(caminho):
    """Retorna o codec do vídeo"""
    try:
        cmd = [
            r'C:\ffmpeg\bin\ffprobe.exe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            caminho
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        codec = result.stdout.strip().lower()
        print(f"🎬 Codec: {codec}")
        return codec
    except Exception as e:
        print(f"❌ Erro ao verificar codec: {e}")
        return None

def baixar_video(url, formato='mp4'):
    """Baixa vídeo/áudio com retry e conversão automática"""
    os.makedirs('downloads', exist_ok=True)

    # ====== PEGA COOKIE (ENV OU LOCAL) ======
    cookie_file = None
    if 'youtube.com' in url or 'youtu.be' in url:
        cookie_file = get_cookie_path('youtube')
    elif 'tiktok.com' in url:
        cookie_file = get_cookie_path('tiktok')

    ydl_opts = {
        'outtmpl': 'downloads/temp_%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': r'C:\ffmpeg\bin',
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 10,
        'extractor_retries': 10,
    }

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    # Configurações por formato
    if formato == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }]
        })
    elif formato == "wav":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }]
        })
    elif formato == "mp4":
        ydl_opts.update({
            'format': 'bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    try:
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'video')

        # Aguarda Windows liberar arquivo
        time.sleep(2)

        # Processamento de vídeo MP4
        if formato == "mp4":
            for tentativa in range(5):
                try:
                    arquivos_temp = [f for f in os.listdir('downloads') if f.startswith('temp_')]
                    
                    if not arquivos_temp:
                        if tentativa < 4:
                            print(f"⏳ Aguardando arquivo... {tentativa+1}/5")
                            time.sleep(2)
                            continue
                        return False, None
                    
                    arquivo_original = f'downloads/{arquivos_temp[0]}'
                    
                    if not os.path.exists(arquivo_original):
                        if tentativa < 4:
                            print(f"⏳ Aguardando existência... {tentativa+1}/5")
                            time.sleep(2)
                            continue
                        return False, None
                    
                    arquivo_final = arquivo_original.replace('temp_', '').rsplit('.', 1)[0] + '.mp4'
                    codec = verificar_codec(arquivo_original)
                    
                    # Converte codecs problemáticos
                    if codec in ['hevc', 'h265', 'hvc1', 'hev1', 'av1']:
                        print(f"🔄 Convertendo {codec} → H.264...")
                        
                        cmd = [
                            r'C:\ffmpeg\bin\ffmpeg.exe',
                            '-i', arquivo_original,
                            '-c:v', 'libx264',
                            '-preset', 'fast',
                            '-crf', '23',
                            '-c:a', 'aac',
                            '-b:a', '320k',
                            '-movflags', '+faststart',
                            '-y',
                            arquivo_final
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            print(f"❌ Erro ffmpeg: {result.stderr}")
                            if tentativa < 4:
                                time.sleep(2)
                                continue
                            return False, None
                        
                        time.sleep(1)
                        
                        # Tenta deletar original
                        for _ in range(3):
                            try:
                                os.remove(arquivo_original)
                                break
                            except PermissionError:
                                time.sleep(1)
                        
                        tamanho_mb = os.path.getsize(arquivo_final) / (1024*1024)
                        print(f"✅ Convertido! {codec} → H.264 ({tamanho_mb:.1f}MB)")
                    else:
                        print(f"✅ Codec OK ({codec})")
                        
                        # Tenta renomear com retry
                        renomeado = False
                        for rename_tentativa in range(3):
                            try:
                                os.rename(arquivo_original, arquivo_final)
                                renomeado = True
                                break
                            except PermissionError:
                                if rename_tentativa < 2:
                                    print(f"⏳ Aguardando liberar... {rename_tentativa+1}/3")
                                    time.sleep(2)
                        
                        # Fallback: copia se rename falhar
                        if not renomeado:
                            print("⚠️ Copiando arquivo...")
                            shutil.copy2(arquivo_original, arquivo_final)
                            try:
                                os.remove(arquivo_original)
                            except:
                                pass
                    
                    return True, titulo
                    
                except Exception as e:
                    if tentativa < 4:
                        print(f"⚠️ Erro tentativa {tentativa+1}/5: {e}")
                        time.sleep(2)
                    else:
                        print(f"❌ Falhou após 5 tentativas")
                        return False, None
            
            return False, None

        return True, titulo

    except Exception as e:
        print(f"❌ Erro yt-dlp: {e}")
        return False, None
    
    finally:
        # ====== LIMPA ARQUIVO TEMPORÁRIO ======
        if cookie_file and '/tmp' in cookie_file or (cookie_file and 'AppData\\Local\\Temp' in cookie_file):
            try:
                os.remove(cookie_file)
            except:
                pass

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
                return None

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
                    return link
            
            print(f"⚠️ Tentativa {tentativa}/{max_tentativas} falhou: {r.status_code}")
            
            if tentativa < max_tentativas:
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ Erro tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                time.sleep(5)
    
    return None


class Downloader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=["dl", "download"],
        usage="[formato] (link)",
        brief="baixa vídeos e áudios",
        help="faz download de vídeos/áudios do youtube, tiktok e outras plataformas. suporta mp4, mp3 e wav."
    )
    async def baixar(self, ctx, formato_ou_url: str = None, *, url: str = None):
        """
        baixa vídeos e áudios de diversas plataformas.
        
        suporta youtube, tiktok, instagram, twitter e muitas outras.
        arquivos até 10mb vão direto pro discord, maiores vão pro catbox.
        converte automaticamente codecs incompatíveis (hevc/av1) para h264.
        
        uso:
        !baixar (link)
        !baixar [formato] (link)
        
        formatos disponíveis: mp4, mp3, wav
        
        exemplo:
        !baixar https://youtube.com/watch?v=exemplo
        !baixar mp3 https://youtube.com/watch?v=exemplo
        !dl wav https://soundcloud.com/exemplo
        """
        utils = self.bot.get_cog('utils')
        
        # Detecta formato e URL
        formatos_validos = ["mp3", "mp4", "wav"]
        
        if url is None:
            url = formato_ou_url
            formato = "mp4"
        else:
            if formato_ou_url.lower() in formatos_validos:
                formato = formato_ou_url.lower()
            else:
                url = f"{formato_ou_url} {url}"
                formato = "mp4"
        
        if formato not in formatos_validos:
            formato = "mp4"
        
        # ==================== LOADING ====================
        embed_loading = utils.base_embed("baixando", None)
        embed_loading.add_field(name="formato", value=f"`{formato.upper()}`", inline=True)
        embed_loading.add_field(name="status", value="processando", inline=True)
        msg = await ctx.send(embed=embed_loading)
        
        # ==================== DOWNLOAD ====================
        loop = asyncio.get_event_loop()
        sucesso, titulo = await loop.run_in_executor(None, baixar_video, url, formato)
        
        if not sucesso:
            embed_erro = utils.base_embed("erro", "não consegui baixar")
            embed_erro.add_field(name="possíveis causas", value="• vídeo privado\n• link inválido\n• região bloqueada", inline=False)
            return await msg.edit(embed=embed_erro)
        
        # Pega arquivo mais recente
        try:
            arquivo = max([f for f in os.listdir('downloads')], key=lambda x: os.path.getctime(f'downloads/{x}'))
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
        
        # ==================== DISCORD (≤8MB) ====================
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
                print(f"discord falhou ({tamanho_mb}MB): {e}")
                try:
                    await msg.delete()
                except:
                    pass
                msg = await ctx.send(embed=utils.base_embed("enviando pro catbox", "arquivo grande demais pro discord"))
        
        # ==================== CATBOX (>8MB) ====================
        
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

    @commands.command(
        usage="",
        brief="lista arquivos salvos na pasta downloads",
        help="mostra os últimos 20 arquivos baixados que ainda estão salvos localmente."
    )
    async def arquivos(self, ctx):
        """
        lista arquivos salvos na pasta downloads.
        
        mostra os 20 arquivos mais recentes que ainda não foram deletados.
        útil para ver o que está ocupando espaço.
        
        uso:
        !arquivos
        
        exemplo:
        !arquivos
        """
        utils = self.bot.get_cog('utils')
        
        if not os.path.exists('downloads') or not os.listdir('downloads'):
            embed = utils.base_embed("pasta vazia", "nenhum arquivo salvo")
            return await ctx.send(embed=embed)
        
        arquivos = sorted(os.listdir('downloads'), key=lambda x: os.path.getctime(f'downloads/{x}'), reverse=True)[:20]
        
        embed = utils.base_embed("arquivos", f"últimos {len(arquivos)}")
        lista = "\n".join([f"`{f[:50]}`" for f in arquivos])
        embed.add_field(name="downloads/", value=lista, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(
        usage="(nome_do_arquivo)",
        brief="deleta um arquivo específico",
        help="remove um arquivo da pasta downloads. use !arquivos para ver os nomes disponíveis."
    )
    async def deletar(self, ctx, *, nome):
        """
        deleta um arquivo específico da pasta downloads.
        
        use o comando !arquivos primeiro para ver a lista de arquivos salvos.
        o nome deve ser exato, incluindo a extensão.
        
        uso:
        !deletar (nome_do_arquivo)
        
        exemplo:
        !deletar video_123456.mp4
        !deletar musica_789012.mp3
        """
        caminho = f"downloads/{nome}"
        
        if os.path.exists(caminho):
            os.remove(caminho)
            await ctx.send(f"deletado `{nome}`")
        else:
            await ctx.send("arquivo não encontrado")

    @commands.command(
        aliases=["clrdl", "clrdls"],
        usage="",
        brief="apaga todos os arquivos baixados",
        help="limpa completamente a pasta downloads. pede confirmação antes de executar."
    )
    async def limpardownloads(self, ctx):
        """
        apaga todos os arquivos da pasta downloads.
        
        remove permanentemente todos os vídeos e áudios baixados.
        pede confirmação digitando 'sim' em 10 segundos.
        
        uso:
        !limpardownloads
        
        exemplo:
        !limpardownloads
        !clrdl
        """
        await ctx.send("apagar tudo? digite `sim` em 10s")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'sim'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=10)
            shutil.rmtree('downloads')
            os.makedirs('downloads')
            await ctx.send("tudo limpo!")
        except:
            await ctx.send("cancelado")

async def setup(bot):
    await bot.add_cog(Downloader(bot))
    print("✅ Downloader carregado!")