"""
🩻 Extração bruta de conteúdo. Cada fonte (Fextralife, MediaWiki, Kiranico)
tem seu próprio "extrator" que sabe achar o bloco de conteúdo, o texto de
categoria e a imagem de destaque — tudo mais daqui pra frente é genérico.
"""

import re
from .data import (
    CATEGORY_ORDER, CATEGORIES,
    CONTENT_SIGNATURE_ORDER, CONTENT_SIGNATURES,
    KIRANICO_URL_CATEGORY_MAP,
)

_SUFIXO_JOGO_REGEX = re.compile(r'\s*\([A-Z]{2,8}\)\s*$')


# ────────────────────────────────────────────────────────────────
# 🖼️  IMAGEM DE DESTAQUE
# ────────────────────────────────────────────────────────────────

def extract_og_image(soup):
    """extrai a imagem principal via og:image/twitter:image — padrão usado
    por praticamente todo site moderno pra gerar preview de link, evita ter
    que adivinhar a classe CSS específica de cada wiki."""
    og = soup.find('meta', property='og:image')
    if og and og.get('content'):
        return og['content']

    tw = soup.find('meta', attrs={'name': 'twitter:image'})
    if tw and tw.get('content'):
        return tw['content']

    return None


# ────────────────────────────────────────────────────────────────
# 🧼  LIMPEZA
# ────────────────────────────────────────────────────────────────

def replace_images_with_text(soup):
    """Lê as imagens e converte para Emojis precisos ou DELETA o lixo impiedosamente"""
    element_map = {
        "fire": ("(🔥)", "Fire"), "water": ("(💧)", "Water"), "thunder": ("(⚡)", "Thunder"),
        "ice": ("(❄️)", "Ice"), "dragon": ("(🐉)", "Dragon"), "poison": ("(☠️)", "Poison"),
        "blast": ("(💥)", "Blastblight"), "sleep": ("(💤)", "Sleep"), "paralysis": ("(🟡)", "Paralysis"),
        "stun": ("(💫)", "Stun"), "attack": ("(⚔️)", "Attack"), "affinity": ("(✨)", "Affinity"),
        "defense": ("(🛡️)", "Defense"), "sharpness": ("(🗡️)", "Sharpness"), "slot": ("(💠)", "Slot"),
        "zenny": ("(🪙)", ""), "research": ("(🔬)", ""), "gem": ("(💎)", ""),
        "rarity": ("(🌟)", "Rarity"), "decoration": ("(💠)", "Decoration"),
        "star": ("⭐", ""), "cut": ("(🔪)", "Cut"), "sever": ("(🔪)", "Sever"),
        "blunt": ("(🔨)", "Blunt"), "ammo": ("(🏹)", "Ammo"), "check": ("✅", ""), "cross": ("❌", ""),
        "element": ("(🌟)", "Element"),
    }

    for img in soup.find_all('img'):
        alt_text = img.get('alt', '').strip().lower()
        src_text = img.get('src', '').lower()
        title_text = img.get('title', '').strip().lower()

        substituido = False
        for key, (emoji, name) in element_map.items():
            if key in alt_text or key in src_text or key in title_text:
                parent_text = img.parent.get_text(separator=" ", strip=True).lower() if img.parent else ""

                if name and name.lower() in parent_text:
                    img.replace_with(f" {emoji} ")
                else:
                    insert_text = f" {emoji} {name} " if name else f"{emoji}"
                    img.replace_with(insert_text)

                substituido = True
                break

        if substituido:
            continue

        # 🕯️ fallback: ícones sem alt/title próprios (comum em MediaWiki) costumam
        # morar dentro de um <a title="..."> que carrega o nome de verdade
        # (ex: title="Attack (MHWI)"). aproveita esse texto em vez de decompor.
        pai_link = img.find_parent('a')
        if pai_link and pai_link.get('title', '').strip():
            texto_limpo = _SUFIXO_JOGO_REGEX.sub('', pai_link['title']).strip()
            if texto_limpo:
                img.replace_with(f" {texto_limpo} ")
                continue

        img.decompose()


