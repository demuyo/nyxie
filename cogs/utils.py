# cogs/utils.py
import discord, random, json, unicodedata, string
from discord.ext import commands
from datetime import datetime, timedelta

# Carregar frases (se tiver)
def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

# Carregar todos
names = carregar_json("cogs/assets/names.json")
lines = carregar_json("cogs/assets/lines.json")
ddd = carregar_json("cogs/assets/ddd.json")
locations = carregar_json("cogs/assets/locations.json")
generic = carregar_json("cogs/assets/generic.json")

class utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def base_embed(self, title, description):
        # Lista de emojis/símbolos que já são usados manualmente
        emojis_existentes = [
            '⬇️', '📤', '✅', '❌', '⚠️', '📋', '🗑️',
            '👢', '🔨', '🔇', '🔊', '🔒', '🔓',
            '⏱️', '📊', '👥', '📢', '🛡️', '📝'
        ]
        
        # Símbolos estéticos (NÃO são emojis coloridos)
        simbolos_esteticos = ['⛧', '☿', '☾', '✦', '⸸', '⌇', '⟡', '✧', '⋆']
        
        # Verifica se o título JÁ TEM algum emoji/símbolo
        tem_emoji = False
        if title:
            for emoji in emojis_existentes:
                if emoji in title:
                    tem_emoji = True
                    break
        
        # SÓ adiciona símbolo se NÃO tiver emoji já
        if title and not tem_emoji and random.randint(1, 10) <= 6:
            simbolo = random.choice(simbolos_esteticos)
            # Adiciona só no final pra não conflitar
            title = f"{title} {simbolo}"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x1a1a1a
        )
        
        embed.set_footer(
            text=f"{random.choice(lines['frases'])}",
            icon_url=self.bot.user.avatar.url
        )
        
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def gerar_nome(self, gen: str = None, sobrenomes_qtd: int = None, lastname: str = None):
        sobrenomes_qtd = sobrenomes_qtd or random.randint(2, 3)

        sobrenomes_rand = random.sample(names["sobrenomes"], k=sobrenomes_qtd) 
        sobrenomes_str = " ".join(sobrenomes_rand)  
        ultimo_sobrenome = sobrenomes_rand[-1]

        gender = None
        if gen and gen.startswith("fem"):
            nome = random.choice(names["femininos"])
            gender = "Feminino"

        elif gen and gen.startswith("masc"):
            nome = random.choice(names["masculinos"])
            gender = "Masculino"

        else: 
            nome = random.choice(names["masculinos"] + names["femininos"])
            if nome in names["masculinos"]:
                gender = "Masculino"
            else: 
                gender = "Feminino"

        return f"{nome} {sobrenomes_str}", gender, ultimo_sobrenome
    
    def gerar_cpf(self):
    # Gera 9 dígitos aleatórios
        cpf = [random.randint(0, 9) for _ in range(9)]
        
        # Calcula 1º dígito verificador
        soma = sum(cpf[i] * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        cpf.append(digito1)
        
        # Calcula 2º dígito verificador
        soma = sum(cpf[i] * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        cpf.append(digito2)
        
        # Formata XXX.XXX.XXX-XX
        cpf_str = ''.join(map(str, cpf))
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    

    def gerar_data_nascimento(self, idade_min=18, idade_max=80):
        # Data de hoje
        hoje = datetime.now()
        
        # Calcula intervalo de anos
        ano_min = hoje.year - idade_max
        ano_max = hoje.year - idade_min
        
        # Gera ano aleatório
        ano = random.randint(ano_min, ano_max)
        
        # Gera mês e dia aleatórios
        mes = random.randint(1, 12)
        
        # Dias por mês (considerando ano bissexto)
        dias_por_mes = [31, 29 if ano % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        dia = random.randint(1, dias_por_mes[mes - 1])
        
        # Formata DD/MM/AAAA
        return f"{dia:02d}/{mes:02d}/{ano}"
    
    def gerar_data_nascimento(self, idade_c: int = None):
        hoje = datetime.now()
        idade_min = 18
        idade_max = 80

        if not idade_c:
            ano_min = hoje.year - idade_max
            ano_max = hoje.year - idade_min
            ano = random.randint(ano_min, ano_max)
        else:    
            ano = hoje.year - idade_c
        
        mes = random.randint(1, 12)
        dias_por_mes = [31, 29 if ano % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        dia = random.randint(1, dias_por_mes[mes - 1])

        data = f"{dia:02d}/{mes:02d}/{ano}"
        
        # Calcula idade
        hoje = datetime.now()
        idade = hoje.year - ano - ((hoje.month, hoje.day) < (mes, dia))

        signo = self.descobrir_signo(dia, mes)
        
        return dia, mes, ano, signo, idade, data

    def descobrir_signo(self, dia, mes):
        signos_datas = [
            ("Capricórnio", (12, 22), (1, 19)),
            ("Aquário", (1, 20), (2, 18)),
            ("Peixes", (2, 19), (3, 20)),
            ("Áries", (3, 21), (4, 19)),
            ("Touro", (4, 20), (5, 20)),
            ("Gêmeos", (5, 21), (6, 20)),
            ("Câncer", (6, 21), (7, 22)),
            ("Leão", (7, 23), (8, 22)),
            ("Virgem", (8, 23), (9, 22)),
            ("Libra", (9, 23), (10, 22)),
            ("Escorpião", (10, 23), (11, 21)),
            ("Sagitário", (11, 22), (12, 21))
        ]
        
        for signo, (mes_ini, dia_ini), (mes_fim, dia_fim) in signos_datas:
            if (mes == mes_ini and dia >= dia_ini) or (mes == mes_fim and dia <= dia_fim):
                return signo
        
        return "Capricórnio"  # Fallback

    
    def gerar_rg(self, estado=None):
        # Estados válidos
        estados = [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
            "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
            "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]
        
        # Se não passou estado, escolhe aleatório
        if not estado:
            estado = random.choice(estados)
        
        # Gera 8 dígitos
        rg = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        
        # Dígito verificador
        digito = random.choice([str(random.randint(0, 9)), 'X'])
        
        # Formata
        rg_formatado = f"{rg[:2]}.{rg[2:5]}.{rg[5:8]}-{digito}"
        
        return rg_formatado, f"SSP/{estado.upper()}"
    
    def gerar_cep(self, estado: str = None):
        if not estado:
            estado = random.choice(list(locations["enderecos"].keys()))
        
        # Se passou estado mas não existe
        if estado.upper() not in locations["enderecos"]:
            return ("Estado inválido! Use a sigla (SP, RJ, MG...)")
            
        endereco = random.choice(locations["enderecos"][estado.upper()])
        cep = endereco['cep']
        cidade = f"{endereco['cidade']}, {estado.upper()}"
        bairro = endereco['bairro']
        rua = f"{endereco['rua']}, {random.randint(1, 200)}"

        return cep, cidade, bairro, rua, estado

    def gerar_senha(self, base: str = None):
        simbolos = "!@#$%&*()-_=+[]"
        caracteres = string.ascii_letters + string.digits + simbolos
        
        if not base:
            senha = ''.join(random.choices(caracteres, k=random.randint(10, 14)))
        elif len(base) <= 3:
            senha = base + ''.join(random.choices(caracteres, k=random.randint(8, 12)))
        elif len(base) >= 4 <= 5:
            senha = base + ''.join(random.choices(caracteres, k=random.randint(6, 10)))
        else:
            senha = base + ''.join(random.choices(caracteres, k=random.randint(4, 8)))
        
        return senha


    def gerar_email(self, dominio=None):
        rand_sep = str(random.choice(["", ".", "-", "_"]))
        nome_completo, gender, _ = self.gerar_nome(None)

        # Remove os acentos
        nome_limpo = unicodedata.normalize('NFD', nome_completo).encode('ascii', 'ignore').decode('utf-8')
        
        # Monta o email base
        email_base = nome_limpo.replace(" ", rand_sep).lower()
        
        # Limita a 16 caracteres
        if len(email_base) > 16:
            email_base = email_base[:16]
        
        # ← REMOVE separador do final
        email_base = email_base.rstrip(".-_")
        
        # Domínio
        if not dominio:
            dominio = random.choice(generic["dominios"])
        elif "." not in dominio:
            dominio += ".com"
        
        email = f"{email_base}@{dominio}"
        
        return email
    
    def generic(self):
        cor_fav = random.choice(generic["cores"])
        peso = random.randint(50, 100)
        altura = f"1,{random.randint(50,99)}"
        tipo_sanguineo = random.choice(generic["tipos_sanguineos"])
        return cor_fav, peso, altura, tipo_sanguineo
    
    def gerar_telefone(self, ddd_in=None):
        # DDD
        if ddd_in:
            if ddd_in.isdigit():
                ddd_info = next((d for d in ddd["ddd"] if d["codigo"] == ddd_in), None)
                if not ddd_info:
                    raise ValueError(f"❌ DDD {ddd_in} não encontrado!")
            else:
                estado = ddd_in.upper()
                ddds_estado = [d for d in ddd["ddd"] if d["estado"] == estado]
                if not ddds_estado:
                    raise ValueError(f"❌ Estado {estado} não encontrado!")
                ddd_info = random.choice(ddds_estado)
        else:
            ddd_info = random.choice(ddd["ddd"])
        
        # Gera CELULAR
        segundo_num_cel = random.choice([7, 8, 9])
        resto_cel = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        celular = f"({ddd_info['codigo']}) 9{segundo_num_cel}{resto_cel[:3]}-{resto_cel[3:]}"
        
        # Gera FIXO
        primeiro_fixo = random.choice([2, 3, 4, 5])
        resto_fixo = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        fixo = f"({ddd_info['codigo']}) {primeiro_fixo}{resto_fixo[:3]}-{resto_fixo[3:]}"
        
        return celular, fixo, ddd_info

    def comando_help_embed(self, comando):
        """
        Gera embed de help para um comando específico
        
        Retorna None se comando não tiver docstring configurada
        """
        if not comando.help and not comando.brief and not comando.description:
            return None
        
        # Título
        nome = f"!{comando.name}"
        if comando.aliases:
            aliases = ", ".join([f"!{a}" for a in comando.aliases])
            titulo = f"{nome} (aliases: {aliases})"
        else:
            titulo = nome
        
        # Descrição principal
        descricao = comando.help or comando.brief or "sem descrição"
        
        embed = self.base_embed(titulo, descricao)
        
        # Uso/Sintaxe
        if comando.usage:
            embed.add_field(
                name="uso",
                value=f"`!{comando.name} {comando.usage}`",
                inline=False
            )
        
        # Exemplos (pega da docstring)
        if comando.description and "exemplo:" in comando.description.lower():
            partes = comando.description.split("exemplo:", 1)
            if len(partes) == 2:
                exemplos = partes[1].strip()
                # Remove linhas vazias extras
                exemplos = "\n".join([line for line in exemplos.split("\n") if line.strip()])
                embed.add_field(
                    name="exemplos",
                    value=f"```\n{exemplos}\n```",
                    inline=False
                )
        
        # Permissões necessárias
        perms = self._extrair_permissoes(comando)
        if perms:
            embed.add_field(
                name="permissões necessárias",
                value=", ".join(perms),
                inline=False
            )
        
        # Categoria (se tiver)
        if comando.cog_name:
            embed.add_field(
                name="categoria",
                value=comando.cog_name,
                inline=True
            )
        
        embed.set_footer(text="(obrigatório) [opcional] ⛧ !help para ver todos os comandos")
        
        return embed

    def _extrair_permissoes(self, comando):
        """Helper para extrair permissões de um comando"""
        if not hasattr(comando, 'checks') or not comando.checks:
            return []
        
        perms = []
        for check in comando.checks:
            if hasattr(check, '__name__'):
                nome = check.__name__
                if 'administrator' in nome:
                    perms.append("administrador")
                elif 'manage_guild' in nome:
                    perms.append("gerenciar Servidor")
                elif 'manage_channels' in nome:
                    perms.append("gerenciar Canais")
                elif 'manage_roles' in nome:
                    perms.append("gerenciar Cargos")
                elif 'manage_messages' in nome:
                    perms.append("gerenciar Mensagens")
                elif 'kick_members' in nome:
                    perms.append("expulsar Membros")
                elif 'ban_members' in nome:
                    perms.append("banir Membros")
                elif 'moderate_members' in nome:
                    perms.append("moderar Membros")
        
        return perms

    
async def setup(bot):
    await bot.add_cog(utils(bot))