import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import random
import os
import subprocess
from datetime import datetime, timedelta
from googleapiclient.discovery import build

# ==========================================
# CONFIGURAÇÕES GERAIS E COMFYUI
# ==========================================
COMFYUI_URL = "http://127.0.0.1:8188"

# ⚠️ ALTERE ISSO PARA O CAMINHO REAL DO SEU COMFYUI NO UBUNTU
COMFYUI_DIR = "/home/demuyo/ComfyUI" 
# Comando para iniciar (se usar ambiente virtual (venv), coloque o caminho absoluto do python do venv)
COMFYUI_CMD = ["bash", "start.sh"] 

WORKFLOWS = {
    "anime": "cogs/assets/workflows/anime.json",
    "realista_lq": "cogs/assets/workflows/realisticlq.json",
    "realista_hq": "cogs/assets/workflows/realistichq.json"
}

RESOLUCOES = {
    "quadrada": (1024, 1024),
    "vertical": (832, 1216),
    "horizontal": (1216, 832)
}

# ==========================================
# INTERFACE VISUAL (MODAL E VIEWS)
# ==========================================

class PromptModal(discord.ui.Modal, title='materializar pensamento 🔮'):
    prompt_input = discord.ui.TextInput(
        label='o que vamos criar?',
        style=discord.TextStyle.paragraph,
        placeholder='ex: a tewi inaba de touhou project...',
        required=True,
        max_length=1000
    )
    
    neg_prompt_input = discord.ui.TextInput(
        label='o que NÃO queremos? (opcional)',
        style=discord.TextStyle.short,
        placeholder='ex: feio, deformado, texto...',
        required=False,
        max_length=500
    )

    def __init__(self, cog, estilo, resolucao_nome, qualidade):
        super().__init__()
        self.cog = cog
        self.estilo = estilo
        self.resolucao_nome = resolucao_nome
        self.qualidade = qualidade

    async def on_submit(self, interaction: discord.Interaction):
        # Manda a mensagem inicial que será editada depois
        msg = await interaction.response.send_message(
            f"🖤 invocando forças primordiais, aguarde...", 
            ephemeral=False
        )
        msg_original = await interaction.original_response()
        
        prompt_user = self.prompt_input.value
        prompt_neg = self.neg_prompt_input.value
        
        asyncio.create_task(
            self.cog.gerar_imagem_comfy(
                interaction.channel, 
                interaction.user, 
                prompt_user, 
                prompt_neg, 
                self.estilo, 
                self.resolucao_nome,
                self.qualidade,
                msg_original
            )
        )