def clean_page_junk(content_block):
    """Oblitera textos inúteis padronizados da wiki, mas NUNCA mexe em blocos
    que escondem tabelas importantes lá dentro (senão mata a tabela junto)."""
    junk_phrases = [
        "legend explanation", "credits to", "armor and weapons related to",
        "each ⭐ star shown below represents", "each star shown below represents",
        "detailed weakness information", "notes and tips go here", "below is an excerpt",
        "starting equipment for the", "weapon tree", "crafting and upgrades", "upgrade tree",
        "each ⭐star shown below represents",
    ]

    junk_regex = re.compile(
        r"(is a .* weapon in monster hunter world)|"
        r"(all weapons have unique properties relating to)|"
        r"(please see weapon mechanics)|"
        r"(is part of an upgrade path)|"
        r"(this weapon has)|"
        r"(crafted specifically for)",
        re.IGNORECASE
    )

    for navbox in content_block.find_all('table'):
        if '♦' in navbox.get_text():
            navbox.decompose()

    for p in content_block.find_all(['p', 'span', 'div', 'h2', 'h3', 'h4']):
        # 🛡️ blindagem: se tem tabela enterrada aqui dentro, NUNCA decompõe
        if p.find('table'):
            continue

        text = p.get_text().lower()
        if any(junk in text for junk in junk_phrases) or junk_regex.search(text):
            p.decompose()


# ────────────────────────────────────────────────────────────────
# 🕵️  DETECÇÃO DE CATEGORIA
# ────────────────────────────────────────────────────────────────

def detectar_categoria_breadcrumb(breadcrumb_text):
    for chave in CATEGORY_ORDER:
        cfg = CATEGORIES[chave]
        if any(pista in breadcrumb_text for pista in cfg["breadcrumbs"]):
            return chave
    return "generic"


def detectar_categoria_por_conteudo(texto_lower):
    """🕯️ fallback heurístico best-effort — só usado quando não há breadcrumb
    nem URL confiável pra decidir a categoria."""
    for categoria in CONTENT_SIGNATURE_ORDER:
        assinaturas = CONTENT_SIGNATURES.get(categoria, [])
        if any(assinatura in texto_lower for assinatura in assinaturas):
            return categoria
    return "generic"


def detectar_categoria_kiranico_por_url(url):
    m = re.search(r'/data/([a-z\-]+)/', url)
    if not m:
        return "generic"
    return KIRANICO_URL_CATEGORY_MAP.get(m.group(1), "generic")


# ────────────────────────────────────────────────────────────────
# 🔎  EXTRATORES POR FONTE
# ────────────────────────────────────────────────────────────────

def extrator_fextralife(soup):
    content_block = soup.find('div', id='wiki-content-block') or soup.body
    breadcrumbs = soup.find('div', id='breadcrumbs-container')
    breadcrumb_text = breadcrumbs.get_text().lower() if breadcrumbs else ""
    thumbnail_url = extract_og_image(soup)
    return content_block, breadcrumb_text, thumbnail_url


def extrator_mediawiki(soup):
    """baseado em amostra real de página de arma (monsterhunterwiki.org).
    essa wiki não expõe catlinks confiável, então a categoria é detectada
    por assinatura de conteúdo lá no parser."""
    content_block = soup.find('div', id='mw-content-text') or soup.body
    if content_block is None:
        return None, "", None

    # a barra de navegação do site inteiro vem embutida em TODA página como
    # template — sem remover, ela polui "informações gerais" de todo scan.
    for nav in content_block.find_all('div', class_=['navbarheader', 'navbar-green']):
        nav.decompose()

    breadcrumb_text = ""

    thumbnail_url = extract_og_image(soup)
    if not thumbnail_url:
        img = content_block.find('img')
        if img and img.get('src'):
            src = img['src']
            thumbnail_url = src if src.startswith('http') else f"https://monsterhunterwiki.org{src}"

    return content_block, breadcrumb_text, thumbnail_url


def extrator_kiranico(soup):
    """⚠️ beta — renderizado no servidor, mas a tabela de status usa <thead>
    vazio (rótulos montados via Alpine.js no navegador). título/descrição/
    imagem são confiáveis; leitura de stats é posicional (ver
    processar_stats_kiranico) e baseada em uma única amostra até agora."""
    article = soup.find('article') or soup.body
    if article is None:
        return None, "", None

    thumbnail_url = extract_og_image(soup)
    if not thumbnail_url:
        img_container = article.find('div', attrs={'aria-hidden': 'true'})
        if img_container:
            img = img_container.find('img')
            if img and img.get('src'):
                thumbnail_url = img['src']

    # "eyebrow" acima do título costuma ser genérico ("Section") — a
    # categoria de verdade vem da URL (detectar_categoria_kiranico_por_url)
    eyebrow = ""
    header = article.find('header')
    if header:
        eyebrow_tag = header.find('p')
        if eyebrow_tag:
            eyebrow = eyebrow_tag.get_text(strip=True).lower()

    return article, eyebrow, thumbnail_url


EXTRACTOR_FUNCS = {
    "fextralife": extrator_fextralife,
    "mediawiki": extrator_mediawiki,
    "kiranico": extrator_kiranico,
}


# ────────────────────────────────────────────────────────────────
# 🧾  TABELAS — fextralife (genérico + fraquezas especiais)
# ────────────────────────────────────────────────────────────────

