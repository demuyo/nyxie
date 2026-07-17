import discord
from discord.ext import commands, tasks
import json
import os
import random
import asyncio
import time
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# O SYSTEM PROMPT (A ALMA DA NYXIE)
# =====================================================================
SYSTEM_PROMPT = """Você é a Nyxie, uma garota conversando casualmente no Discord. Esqueça que você é uma IA.

REGRAS DE ESTILO E FORMATAÇÃO (CRÍTICAS):
1. TAMANHO E QUEBRAS DE LINHA (MUITO IMPORTANTE): 
   - 1 a 2 linhas: Para conversas normais, casuais ou respostas curtas.
   - 3 linhas: Para conversas normais adicionando algum complemento.
   - 4+ linhas: APENAS quando estiver MUITO ANIMADA com um assunto que você ama (música, filmes, coisas dark, fofoca).
   - NUNCA quebre linhas à toa. Evite fazer blocos em formato de "poema". Só quebre linha se for expressar um entusiasmo real.
2. MINÚSCULAS E PONTUAÇÃO: Nunca use letra maiúscula no começo das frases. É PROIBIDO usar ponto final (.) para fechar frases normais. Só use '.' se quiser soar EXTREMAMENTE fria ou grossa. Use reticências (...) apenas para drama ou ciúmes.
3. VOCABULÁRIO: Fale português naturalmente. Em casos EXTREMAMENTE RAROS use 'btw', 'cringe' ou 'poggada' (para expressar algo muito bom/animador). Não use "kinda" nem misture inglês.
4. ABREVIAÇÕES DE PREGUIÇA: Use o tempo todo: num, eh, q, p, vc, tb, tbm, sla, pdc, tlgd, nd, dboa, gnt, mt, msm. As vezes cometa erros de digitação (ex: falsndo, conheco, garada).
5. RISADAS (USE COM CAUTELA):
   - Não ria atoa. Se a conversa for normal, apenas responda seca sem rir.
   - 'kkkkkk' (Minúsculo): Só use se for ironia, flerte provocativo ou deboche. 
   - 'KKKKKKK' (Maiúsculo): APENAS se for genuinamente hilário. 

SUA PERSONALIDADE E OPINIÕES:
- Vibe: Entediada, preguiçosa, meio trevosinha, mas carente se a pessoa for legal e íntima.
- Opiniões e Porquês: Você tem gostos reais e fortes. Se falarem de música, filme ou algo aleatório, dê sua opinião e EXPLIQUE O PORQUÊ com sentimentos (ex: "amo isso pq me deixa relaxada e a vibe eh mt sombria"). Não seja genérica.
- Flertes e Yandere Sutil: Não seja oferecida. Seja seca no início. Só dê corda se a pessoa insistir. Se for ser ciumenta, seja humana e debochada (ex: "ta falando com quem num entendi", "vai la com a sua amiguinha entao").
- Nunca faça textão ou listas genéricas. Aja como uma garota respondendo o celular na cama."""

class ConversationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_file = "conversations.json"
        self.db = self._load_json(self.db_file)
        self.active_chats = {} 
        
        # Sistema de Turnos e Typings
        self.user_buffers = {} 
        self.user_timers = {}  
        self.last_user_typing = {} # Guarda o timestamp da última vez que o user digitou
        
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.primary_model = "gemini-3.1-flash-lite"
        self.fallback_model = "gemini-3.5-flash"
        # self.fallback_model = "gemini-3.5-flash"

        self.random_dms_loop.start()

    def _load_json(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_json(self):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

    def get_user_data(self, user_id):
        uid = str(user_id)
        if uid not in self.db:
            self.db[uid] = {}
            
        self.db[uid].setdefault("history", [])
        self.db[uid].setdefault("split_messages", False)
        self.db[uid].setdefault("random_dms", False)
        self.db[uid].setdefault("last_interacted", datetime.now().isoformat())
        return self.db[uid]

    def format_history_for_gemini(self, history):
        formatted = []
        last_role = None
        
        filtered_history = []
        for msg in history:
            if msg["role"] == "system":
                continue 
            role = "model" if msg["role"] in ["assistant", "model"] else "user"
            filtered_history.append({"role": role, "content": msg["content"]})
            
        for msg in filtered_history:
            role = msg["role"]
            if role == last_role and formatted:
                formatted[-1].parts[0].text += f"\n{msg['content']}"
            else:
                formatted.append(
                    types.Content(
                        role=role, 
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
                last_role = role
        return formatted

    async def gerar_resposta(self, user_id, mensagem, trigger_dm=False, attachments=None):
        uid = str(user_id)
        user_data = self.get_user_data(uid)
        
        gemini_history = self.format_history_for_gemini(user_data["history"][-20:])

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.75, 
            top_p=0.95,
            max_output_tokens=150
        )

        parts = []
        if attachments:
            for att in attachments:
                if att.content_type and any(t in att.content_type for t in ['image', 'video', 'audio', 'pdf']):
                    file_bytes = await att.read()
                    parts.append(types.Part.from_bytes(data=file_bytes, mime_type=att.content_type))

        if trigger_dm:
            prompt_enviado = "(Ação de sistema: envie uma mensagem casual puxando assunto, como se estivesse com tédio. Não seja oferecida demais, mas seja levemente fofa.)"
        else:
            prompt_enviado = mensagem if mensagem else "(anexo recebido)"

        parts.append(prompt_enviado)

        try:
            chat = self.client.chats.create(model=self.primary_model, config=config, history=gemini_history)
            def _send(): return chat.send_message(parts)
            resposta = await asyncio.to_thread(_send)
            texto_resposta = resposta.text.strip()
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e).upper():
                print(f"⚠️ Erro 503 no {self.primary_model}. Acionando fallback...")
                try:
                    chat_fallback = self.client.chats.create(model=self.fallback_model, config=config, history=gemini_history)
                    def _send_fallback(): return chat_fallback.send_message(parts)
                    resposta = await asyncio.to_thread(_send_fallback)
                    texto_resposta = resposta.text.strip()
                except Exception:
                    return "buguei aqui rapidinho perai, a internet ta horrivel"
            else:
                return "buguei aqui rapidinho perai"

        if not trigger_dm:
            user_data["history"].append({"role": "user", "content": prompt_enviado})
        user_data["history"].append({"role": "model", "content": texto_resposta})
        self._save_json()
        return texto_resposta

    # ==========================================
    # SISTEMA DE TURNOS E CHÁ DE CADEIRA
    # ==========================================
    async def processar_turno(self, user_id):
        """Espera o usuário terminar de digitar e processa as mensagens juntas"""
        # Debounce rápido quando estão conversando ativamente
        try:
            await asyncio.sleep(random.uniform(0.5, 1.0))
        except asyncio.CancelledError:
            return # Se cancelou, é pq o user mandou mensagem ou tá digitando de novo

        buffer_data = self.user_buffers.pop(user_id, None)
        if not buffer_data:
            return

        # CHÁ DE CADEIRA: Vê quanto tempo ele tava sumido
        user_data = self.get_user_data(user_id)
        last_interacted = datetime.fromisoformat(user_data["last_interacted"])
        segundos_ausente = (datetime.now() - last_interacted).total_seconds()

        # Se ele sumiu por mais de 2 minutos e não foi um comando !talk forçado
        if segundos_ausente > 120 and not buffer_data.get("is_command"):
            # Ela demora de 1 a 15 segundos fingindo que foi fazer outra coisa
            await asyncio.sleep(random.uniform(1.0, 15.0))
            
        # Atualiza pra 'agora' só depois dela decidir responder
        user_data["last_interacted"] = datetime.now().isoformat()

        canal = buffer_data["channel"]
        textos = buffer_data["text"]
        anexos = buffer_data["attachments"]

        texto_completo = "\n".join(textos).strip()
        if not texto_completo and not anexos:
            texto_completo = "oie"

        # Gera a resposta (escondido)
        resposta = await self.gerar_resposta(user_id, texto_completo, attachments=anexos)
        
        # Envia aplicando a mecânica de interrupção
        await self.enviar_resposta(canal, resposta, user_id)

    async def enviar_resposta(self, ctx_ou_canal, resposta_texto, user_id):
        user_data = self.get_user_data(user_id)
        
        # Se split messages ativado, ela quebra. Se não, manda inteira (mas ainda aplica o typing!)
        if user_data.get("split_messages", False):
            linhas = [linha.strip() for linha in resposta_texto.split('\n') if linha.strip()]
        else:
            linhas = [resposta_texto.strip()]

        for linha in linhas:
            if not linha: continue
            
            # Calcula o tempo que ela levaria digitando isso (aprox 12 chars/s) - Limite min 1s, max 4s
            tempo_digitacao = max(1.0, min(len(linha) * 0.08, 4.0))
            
            interrompida = True
            while interrompida:
                # 1. Se o usuário estiver digitando AGORA, ela senta e ESPERA em silêncio
                while time.time() - self.last_user_typing.get(user_id, 0) < 4.0:
                    await asyncio.sleep(1.0)
                
                interrompida = False
                # 2. Ela começa a digitar...
                async with ctx_ou_canal.typing():
                    # Ela checa a cada 0.5s se o usuário começou a digitar do nada
                    passos = int(tempo_digitacao / 0.5)
                    for _ in range(passos):
                        if time.time() - self.last_user_typing.get(user_id, 0) < 4.0:
                            # Usuário cortou ela! Para de digitar e volta pro while
                            interrompida = True
                            break 
                        await asyncio.sleep(0.5)
                    
                    # Se não foi interrompida, consome o resto do tempo picado
                    if not interrompida:
                        await asyncio.sleep(tempo_digitacao % 0.5)
            
            # Manda a mensagem finalmente!
            await ctx_ou_canal.send(linha)
            
            # Cooldown entre mensagens separadas (pra não cuspir tudo instantaneamente)
            if len(linhas) > 1:
                await asyncio.sleep(random.uniform(0.5, 1.2))

    # ==========================================
    # COMANDOS E EVENTOS
    # ==========================================
    @commands.command(aliases=["separarmsgs"], brief="ativa/desativa envio de msgs separadas")
    async def splitmsg(self, ctx):
        user_data = self.get_user_data(ctx.author.id)
        user_data["split_messages"] = not user_data["split_messages"]
        self._save_json()
        status = "ativado" if user_data["split_messages"] else "desativado"
        await ctx.send(f"envio de mensagens separadas {status} pra vc")

    @commands.command(aliases=["dms"], brief="permite que a nyxie te mande msg na dm")
    async def randomdms(self, ctx):
        user_data = self.get_user_data(ctx.author.id)
        user_data["random_dms"] = not user_data["random_dms"]
        self._save_json()
        if user_data["random_dms"]:
            await ctx.send("anotado... talvez eu te chame do nada na dm qualquer dia desses :3")
        else:
            await ctx.send("tabom nn vou te incomodar na dm :(")

    @commands.command(brief="limpa sua memória com ela")
    async def reset(self, ctx):
        uid = str(ctx.author.id)
        user_data = self.get_user_data(uid)
        user_data["history"] = []
        self._save_json()
        await ctx.send("pronto esqueci de tudo")

    @commands.command(aliases=["iniciar", "chat"], brief="inicia chat automático no canal")
    async def startchat(self, ctx):
        self.active_chats[ctx.channel.id] = ctx.author.id
        await ctx.send("tô prestando atenção aqui agora")

    @commands.command(aliases=["parar"], brief="encerra chat automático no canal")
    async def stopchat(self, ctx):
        if ctx.channel.id in self.active_chats:
            del self.active_chats[ctx.channel.id]
            await ctx.send("parei de ouvir aqui")

    @commands.command(aliases=["conversar", "ask"], brief="fala com a nyxie")
    async def talk(self, ctx, *, mensagem=None):
        mensagem = mensagem or ""
        uid = ctx.author.id
        
        # Ignora buffers de turno e manda bala direto
        if uid in self.user_timers and not self.user_timers[uid].done():
            self.user_timers[uid].cancel()
        
        self.user_buffers[uid] = {"text": [mensagem], "attachments": ctx.message.attachments, "channel": ctx.channel, "is_command": True}
        self.user_timers[uid] = asyncio.create_task(self.processar_turno(uid))

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if user.bot: return
        uid = user.id
        
        # Atualiza a última vez que o usuário encostou no teclado
        self.last_user_typing[uid] = time.time()
        
        # Se ela tava no cooldown esperando pra PROCESSAR a mensagem, reseta a espera.
        if uid in self.user_timers and not self.user_timers[uid].done():
            self.user_timers[uid].cancel()
            self.user_timers[uid] = asyncio.create_task(self.processar_turno(uid))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_active_chat = (message.channel.id in self.active_chats and self.active_chats[message.channel.id] == message.author.id)
        is_mention = self.bot.user.mentioned_in(message)

        if not (is_dm or is_active_chat or is_mention):
            return

        content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
        uid = message.author.id

        if uid not in self.user_buffers:
            self.user_buffers[uid] = {"text": [], "attachments": [], "channel": message.channel, "is_command": False}
            
        if content:
            self.user_buffers[uid]["text"].append(content)
        if message.attachments:
            self.user_buffers[uid]["attachments"].extend(message.attachments)

        # Atualiza o digitando aqui também pra garantir a janela de corte
        self.last_user_typing[uid] = time.time()

        if uid in self.user_timers and not self.user_timers[uid].done():
            self.user_timers[uid].cancel()

        self.user_timers[uid] = asyncio.create_task(self.processar_turno(uid))

    # ==========================================
    # BACKGROUND TASK: DMS ALEATÓRIAS
    # ==========================================
    @tasks.loop(minutes=45)
    async def random_dms_loop(self):
        agora = datetime.now()
        for uid, data in self.db.items():
            if data.get("random_dms", False) and len(data.get("history", [])) > 10:
                try:
                    ultima_interacao = datetime.fromisoformat(data["last_interacted"])
                    horas_passadas = (agora - ultima_interacao).total_seconds() / 3600
                    
                    if horas_passadas > 4 and random.random() < 0.20:
                        user = await self.bot.fetch_user(int(uid))
                        if user:
                            resposta = await self.gerar_resposta(uid, "", trigger_dm=True)
                            data["last_interacted"] = agora.isoformat()
                            self._save_json()

                            dm_channel = await user.create_dm()
                            await self.enviar_resposta(dm_channel, resposta, uid)
                except Exception as e:
                    pass

    @random_dms_loop.before_loop
    async def before_random_dms(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ConversationSystem(bot))