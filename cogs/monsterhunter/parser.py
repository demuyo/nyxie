"""
📋 Montagem das páginas finais a partir do conteúdo bruto extraído.
Nada aqui sabe fazer requisição de rede — só recebe HTML já baixado.
"""

import re
from bs4 import BeautifulSoup

from . import extractors
from .data import CATEGORIES, SHORTCUTS, _CAMPOS_LISTA_PIPE


def build_summary_dict(raw_sections):
    resumo = {}
    for linhas in raw_sections.values():
        for linha in linhas:
            m = re.match(r"✦ \*\*(.*?)\*\*: (.*)", linha)
            if m:
                resumo[m.group(1).lower()] = m.group(2)
    return resumo


def buscar_no_resumo(summary_dict, variacoes):
    for chave, valor in summary_dict.items():
        if any(v in chave for v in variacoes):
            return valor
    return None


def build_ficha_page(raw_sections, summary_dict, cfg, termo):
    intro = raw_sections.get("informações gerais", [])
    variacoes_usadas = {v for variacoes, _ in cfg["ficha_keys"] for v in variacoes}

    descricao = []
    for linha in intro:
        m = re.match(r"✦ \*\*(.*?)\*\*:", linha)
        eh_campo_chave = bool(m) and any(v in m.group(1).lower() for v in variacoes_usadas)
        if not eh_campo_chave and linha.strip():
            descricao.append(linha)

    linhas = []

    # 🩸 evita duplicar o nome: se a wiki já traz uma linha tipo
    # "✦ **Rathalos** リオレウス", usa ela como título em vez de criar outra
    if descricao:
        primeira_linha = descricao[0]
        m = re.match(r"✦ \*\*(.*?)\*\*", primeira_linha)
        if m and termo.lower() in m.group(1).lower():
            linhas.append(primeira_linha)
            descricao = descricao[1:]
        else:
            linhas.append(f"✦ **{termo.title()}**")
    else:
        linhas.append(f"✦ **{termo.title()}**")

    if descricao:
        linhas.append("")
        linhas.extend(descricao[:9])

    # 🕷️ destaque especial (ex: localização de vida endêmica) logo após a descrição
    destaque = cfg.get("campo_destaque")
    campo_ja_usado = None
    if destaque:
        variacoes_destaque, label_destaque = destaque
        valor_destaque = buscar_no_resumo(summary_dict, variacoes_destaque)
        if valor_destaque:
            linhas.append("")
            linhas.append(f"📍 **{label_destaque}**: {valor_destaque}")
            campo_ja_usado = variacoes_destaque

    campos_extraidos = []
    for variacoes, nome_exibido in cfg["ficha_keys"]:
        if variacoes == campo_ja_usado:
            continue
        valor = buscar_no_resumo(summary_dict, variacoes)
        if not valor:
            continue
        if nome_exibido in _CAMPOS_LISTA_PIPE:
            valor = re.sub(r'( \(\S+\))', r' | \1', valor).strip(' |')
        campos_extraidos.append(f"✦ **{nome_exibido}**: {valor}")

    if campos_extraidos:
        linhas.append("")
        linhas.extend(campos_extraidos)

    return linhas


def montar_paginas_tematicas(raw_sections, summary_dict, category, cfg, termo):
    paginas = {cfg["ficha_titulo"]: build_ficha_page(raw_sections, summary_dict, cfg, termo)}

    for bucket_titulo, _ in cfg["buckets"]:
        paginas.setdefault(bucket_titulo, [])

    if "fraquezas & status" in raw_sections:
        paginas.setdefault("fraquezas & status", [])
        paginas["fraquezas & status"].extend(raw_sections["fraquezas & status"])

    for secao, linhas in raw_sections.items():
        if secao in ("informações gerais", "fraquezas & status"):
            continue

        secao_lower = secao.lower()
        destino = cfg["bucket_padrao"]
        for bucket_titulo, palavras_chave in cfg["buckets"]:
            if any(p in secao_lower for p in palavras_chave):
                destino = bucket_titulo
                break

        paginas.setdefault(destino, [])
        paginas[destino].extend([f"\n**{secao}**"] + linhas)

    return {k: v for k, v in paginas.items() if v}


def resolver_atalho(acao, category, paginas_tematicas):
    if acao == "scan":
        return paginas_tematicas, None

    atalho = SHORTCUTS.get(acao)
    if not atalho:
        return paginas_tematicas, None

    bucket_nome = atalho["buckets"].get(category)
    if not bucket_nome:
        categorias_validas = " / ".join(CATEGORIES[c]["label"] for c in atalho["buckets"])
        return None, f"categoria_errada::{categorias_validas}"

    conteudo = paginas_tematicas.get(bucket_nome, [atalho["vazio"]])
    return {bucket_nome: conteudo}, None


def renderizar_embeds(pages_to_render, url, cfg, fonte_label, thumbnail_url, make_embed):
    embeds_prontos = []
    primeiro = True

    for secao, linhas in pages_to_render.items():
        content = "\n".join(linhas)
        content = re.sub(r'\n{3,}', '\n\n', content)

        chunks = [content[i:i + 3900] for i in range(0, len(content), 3900)] or [""]

        for idx, chunk in enumerate(chunks):
            sufixo = " (cont.)" if idx > 0 else ""
            titulo = f"{cfg['icon']} {secao.lower()}{sufixo}"
            embed = make_embed(titulo, chunk or "*(sem conteúdo)*")
            embed.url = url
            embed.set_footer(text=f"fonte: {fonte_label} • {cfg['label']}")

            if primeiro and thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
                primeiro = False

            embeds_prontos.append(embed)

    return embeds_prontos


def parse_page(html, url, acao, termo, parser_name, fonte_label, make_embed):
    """pipeline principal — recebe HTML cru e devolve embeds prontos (ou uma
    string de erro no formato 'categoria_errada::...' pro atalho errado)."""
    soup = BeautifulSoup(html, 'html.parser')

    extrator = extractors.EXTRACTOR_FUNCS.get(parser_name, extractors.extrator_fextralife)
    content_block, breadcrumb_text, thumbnail_url = extrator(soup)

    if content_block is None:
        return []

    # 🕵️ cadeia de detecção: sinal mais confiável primeiro.
    # breadcrumb (fextra) → URL (kiranico) → assinatura de conteúdo (fallback)
    category = extractors.detectar_categoria_breadcrumb(breadcrumb_text)

    if category == "generic" and parser_name == "kiranico":
        category = extractors.detectar_categoria_kiranico_por_url(url)

    if category == "generic":
        texto_pagina = content_block.get_text(" ", strip=True).lower()
        category = extractors.detectar_categoria_por_conteudo(texto_pagina)

    cfg = CATEGORIES[category]

    for tag in content_block.find_all(['script', 'style']):
        tag.decompose()
    for br in content_block.find_all('br'):
        br.replace_with('\n')

    extractors.replace_images_with_text(content_block)
    extractors.clean_page_junk(content_block)

    raw_sections = extractors.extract_raw_sections(content_block, category, parser_name)
    summary_dict = build_summary_dict(raw_sections)
    paginas_tematicas = montar_paginas_tematicas(raw_sections, summary_dict, category, cfg, termo)

    pages_to_render, erro = resolver_atalho(acao, category, paginas_tematicas)
    if erro:
        return erro

    if not pages_to_render:
        return []

    return renderizar_embeds(pages_to_render, url, cfg, fonte_label, thumbnail_url, make_embed)