def tentar_tabela_ailment(grade, raw_sections):
    if len(grade) < 2 or "ailment" not in grade[0][0].lower() or "weakness" not in grade[1][0].lower():
        return False

    raw_sections["fraquezas & status"].append("✦ **Ailment Weakness**:")
    for i in range(1, len(grade[0])):
        ail = grade[0][i] if i < len(grade[0]) else "—"
        estrelas = grade[1][i] if i < len(grade[1]) else "—"
        raw_sections["fraquezas & status"].append(f"⟡ **{ail}**: {estrelas}")
    raw_sections["fraquezas & status"].append("")
    return True


def tentar_tabela_weakpoint(grade, raw_sections):
    if len(grade) < 2 or "weak point" not in grade[0][0].lower():
        return False

    raw_sections["fraquezas & status"].append("✦ **Damage Type Weakness**:")
    for row_idx in range(1, len(grade)):
        linha = grade[row_idx]
        parte = linha[0]
        fraquezas = []
        for i in range(1, len(linha)):
            dmg_type = grade[0][i] if i < len(grade[0]) else "—"
            fraquezas.append(f"{dmg_type} {linha[i]}")
        raw_sections["fraquezas & status"].append(f"⟡ **{parte}**: {' | '.join(fraquezas)}")
    raw_sections["fraquezas & status"].append("")
    return True


def processar_tabela(tabela, raw_sections, secao_atual, category):
    rows = tabela.find_all('tr')
    grade = []
    for row in rows:
        cols = []
        for c in row.find_all(['th', 'td']):
            ctext = re.sub(r'\s+', ' ', c.get_text(separator=" ", strip=True)).strip()
            cols.append(ctext if ctext else "—")
        if cols and any(x != "—" for x in cols):
            grade.append(cols)

    if not grade:
        return

    if category == "monster":
        if tentar_tabela_ailment(grade, raw_sections):
            return
        if tentar_tabela_weakpoint(grade, raw_sections):
            return

    for cols in grade:
        if len(cols) == 2:
            raw_sections[secao_atual].append(f"✦ **{cols[0]}**: {cols[1]}")
        elif len(cols) > 2:
            raw_sections[secao_atual].append(f"✦ **{cols[0]}** | {' | '.join(cols[1:])}")
        elif len(cols) == 1:
            raw_sections[secao_atual].append(f"✦ **{cols[0]}**")
    raw_sections[secao_atual].append("")


# ────────────────────────────────────────────────────────────────
# 🧾  TABELAS — MediaWiki
# ────────────────────────────────────────────────────────────────

def extrair_sharpness_mediawiki(celula):
    """as barras de sharpness dessa wiki não têm texto visível — a info real
    mora nos atributos data-orig/title de cada segmento colorido."""
    barras = celula.find_all('div', attrs={'data-orig': True})
    if not barras:
        return None

    partes, vistos = [], set()
    for barra in barras:
        titulo = barra.get('title', '').strip()
        if titulo and titulo not in vistos:
            vistos.add(titulo)
            partes.append(titulo)

    return " | ".join(partes) if partes else None


def processar_tabela_mediawiki(tabela, raw_sections, secao_atual):
    """tabelas dessa wiki intercalam uma linha só-de-headers (<th>) com uma
    linha só-de-valores (<td>) de mesma quantidade de células. header único
    (ex: 'Sharpness', 'Cost to Forge') vira mini-seção própria; headers
    múltiplos lado a lado ficam soltos na seção atual, prontos pra ficha."""
    linhas_tr = tabela.find_all('tr')
    total = len(linhas_tr)
    i = 0

    while i < total:
        celulas = linhas_tr[i].find_all(['th', 'td'])
        if not celulas:
            i += 1
            continue

        eh_so_header = all(c.name == 'th' for c in celulas)
        if not eh_so_header:
            i += 1
            continue

        headers = [re.sub(r'\s+', ' ', c.get_text(separator=" ", strip=True)).strip() for c in celulas]
        headers = [h for h in headers if h]
        if not headers:
            i += 1
            continue

        proxima_celulas = linhas_tr[i + 1].find_all(['th', 'td']) if i + 1 < total else []
        eh_so_valor = bool(proxima_celulas) and all(c.name == 'td' for c in proxima_celulas)

        if not eh_so_valor or len(proxima_celulas) != len(celulas):
            for h in headers:
                raw_sections[secao_atual].append(f"✦ **{h}**")
            i += 1
            continue

        if len(headers) == 1:
            nome_secao = headers[0]
            valor = None
            if nome_secao.lower() == "sharpness":
                valor = extrair_sharpness_mediawiki(proxima_celulas[0])
            if not valor:
                valor = re.sub(r'\s+', ' ', proxima_celulas[0].get_text(separator=" ", strip=True)).strip() or "—"

            raw_sections.setdefault(nome_secao, [])
            raw_sections[nome_secao].append(f"✦ **{nome_secao}**: {valor}")
        else:
            valores = [re.sub(r'\s+', ' ', c.get_text(separator=" ", strip=True)).strip() or "—" for c in proxima_celulas]
            for h, v in zip(headers, valores):
                raw_sections[secao_atual].append(f"✦ **{h}**: {v}")

        i += 2

    raw_sections[secao_atual].append("")


