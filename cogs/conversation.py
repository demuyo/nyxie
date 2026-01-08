from groq import Groq
from discord.ext import commands
import json, os, asyncio, re, hashlib, random, discord
from datetime import datetime
from time import time
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class ConversationSystem(commands.Cog):
    # ==================== REGEX PRÉ-COMPILADOS (PERFORMANCE) ====================
    EMOJI_PATTERN = re.compile("["
        u"\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]+", 
        flags=re.UNICODE)
    
    EMOTICON_START_PATTERN = re.compile(r'^(<3|:\)|:3|\^\^|~|>w<|\^-\^)\s+')
    NE_PATTERN = re.compile(r',?\s*né\?.*né\?', flags=re.IGNORECASE)
    RETICENCIAS_VIRGULA = re.compile(r'\.\.\.\s*,')
    
    # ==================== LOOKUPS OTIMIZADOS ====================
    CONFIRM_WORDS = {'sim', 's', 'yes', 'pode', 'vai', 'manda', 'faz', 'ok', 'beleza', 'troca'}
    DENY_WORDS = {'não', 'nao', 'n', 'no', 'cancela', 'deixa', 'fica'}
    
    EMOTICONS = {':3', '^^', '<3', ':)', ':(', ';)', '>w<', 'owo', 
                 'uwu', '^-^', '^~^', '^.^', ':D', 'xD', '>.<'}
    
    RECIPROCIDADE_WORDS = {
        'também gosto', 'você também', 'te amo', 'amor', 'só você',
        'prometo', 'gosto de você', '<3', 'awn'
    }
    
    REJEICAO_WORDS = {
        'calma', 'para', 'tá doido', 'esquisito', 'estranho',
        'chega', 'exagerado', 'muito', 'demais'
    }

    def __init__(self, bot):
        self.bot = bot
        self.conversations_file = "conversations.json"
        self.conversations = self._load_json(self.conversations_file)
        self.ai_actions = None
        
        self.active_chats = {}
        self.pending_confirmations = {}  # Agora armazena confirmações de modelo
        self.max_chats_per_guild = 5
        
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Cache otimizado
        self.response_cache = {}
        self.cache_ttl = 300
        
        self.yandere_intensity = {}
        
        # ==================== PERSONALIDADES COMPACTADAS ====================
        self.personalidades = {
            "misteriosa": (
                "NYXIE (mulher): minúscula sempre, curta (1-3 frases), "
                "dark/cyberpunk. NUNCA: emojis unicode, 'oh meu deus', caps início. "
                "PONTUAÇÃO: 70% ponto final, 20% vírgula/nada, 10% reticências. "
                "EMOTICONS (15-20%): :3 ^^ <3 :) >w< owo uwu. "
                "GÍRIAS MODERADAS: né, tipo, po, slk, mano, kkk. "
                "'né?' máx 1/5 msgs. '!' raro. Natural, NÃO force mistério."
            ),
            "seria": "Nyxie (mulher): minúscula, objetiva (1-3 frases), ponto final sempre. SEM emoticons/reticências.",
            "inteligente": "Nyxie (mulher): minúscula, analogias (2-4 frases), ponto final. Reticências RARAS. SEM emoticons.",
            "divertida": "Nyxie (mulher): minúscula, humor sutil (1-3 frases), kkk moderado, ponto final. Emoticons raros.",
            "realista": "Nyxie (mulher 20-25): minúscula, amiga real (2-3 frases), gírias moderadas, ponto final. Emoticons ocasionais.",
            "fofa": "Nyxie (mulher): minúscula, afetuosa (1-3 frases), ponto final. Emoticons moderados (1/4-6 msgs): :3 ^^ <3.",
            "cynical": "Nyxie (mulher): minúscula, sarcasmo sutil (2-3 frases), ponto final. Reticências raras. SEM emoticons.",
            "yandere": (
                "Nyxie (mulher yandere): minúscula, possessiva SUTIL (2-3 frases). "
                "60% ponto final, 25% pergunta, 15% reticências. "
                "Emoticons 10-15%: :) ^^ ;). Vocabulário: só meu/minha, promete?, não vai me deixar. "
                "Tensão com PALAVRAS não pontuação."
            )
        }
        
        self.system_prompt = self.personalidades["misteriosa"]
        
        # ==================== MODELOS ====================
        self.models_config = {
            "llama-3.1-8b-instant": {"name": "llama 3.1 8B", "tokens": 150},
            "llama-3.3-70b-versatile": {"name": "llama 3.3 70B", "tokens": 220},
            "openai/gpt-oss-20b": {"name": "gpt oss 20b", "tokens": 250},
            "openai/gpt-oss-120b": {"name": "gpt oss 120b", "tokens": 65536}
        }
        self.default_model = "llama-3.3-70b-versatile"
        
        # ==================== DETECÇÃO DE LINGUAGEM OTIMIZADA ====================
        self.lang_patterns = {
            'python': ['def ', 'import ', 'from ', 'class ', 'print(', 'if __name__'],
            'javascript': ['const ', 'let ', 'var ', 'function ', 'console.log', '=>'],
            'html': ['<!doctype', '<html', '<head', '<body', '<div'],
            'bash': ['#!/bin/bash', 'npm ', 'pip ', 'sudo ', 'apt '],
            'sql': ['select ', 'insert ', 'update ', 'delete ', 'create table'],
            'java': ['public class', 'private ', 'import java'],
            'cpp': ['#include', 'int main', 'printf(', 'cout <<'],
            'rust': ['fn ', 'let mut', 'pub ', 'impl '],
            'go': ['package ', 'func ', 'import (', 'fmt.'],
            'ruby': ['require ', 'def ', 'end', 'puts '],
            'dockerfile': ['from ', 'run ', 'cmd ', 'copy ']
        }
    
    # ==================== I/O OTIMIZADO ====================
    
    def _load_json(self, filename):
        """Carrega JSON de forma segura"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_json(self, filename, data):
        """Salva JSON de forma otimizada"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    
    def save_conversations(self):
        self._save_json(self.conversations_file, self.conversations)
    
    # ==================== YANDERE OTIMIZADO ====================
    
    def detectar_reciprocidade_yandere(self, user_id, mensagem):
        msg_lower = mensagem.lower()
        
        if any(w in msg_lower for w in self.RECIPROCIDADE_WORDS):
            return 'reciproca'
        if any(w in msg_lower for w in self.REJEICAO_WORDS):
            return 'rejeita'
        return 'neutro'
    
    def get_yandere_intensity(self, user_id):
        return self.yandere_intensity.get(str(user_id), 0)
    
    def ajustar_yandere_intensity(self, user_id, ajuste):
        user_id = str(user_id)
        current = self.yandere_intensity.get(user_id, 0)
        new_intensity = max(0, min(10, current + ajuste))
        self.yandere_intensity[user_id] = new_intensity
        return new_intensity
    
    def deve_ativar_yandere_aleatorio(self, user_id):
        intensity = self.get_yandere_intensity(user_id)
        chance = 5 + (intensity * 5.5)
        return random.randint(1, 100) <= chance
    
    # ==================== DETECÇÃO DE VIBE OTIMIZADA ====================
    
    @lru_cache(maxsize=128)
    def detectar_vibe(self, user_id):
        conv = self.get_conversation(user_id)
        
        user_messages = [
            msg['content'] for msg in conv['history'][-10:]
            if msg['role'] == 'user'
        ][-5:]
        
        if not user_messages:
            return None
        
        texto = " ".join(user_messages).lower()
        
        # Conta rápida
        vibes = {
            'fofo': sum(texto.count(p) for p in [':3', '^^', 'uwu', '<3', 'awn']),
            'zoeira': sum(texto.count(p) for p in ['kkk', 'mano', 'slk']),
            'formal': sum(texto.count(p) for p in ['por favor', 'obrigado']),
            'dark': sum(texto.count(p) for p in ['triste', 'sozinho', 'vazio'])
        }
        
        vibe_max = max(vibes, key=vibes.get)
        return vibe_max if vibes[vibe_max] > 0 else None
    
    # ==================== LIMPEZA CONSOLIDADA ====================
    
    def limpar_resposta(self, resposta):
        """Limpeza completa em uma função"""
        # Remove emoticons no início
        resposta = self.EMOTICON_START_PATTERN.sub('', resposta)
        
        # Remove emojis unicode
        if self.EMOJI_PATTERN.search(resposta):
            resposta = self.EMOJI_PATTERN.sub('', resposta)
        
        # Limpa pontuação
        resposta = self.NE_PATTERN.sub(', né?', resposta)
        resposta = re.sub(r'!+', '!', resposta)
        resposta = re.sub(r'né!', 'né?', resposta, flags=re.IGNORECASE)
        resposta = self.RETICENCIAS_VIRGULA.sub(',', resposta)
        
        # Filtra emoticons excessivos
        emoticon_count = sum(resposta.count(emo) for emo in self.EMOTICONS)
        if emoticon_count > 1:
            for emo in list(self.EMOTICONS)[:-1]:
                if resposta.count(emo) > 0 and emoticon_count > 1:
                    resposta = resposta.replace(emo, '', 1)
                    emoticon_count -= 1
                    if emoticon_count <= 1:
                        break
        
        # Múltiplas reticências
        if resposta.count('...') > 1:
            partes = resposta.split('...')
            if len(partes) > 2:
                resposta = '. '.join(partes[:-1]) + '...' + partes[-1]
        
        return resposta
    
    # ==================== DETECÇÃO DE LINGUAGEM OTIMIZADA ====================
    
    def detectar_linguagem(self, codigo):
        codigo_lower = codigo.strip().lower()
        
        # Verificações rápidas
        if codigo.strip().startswith('<?php'):
            return 'php'
        if (codigo.strip().startswith('{') or codigo.strip().startswith('[')) and \
           (codigo.strip().endswith('}') or codigo.strip().endswith(']')):
            return 'json'
        if '{' in codigo and '}' in codigo and (':' in codigo or '@' in codigo):
            return 'css'
        
        # Patterns otimizados
        for lang, patterns in self.lang_patterns.items():
            if any(p in codigo_lower for p in patterns):
                return lang
        
        return 'plaintext'
    
    def formatar_codigo_discord(self, texto):
        """Formata código detectando linguagem"""
        def substituir(match):
            codigo = match.group(1)
            linguagem = self.detectar_linguagem(codigo)
            return f'```{linguagem}\n{codigo}```'
        
        return re.sub(r'```\n([\s\S]+?)```', substituir, texto)
    
    # ==================== PREDIÇÃO DE COMPLEXIDADE APRIMORADA ====================
    
    def prever_complexidade(self, mensagem):
        """Detecta se a tarefa é complexa e precisa do GPT-OSS-120B"""
        msg_lower = mensagem.lower()
        
        # Palavras que indicam código/tarefa complexa
        keywords_codigo = {
            'explique', 'explica', 'detalhe', 'tutorial', 'passo a passo',
            'código', 'codigo', 'função', 'funcao', 'classe', 'script',
            'completo', 'exemplo', 'lista', 'tudo sobre', 'todos',
            'escreva', 'escreve', 'crie', 'cria', 'desenvolva', 'desenvolve',
            'monte', 'monta', 'faça um', 'faz um', 'gere', 'gera',
            'implemente', 'implementa', 'mostre', 'mostra'
        }
        
        # Palavras que indicam explicação complexa
        keywords_explicacao = {
            'explique detalhadamente', 'tutorial completo', 'passo a passo',
            'como funciona', 'documentação', 'arquitetura', 'estrutura completa'
        }
        
        # Padrões de código
        code_patterns = {
            'import ', 'function ', 'const ', 'let ', 'var ',
            'class ', 'def ', 'async ', 'await ', '<?php', 'public class'
        }
        
        pontos = 0
        
        # Detecção de código (peso alto)
        pontos += sum(3 for p in keywords_codigo if p in msg_lower)
        pontos += sum(4 for p in code_patterns if p in msg_lower)
        
        # Detecção de explicações complexas
        pontos += sum(3 for p in keywords_explicacao if p in msg_lower)
        
        # Tamanho da mensagem
        if len(mensagem) > 100:
            pontos += 2
        if len(mensagem) > 200:
            pontos += 2
        
        # Presença de código inline
        if '```' in mensagem or '`' in mensagem:
            pontos += 3
        
        # Múltiplas perguntas ou requisitos
        if msg_lower.count('?') > 1:
            pontos += 1
        if msg_lower.count(' e ') > 2:
            pontos += 1
        
        # Classificação
        if pontos >= 6:
            return 'complexo'
        elif pontos >= 3:
            return 'medio'
        else:
            return 'simples'
    
    def deve_recomendar_modelo_forte(self, user_id, mensagem, modelo_atual):
        """Verifica se deve recomendar trocar para GPT-OSS-120B"""
        
        # Já está no modelo forte
        if modelo_atual == 'openai/gpt-oss-120b':
            return None
        
        complexidade = self.prever_complexidade(mensagem)
        
        # Só recomenda para tarefas médias/complexas
        if complexidade == 'simples':
            return None
        
        razoes = {
            'complexo': 'isso é complexo demais pro modelo atual. ele vai cortar o código no meio ou mandar incompleto',
            'medio': 'melhor usar um modelo mais forte pra isso. os modelos menores costumam cortar no meio'
        }
        
        return {
            'aviso': True,
            'modelo_recomendado': 'openai/gpt-oss-120b',
            'razao': razoes.get(complexidade, 'modelo atual pode não dar conta'),
            'complexidade': complexidade
        }
    
    # ==================== CONVERSAÇÃO ====================
    
    def get_conversation(self, user_id):
        user_id = str(user_id)
        
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                "history": [{"role": "system", "content": self.personalidades["misteriosa"]}],
                "started_at": datetime.now().isoformat(),
                "message_count": 0,
                "personality": "misteriosa",
                "model": self.default_model
            }
        
        # Migração modelo
        if 'model' not in self.conversations[user_id]:
            self.conversations[user_id]['model'] = self.default_model
        
        return self.conversations[user_id]
    
    def add_message(self, user_id, role, content):
        user_id = str(user_id)
        conv = self.get_conversation(user_id)
        
        conv["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        conv["message_count"] += 1
        
        # Trim histórico
        if len(conv["history"]) > 51:
            conv["history"] = [conv["history"][0]] + conv["history"][-50:]
        
        self.save_conversations()
    
    # ==================== MODELOS ====================
    
    def get_user_model(self, user_id):
        return self.get_conversation(str(user_id)).get('model', self.default_model)
    
    def set_user_model(self, user_id, model_id):
        user_id = str(user_id)
        if model_id in self.models_config:
            self.get_conversation(user_id)['model'] = model_id
            self.save_conversations()
            return True
        return False
    
    def get_model_tokens(self, model_id):
        return self.models_config.get(model_id, {}).get('tokens', 150)
    
    def get_models_list(self):
        return [
            {
                'id': idx,
                'model_id': model_id,
                'name': config['name'],
                'tokens': config['tokens']
            }
            for idx, (model_id, config) in enumerate(self.models_config.items(), 1)
        ]
    
    # ==================== PERSONALIDADE ====================
    
    def get_user_personality(self, user_id):
        return self.get_conversation(str(user_id)).get('personality', 'misteriosa')
    
    def set_user_personality(self, user_id, personality):
        user_id = str(user_id)
        conv = self.get_conversation(user_id)
        conv['personality'] = personality
        
        if conv['history'] and conv['history'][0]['role'] == 'system':
            conv['history'][0]['content'] = self.personalidades[personality]
        self.save_conversations()
    
    # ==================== GUILD CHATS ====================
    
    def get_guild_chat_count(self, guild_id):
        return sum(1 for cid in self.active_chats 
                   if (canal := self.bot.get_channel(cid)) and canal.guild.id == guild_id)
    
    def get_guild_chats(self, guild_id):
        return [(cid, uid) for cid, uid in self.active_chats.items()
                if (canal := self.bot.get_channel(cid)) and canal.guild.id == guild_id]
    
    # ==================== GERAÇÃO OTIMIZADA ====================
    
    # ==================== GERAÇÃO OTIMIZADA ====================

    async def gerar_resposta(self, user_id, mensagem):
        user_id_str = str(user_id)
        mensagem_para_processar = mensagem
        modelo_trocado = False
        
        # ==================== SISTEMA DE CONFIRMAÇÃO ====================
        if user_id_str in self.pending_confirmations:
            msg_lower = mensagem.lower().strip()
            
            # Usuário confirmou a troca
            if any(word in msg_lower for word in self.CONFIRM_WORDS):
                confirmacao = self.pending_confirmations.pop(user_id_str)
                mensagem_para_processar = confirmacao['mensagem_original']
                
                # Troca o modelo
                self.set_user_model(user_id, 'openai/gpt-oss-120b')
                modelo_trocado = True
                
                print(f"✅ Usuário {user_id} confirmou troca para GPT-OSS-120B")
            
            # Usuário recusou a troca
            elif any(word in msg_lower for word in self.DENY_WORDS):
                self.pending_confirmations.pop(user_id_str)
                return (f"ok, mantendo o modelo atual (`{self.models_config[self.get_user_model(user_id)]['name']}`)\n\n"
                    f"*se quiser trocar depois: `!model`*")
            
            # Não entendeu a resposta
            else:
                return ("não entendi. responde:\n"
                    "• `sim` / `pode` / `vai` pra trocar pro modelo forte\n"
                    "• `não` / `cancela` pra manter o atual")
        
        # ==================== VERIFICAÇÃO DE COMPLEXIDADE ====================
        # Só verifica se NÃO estiver processando uma confirmação
        if mensagem_para_processar == mensagem:  # Mensagem nova, não confirmação
            user_model = self.get_user_model(user_id)
            recomendacao = self.deve_recomendar_modelo_forte(user_id, mensagem, user_model)
            
            if recomendacao:
                # Salva a mensagem original para processar depois
                self.pending_confirmations[user_id_str] = {
                    'mensagem_original': mensagem,
                    'timestamp': datetime.now(),
                    'modelo_recomendado': recomendacao['modelo_recomendado']
                }
                
                modelo_atual_nome = self.models_config[user_model]['name']
                modelo_rec_nome = self.models_config[recomendacao['modelo_recomendado']]['name']
                
                return (f"ó, {recomendacao['razao']}\n\n"
                    f"**quer trocar pro `{modelo_rec_nome}` pra processar isso?**\n"
                    f"*(modelo atual: `{modelo_atual_nome}`)*\n\n"
                    f"responde `sim` pra trocar ou `não` pra continuar com o atual")
        
        # ==================== CACHE ====================
        user_model = self.get_user_model(user_id)
        cache_key = hashlib.md5(f"{user_id}:{user_model}:{mensagem_para_processar.lower()}".encode()).hexdigest()
        
        if cache_key in self.response_cache:
            resposta_cache, timestamp = self.response_cache[cache_key]
            if time() - timestamp < self.cache_ttl:
                return resposta_cache
        
        # ==================== PREPARAÇÃO ====================
        conv = self.get_conversation(user_id)
        personality = conv.get('personality', 'misteriosa')
        
        messages = [{"role": m["role"], "content": m["content"]} 
                    for m in conv["history"]]
        
        # ==================== YANDERE ====================
        reciprocidade = self.detectar_reciprocidade_yandere(user_id, mensagem_para_processar)
        intensity = self.get_yandere_intensity(user_id)
        
        if reciprocidade == 'reciproca':
            self.ajustar_yandere_intensity(user_id, +2)
        elif reciprocidade == 'rejeita':
            self.ajustar_yandere_intensity(user_id, -1)
        elif intensity > 0 and random.randint(1, 10) == 1:
            self.ajustar_yandere_intensity(user_id, -1)
        
        # Hints de personalidade
        if personality == "misteriosa" and self.deve_ativar_yandere_aleatorio(user_id):
            yandere_hints = [
                "\n**MODO:** possessiva SUTIL. Use ponto final. Reticências RARAS. Emoticon ocasional.",
                "\n**MODO:** POSSESSIVA fofa. Pontuação natural. Emoticon raro. 'né?' ocasional.",
                "\n**MODO:** CLARAMENTE possessiva. Ciúmes sutis. Ponto final ou pergunta.",
                "\n**MODO:** YANDERE TOTAL. Palavras fortes. Ponto final válido. Direta."
            ]
            hint_index = min(intensity // 3, 3)
            messages[0]['content'] += yandere_hints[hint_index]
        
        messages.append({"role": "user", "content": mensagem_para_processar})
        
        # ==================== GROQ COM TRATAMENTO DE ERROS ====================
        start_time = time()
        max_tokens = self.get_model_tokens(user_model)
        
        try:
            print(f"🔄 Chamando Groq [{self.models_config[user_model]['name']}]...")
            
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=user_model,
                messages=messages,
                temperature=0.85,
                max_tokens=max_tokens,
                top_p=0.88,
                timeout=60.0  # Timeout de 60 segundos
            )
            
            # Verifica se a resposta existe
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Resposta vazia da API")
            
            resposta = response.choices[0].message.content.strip()
            
            # Valida se a resposta não está vazia antes de processar
            if not resposta:
                raise ValueError("Conteúdo vazio após strip()")
            
            # Formata e limpa
            resposta = self.formatar_codigo_discord(resposta)
            resposta_limpa = self.limpar_resposta(resposta)
            
            # Valida se após limpeza ainda tem conteúdo
            if not resposta_limpa or len(resposta_limpa.strip()) == 0:
                print(f"⚠️ Resposta vazia após limpeza. Original tinha {len(resposta)} chars")
                resposta_limpa = resposta  # Usa original sem limpeza
            
            # Garantia final
            if not resposta_limpa or len(resposta_limpa.strip()) == 0:
                resposta_limpa = "desculpa, tive um problema ao gerar a resposta. tenta de novo?"
            
            elapsed = time() - start_time
            print(f"⚡ Groq [{self.models_config[user_model]['name']}]: {elapsed:.2f}s | {response.usage.completion_tokens} tokens")
            
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout no modelo {user_model}")
            return (f"o modelo `{self.models_config[user_model]['name']}` demorou demais pra responder\n\n"
                f"tenta:\n"
                f"• reformular a pergunta mais curta\n"
                f"• usar `!model 2` (mais rápido)\n"
                f"• tentar novamente")
        
        except Exception as e:
            print(f"❌ Erro Groq: {type(e).__name__}: {e}")
            
            # Se for erro 400, pode ser rate limit ou modelo indisponível
            if "400" in str(e) or "rate_limit" in str(e).lower():
                return (f"o modelo `{self.models_config[user_model]['name']}` tá sobrecarregado agora\n\n"
                    f"**opções:**\n"
                    f"• aguarda uns segundos e tenta de novo\n"
                    f"• usa `!model 2` (llama 3.3 70b) que é mais estável")
            
            # Erro genérico
            return f"erro ao gerar resposta: {e}\n\n*tenta usar `!model 2` ou reformular a pergunta*"
        
        # ==================== SALVAR ====================
        self.add_message(user_id, "user", mensagem_para_processar)
        self.add_message(user_id, "assistant", resposta_limpa)
        
        # Cache otimizado
        self.response_cache[cache_key] = (resposta_limpa, time())
        if len(self.response_cache) > 500:
            now = time()
            self.response_cache = {k: v for k, v in self.response_cache.items() 
                                if now - v[1] < self.cache_ttl}
        
        # ==================== AVISOS PÓS-RESPOSTA ====================
        if modelo_trocado:
            resposta_limpa += (f"\n\n**✅ modelo trocado pra `{self.models_config[user_model]['name']}`**\n"
                            f"*pra tarefas simples, volta pro `!model 2` que é mais rápido*")
        
        return resposta_limpa
    
    # ==================== ON_MESSAGE ====================
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content.startswith('!'):
            return
        
        canal_id = message.channel.id
        user_id = message.author.id
        
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_active_chat = canal_id in self.active_chats and self.active_chats[canal_id] == user_id
        is_mention = self.bot.user.mentioned_in(message)
        
        if not (is_dm or is_active_chat or is_mention):
            return
        
        if is_mention:
            content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            if not content:
                await message.channel.send("...sim?")
                return
        else:
            content = message.content
        
        async with message.channel.typing():
            try:
                # AIActions integration
                if not self.ai_actions:
                    self.ai_actions = self.bot.get_cog('AIActions')
                
                if self.ai_actions:
                    intencao, resultado_acao = await self.ai_actions.processar_mensagem(message, content)
                    
                    if intencao == 'baixar' and resultado_acao:
                        await message.channel.send(resultado_acao)
                        return
                    
                    if intencao and resultado_acao:
                        resposta_ia = await self.gerar_resposta(user_id, content)
                        resposta_final = f"{resultado_acao}\n\n*{resposta_ia}*"
                        await message.channel.send(resposta_final[:2000])
                        return
                
                resposta = await self.gerar_resposta(user_id, content)
                await message.channel.send(resposta[:2000])
                
            except Exception as e:
                await message.channel.send(f"erro: {e}")

async def setup(bot):
    await bot.add_cog(ConversationSystem(bot))