class GenView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.estilo_selecionado = "anime"
        self.resolucao_selecionada = "vertical"
        self.qualidade_selecionada = "hq"

    @discord.ui.select(
        placeholder="1️⃣ escolha o estilo (padrão: anime)",
        options=[
            discord.SelectOption(label="Anime", description="estilo japonês, 2d, ilustrado", value="anime", emoji="🌸"),
            discord.SelectOption(label="Realista", description="fotografia e renderizações hiper-realistas", value="realista", emoji="📸")
        ],
        row=0
    )
    async def select_estilo(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.estilo_selecionado = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="2️⃣ escolha a resolução (padrão: vertical)",
        options=[
            discord.SelectOption(label="Vertical (Retrato)", description="832x1216 - ideal para personagens", value="vertical", emoji="📱"),
            discord.SelectOption(label="Horizontal (Paisagem)", description="1216x832 - ideal para cenários", value="horizontal", emoji="🖥️"),
            discord.SelectOption(label="Quadrada", description="1024x1024 - formato instagram", value="quadrada", emoji="⬛")
        ],
        row=1
    )
    async def select_resolucao(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.resolucao_selecionada = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.select(
        placeholder="3️⃣ escolha a qualidade (padrão: alta)",
        options=[
            discord.SelectOption(label="Maior Qualidade (Lento)", description="resultados superiores, demora mais", value="hq", emoji="✨"),
            discord.SelectOption(label="Menor Qualidade (Rápido)", description="gera rápido, qualidade reduzida", value="lq", emoji="⚡")
        ],
        row=2
    )
    async def select_qualidade(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.qualidade_selecionada = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Descrever Imagem", style=discord.ButtonStyle.secondary, emoji="🔮", row=3)
    async def btn_prompt(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PromptModal(self.cog, self.estilo_selecionado, self.resolucao_selecionada, self.qualidade_selecionada)
        await interaction.response.send_modal(modal)

# ==========================================
# COG PRINCIPAL
# ==========================================

class ImageGen(commands.Cog):
    """gerador de realidades visuais da nyxie com controle de processo"""

    def __init__(self, bot):
        self.bot = bot
        self.comfy_process = None
        self.last_activity = datetime.now()
        # Inicia a tarefa de checagem a cada 1 minuto
        self.monitor_comfyui.start()

    def cog_unload(self):
        self.monitor_comfyui.cancel()
        if self.comfy_process:
            self.comfy_process.terminate()

    @property
    def utils(self):
        return self.bot.get_cog('utils')

    @property
    def conv_sys(self):
        return self.bot.get_cog('ConversationSystem')

    # ==========================================
    # GERENCIAMENTO DO PROCESSO COMFYUI
    # ==========================================
    @tasks.loop(minutes=1)
    async def monitor_comfyui(self):
        """Checa se o ComfyUI está inativo há mais de 10 minutos e o desliga."""
        if self.comfy_process is not None:
            tempo_inativo = datetime.now() - self.last_activity
            if tempo_inativo > timedelta(minutes=10):
                print("[Nyxie] ComfyUI inativo por 10 minutos. Adormecendo processo...")
                self.comfy_process.terminate()
                self.comfy_process = None

    async def garantir_comfyui_online(self, msg_original):
        """Liga o ComfyUI se estiver fechado e aguarda ele ficar pronto."""
        self.last_activity = datetime.now() # Reseta o timer
        
        # Se o processo existe e ainda tá rodando, tá tudo ok
        if self.comfy_process is not None and self.comfy_process.poll() is None:
            return True

        await msg_original.edit(content="⚙️ **1/4** • o motor de geração estava dormindo. despertando o ComfyUI localmente... (pode demorar alguns segundos)")
        
        try:
            # Abre o processo no Ubuntu (sem bloquear o bot)
            self.comfy_process = subprocess.Popen(
                COMFYUI_CMD, 
                cwd=COMFYUI_DIR,
                stdout=subprocess.DEVNULL, # Ignora os logs no terminal do discord
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            await msg_original.edit(content=f"❌ erro crítico ao tentar ligar o comfyui no sistema: `{e}`")
            return False

        # Fica testando a porta 8188 até ele responder (máximo de ~60 segundos)
        tentativas = 0
        async with aiohttp.ClientSession() as session:
            while tentativas < 30:
                try:
                    async with session.get(f"{COMFYUI_URL}/system_stats", timeout=2) as resp:
                        if resp.status == 200:
                            return True
                except:
                    pass
                tentativas += 1
                await asyncio.sleep(2)
                
        await msg_original.edit(content="❌ o ComfyUI demorou demais para responder. verifique o servidor.")
        if self.comfy_process:
            self.comfy_process.terminate()
            self.comfy_process = None
        return False

    # ==========================================
    # COMANDOS E GERAÇÃO
    # ==========================================
    @commands.command(aliases=["draw", "desenhar", "imagine"], brief="gera imagens pelo comfyui")
    async def gerar(self, ctx):
        """inicia o painel de criação de imagens"""
        embed = self.utils.base_embed(
            "materialização", 
            "o que vamos criar nas sombras hoje, fofuxo?\n\nescolha o **estilo**, a **resolução** e a **qualidade** nos menus abaixo, e depois clique no botão para descrever seu desejo..."
        )
        view = GenView(self)
        await ctx.send(embed=embed, view=view)

    def pesquisar_personagem(self, prompt):
        API_KEY = os.getenv('GOOGLE_API_KEY')
        CSE_ID = os.getenv('GOOGLE_CSE_ID')
        if not API_KEY or not CSE_ID: return ""
        try:
            service = build("customsearch", "v1", developerKey=API_KEY)
            query = f"{prompt} character design visual appearance wiki"
            result = service.cse().list(q=query, cx=CSE_ID, num=3).execute()
            snippets = [r.get('snippet', '') for r in result.get('items', [])]
            return " ".join(snippets)
        except Exception as e:
            return ""

    async def expandir_prompt_com_groq(self, user_prompt, contexto_pesquisa):
        system_prompt = (
            "You are an expert at writing prompts for Stable Diffusion models (Danbooru tag style for Anime, realistic descriptive style for Realistic). "
            "I will give you a character request, and optionally some search context about their visual appearance. "
            "You MUST describe their appearance accurately (hair color, clothes, eyes, signature items). "
            "Format the output strictly as a comma-separated list of keywords or tags. Add masterpiece, best quality, highly detailed at the start. "
            "NEVER use conversational text. ONLY return the tags."
        )
        
        user_content = f"Request: {user_prompt}\n"
        if contexto_pesquisa:
            user_content += f"Visual Appearance Context (from web): {contexto_pesquisa}\n"
        user_content += "\nTransform this into a prompt."

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]

        try:
            response = await asyncio.to_thread(
                self.conv_sys.groq_client.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except:
            return f"masterpiece, best quality, {user_prompt}"

    async def gerar_imagem_comfy(self, canal, user, user_prompt, negative_prompt, estilo, resolucao_nome, qualidade, msg_original):
        # 1. Garante que o ComfyUI tá aberto
        comfy_ok = await self.garantir_comfyui_online(msg_original)
        if not comfy_ok: return
        self.last_activity = datetime.now()

        # 2. Define o Workflow
        if estilo == "anime":
            json_path = WORKFLOWS["anime"]
        else: # realista
            json_path = WORKFLOWS["realista_hq"] if qualidade == "hq" else WORKFLOWS["realista_lq"]

        if not os.path.exists(json_path):
            await msg_original.edit(content=f"❌ erro: não achei o arquivo de workflow em `{json_path}` ainda...")
            return

        width, height = RESOLUCOES[resolucao_nome]
        
        # 3. Inteligência (Groq)
        usar_ia = False
        user_prompt_clean = user_prompt.lower().strip()
        if len(user_prompt_clean.split()) < 10 or "detalha" in user_prompt_clean or "expande" in user_prompt_clean:
            usar_ia = True
            
        user_prompt_clean = user_prompt_clean.replace("detalha:", "").replace("expande:", "").strip()

        if usar_ia:
            await msg_original.edit(content="🧠 **2/4** • o prompt estava simples. consultando a rede para puxar a aparência exata do alvo...")
            contexto = await asyncio.to_thread(self.pesquisar_personagem, user_prompt_clean)
            enhanced_prompt = await self.expandir_prompt_com_groq(user_prompt_clean, contexto)
        else:
            await msg_original.edit(content="🧠 **2/4** • o prompt está denso o suficiente, enviando direto...")
            enhanced_prompt = f"masterpiece, best quality, {user_prompt}"

        # 4. Carrega e preenche o JSON de acordo com Estilo/Qualidade
        with open(json_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        seed_val = random.randint(1, 999999999999999)
        base_negativo = "worst quality, low quality, watermark, text, bad anatomy, bad hands, deformed"
        final_negativo = f"{base_negativo}, {negative_prompt}" if negative_prompt else base_negativo

        if estilo == "anime":
            workflow["5"]["inputs"]["width"] = width
            workflow["5"]["inputs"]["height"] = height
            workflow["6"]["inputs"]["seed"] = seed_val
            workflow["43"]["inputs"]["positive"] = enhanced_prompt
            workflow["43"]["inputs"]["temp_str"] = ""
            workflow["8"]["inputs"]["positive"] = final_negativo
            workflow["8"]["inputs"]["temp_str"] = ""
            
            # Controle de qualidade para anime (Steps)
            workflow["6"]["inputs"]["steps"] = 30 if qualidade == "hq" else 15

        elif estilo == "realista" and qualidade == "lq":
            workflow["6"]["inputs"]["width"] = width
            workflow["6"]["inputs"]["height"] = height
            workflow["5"]["inputs"]["seed"] = seed_val
            workflow["3"]["inputs"]["text"] = enhanced_prompt
            workflow["4"]["inputs"]["text"] = final_negativo

        elif estilo == "realista" and qualidade == "hq":
            workflow["64:13"]["inputs"]["width"] = width
            workflow["64:13"]["inputs"]["height"] = height
            workflow["64:3"]["inputs"]["seed"] = seed_val
            workflow["64:27"]["inputs"]["text"] = enhanced_prompt
            # O zimageturbo não precisa de text_input negativo (ConditioningZeroOut cuida disso).

        # 5. Comunicação com a placa de vídeo
        await msg_original.edit(content=f"🩸 **3/4** • processando a imagem... \n*(lembrete: a primeira geração da sessão sempre demora um pouco mais por causa do carregamento dos modelos na VRAM!)*")
        
        async with aiohttp.ClientSession() as session:
            queue_data = {"prompt": workflow}
            async with session.post(f"{COMFYUI_URL}/prompt", json=queue_data) as response:
                if response.status != 200:
                    await msg_original.edit(content=f"❌ erro ao comunicar com o comfyui nas profundezas... (Status {response.status})")
                    return
                resp_json = await response.json()
                prompt_id = resp_json['prompt_id']

            # 6. Polling (Espera Ativa)
            while True:
                self.last_activity = datetime.now() # Mantém o processo vivo durante o job
                async with session.get(f"{COMFYUI_URL}/history/{prompt_id}") as hist_resp:
                    hist_data = await hist_resp.json()
                    
                    if prompt_id in hist_data:
                        outputs = hist_data[prompt_id]['outputs']
                        node_save_image = None
                        for node_id, output in outputs.items():
                            if 'images' in output:
                                node_save_image = node_id
                                break
                                
                        if node_save_image:
                            image_info = outputs[node_save_image]['images'][0]
                            filename = image_info['filename']
                            subfolder = image_info['subfolder']
                            folder_type = image_info['type']
                            break
                        else:
                            await msg_original.edit(content="❌ deu algo errado no nó de salvar imagem... =(")
                            return
                
                await asyncio.sleep(2)

            # 7. Resgata e Envia a Imagem Final
            await msg_original.edit(content=f"📥 **4/4** • puxando imagem da base de dados...")
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            async with session.get(f"{COMFYUI_URL}/view", params=params) as img_resp:
                if img_resp.status == 200:
                    image_data = await img_resp.read()
                    temp_path = f"downloads/temp_{prompt_id}.png"
                    os.makedirs("downloads", exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(image_data)

                    embed = self.utils.base_embed("visão concluída", f"aqui está sua materialização, {user.mention}")
                    embed.add_field(name="prompt original", value=f"`{user_prompt}`", inline=False)
                    if usar_ia:
                        embed.add_field(name="prompt expandido (ia)", value=f"`{enhanced_prompt[:1000]}`", inline=False)
                    embed.add_field(name="configurações", value=f"`{estilo} | {qualidade.upper()} | {width}x{height}`", inline=True)

                    file = discord.File(temp_path, filename="visão.png")
                    embed.set_image(url="attachment://visão.png")

                    await msg_original.delete()
                    await canal.send(embed=embed, file=file)
                    os.remove(temp_path)

async def setup(bot):
    await bot.add_cog(ImageGen(bot))