# ────────────────────────────────────────────────────────────────
# 🧾  TABELAS — Kiranico (posicional, beta)
# ────────────────────────────────────────────────────────────────

def eh_tabela_stats_kiranico(tabela):
    """a tabela de status da kiranico começa com um <td> com o ícone do
    item como avatar — sinal simples pra diferenciar de tabelas de material."""
    primeira_linha = tabela.find('tr')
    if not primeira_linha:
        return False
    primeira_celula = primeira_linha.find(['td', 'th'])
    return bool(primeira_celula and primeira_celula.find('img'))


def processar_stats_kiranico(tabela, raw_sections, secao_atual):
    """⚠️ posicional, baseado em UMA amostra (Dual Blades). rótulos de coluna
    não existem no HTML puro (montados via Alpine.js). erros de índice são
    silenciados pra não quebrar o scan inteiro por causa de uma categoria
    de arma com layout diferente (arco, bowgun etc)."""
    corpo = tabela.find('tbody')
    if not corpo:
        return
    tr = corpo.find('tr')
    if not tr:
        return

    celulas = tr.find_all('td', recursive=False)
    if not celulas:
        return

    try:
        attack_txt = celulas[2].get_text(strip=True)
        if attack_txt:
            raw_sections[secao_atual].append(f"✦ **Attack**: {attack_txt}")
    except IndexError:
        pass

    try:
        defesa_txt = re.sub(r'\s+', ' ', celulas[3].get_text(separator=" ", strip=True)).strip()
        m = re.match(r'(.+?)\s+([+\-]?\d[\d.,]*%?)$', defesa_txt)
        if m:
            raw_sections[secao_atual].append(f"✦ **{m.group(1).strip()}**: {m.group(2).strip()}")
        elif defesa_txt:
            raw_sections[secao_atual].append(f"✦ **{defesa_txt}**")
    except IndexError:
        pass

    try:
        rampage_links = celulas[6].find_all('a')
        nomes = [a.get_text(strip=True) for a in rampage_links if a.get_text(strip=True)]
        if nomes:
            raw_sections[secao_atual].append(f"✦ **Rampage Skills**: {' | '.join(nomes)}")
    except IndexError:
        pass

    raw_sections[secao_atual].append("")


# ────────────────────────────────────────────────────────────────
# 🩻  EXTRAÇÃO GERAL DE SEÇÕES BRUTAS
# ────────────────────────────────────────────────────────────────

def extract_raw_sections(content_block, category, parser_name="fextralife"):
    raw_sections = {"informações gerais": []}

    if category == "monster":
        raw_sections["fraquezas & status"] = []

    secao_atual = "informações gerais"
    elementos_processados = set()

    for elemento in content_block.find_all(['h2', 'h3', 'h4', 'p', 'table', 'ul']):
        if id(elemento) in elementos_processados:
            continue
        for filho in elemento.find_all(['p', 'table', 'ul', 'li']):
            elementos_processados.add(id(filho))

        texto_bruto = re.sub(r'\s+', ' ', elemento.get_text(separator=" ", strip=True))
        if not texto_bruto or len(texto_bruto) < 2:
            continue

        if elemento.name in ('h2', 'h3', 'h4'):
            secao_atual = texto_bruto
            raw_sections.setdefault(secao_atual, [])

        elif elemento.name == 'p':
            raw_sections[secao_atual].append(texto_bruto)

        elif elemento.name == 'ul':
            for li in elemento.find_all('li', recursive=False):
                li_text = re.sub(r'\s+', ' ', li.get_text(separator=" ", strip=True))
                if li_text:
                    raw_sections[secao_atual].append(f"⟡ {li_text}")
            raw_sections[secao_atual].append("")

        elif elemento.name == 'table':
            if parser_name == "mediawiki":
                processar_tabela_mediawiki(elemento, raw_sections, secao_atual)
            elif parser_name == "kiranico" and eh_tabela_stats_kiranico(elemento):
                processar_stats_kiranico(elemento, raw_sections, secao_atual)
            else:
                processar_tabela(elemento, raw_sections, secao_atual, category)

    return {k: v for k, v in raw_sections.items() if v}