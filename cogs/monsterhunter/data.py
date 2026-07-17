"""
🕸️ Configuração estática do módulo de Monster Hunter.

Tudo que é "conhecimento declarado" mora aqui: categorias de página, fontes de
wiki disponíveis por jogo, atalhos de comando. Nenhuma lógica de parsing ou
rede vive nesse arquivo — só dados.
"""

# ────────────────────────────────────────────────────────────────
# 🗺️  CATEGORIAS — cada uma sabe como se identificar, qual ícone usar,
# quais campos formam a ficha técnica e como agrupar o resto em baldes.
# ────────────────────────────────────────────────────────────────

CATEGORY_ORDER = [
    "layered_armor", "companion_gear", "armor", "weapon", "decoration",
    "talisman", "slinger", "switch_skill", "item", "monster",
    "endemic_life", "location", "quest", "npc", "lore", "skill",
    "guide", "general",
]

CATEGORIES = {
    "layered_armor": {
        "breadcrumbs": ["layered armor"],
        "icon": "🕸️", "label": "armadura em camadas",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [(["rarity"], "Rarity"), (["slot"], "Slots"), (["defense"], "Defense")],
        "buckets": [("como obter", ["obtain", "unlock", "reward", "craft", "quest"])],
        "bucket_padrao": "detalhes visuais",
    },
    "companion_gear": {
        "breadcrumbs": ["palico gear", "palico equipment", "buddy gear", "buddy equipment", "palamute gear"],
        "icon": "🐈‍⬛", "label": "equipamento de companheiro",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["rarity"], "Rarity"), (["attack"], "Attack"),
            (["defense"], "Defense"), (["element"], "Element"), (["slot"], "Slots"),
        ],
        "buckets": [("craft & materiais", ["craft", "material", "upgrade"])],
        "bucket_padrao": "detalhes do equipamento",
    },
    "armor": {
        "breadcrumbs": ["armor"],
        "icon": "🖤", "label": "armadura",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["rarity"], "Rarity"), (["defense"], "Defense"),
            (["fire res"], "Fire Res"), (["water res"], "Water Res"),
            (["thunder res"], "Thunder Res"), (["ice res"], "Ice Res"),
            (["dragon res"], "Dragon Res"), (["slot"], "Slots"), (["set"], "Set"),
        ],
        "buckets": [
            ("skills & habilidades", ["skill"]),
            ("conjunto & set", ["set bonus", "group skill", "set"]),
            ("craft & materiais", ["craft", "upgrade", "material", "forge"]),
        ],
        "bucket_padrao": "detalhes da armadura",
    },
    "weapon": {
        "breadcrumbs": ["weapons"],
        "icon": "🔪", "label": "arma",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["rarity"], "Rarity"), (["attack"], "Attack"), (["affinity"], "Affinity"),
            (["defense"], "Defense Bonus"), (["element"], "Element"), (["status"], "Status"),
            (["elderseal"], "Elderseal"), (["slot"], "Slots"), (["sharpness"], "Sharpness"),
        ],
        "buckets": [
            ("craft & upgrades", ["craft", "upgrade", "path", "material", "tree", "forge", "cost to"]),
            ("notas & mecânicas", ["note", "tip", "mechanic", "special", "hidden"]),
        ],
        "bucket_padrao": "detalhes da arma",
    },
    "decoration": {
        "breadcrumbs": ["decorations", "rampage decorations", "rampage decoration"],
        "icon": "💠", "label": "decoração",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["rarity"], "Rarity"), (["slot"], "Slot Level"),
            (["effect"], "Effect"), (["skill"], "Skill"),
        ],
        "buckets": [("onde conseguir", ["craft", "drop", "reward", "obtain", "melding", "location"])],
        "bucket_padrao": "detalhes da decoração",
    },
    "talisman": {
        "breadcrumbs": ["talisman"],
        "icon": "🌑", "label": "talismã",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [(["rarity"], "Rarity"), (["skill"], "Skills"), (["slot"], "Slots")],
        "buckets": [("onde conseguir", ["melding", "craft", "obtain", "reward"])],
        "bucket_padrao": "detalhes do talismã",
    },
    "slinger": {
        "breadcrumbs": ["slinger"],
        "icon": "⛓️", "label": "ferramenta de slinger",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [(["ammo"], "Ammo Type"), (["effect"], "Effect")],
        "buckets": [],
        "bucket_padrao": "detalhes",
    },
    "switch_skill": {
        "breadcrumbs": ["switch skills", "switch skill"],
        "icon": "🩸", "label": "switch skill",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [(["weapon type"], "Weapon Type"), (["slot"], "Slot"), (["effect"], "Effect")],
        "buckets": [("como desbloquear", ["unlock", "scroll", "obtain", "kamura"])],
        "bucket_padrao": "detalhes do golpe",
    },
    "item": {
        "breadcrumbs": ["items", "materials", "petalace"],
        "icon": "🥀", "label": "item",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["rarity"], "Rarity"), (["effect", "description"], "Effect"),
            (["sell"], "Sell Price"), (["buy"], "Buy Price"), (["carry"], "Carry Limit"),
        ],
        "buckets": [
            ("como conseguir", ["location", "gather", "reward", "craft", "quest", "buy", "shop", "carve", "drop"]),
            ("uso & combinações", ["combine", "use", "effect"]),
        ],
        "bucket_padrao": "detalhes do item",
    },
    "monster": {
        "breadcrumbs": ["monsters"],
        "icon": "🦇", "label": "monstro",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [
            (["enemy type"], "Enemy Type"), (["species"], "Species"),
            (["element"], "Elements"), (["ailment"], "Ailments"),
            (["weakness"], "Weakness"), (["resistance"], "Resistances"),
            (["threat level"], "Threat Level"), (["location"], "Locations"),
            (["tempered"], "Tempered Lv."),
        ],
        "buckets": [
            ("fraquezas & status", ["weak", "resist", "ailment", "damage"]),
            ("drops & carves", ["carve", "drop", "reward", "master rank", "high rank", "low rank"]),
            ("equipamentos & armas", ["weapon", "armor", "equipment"]),
            ("guia & combate", ["guide", "combat", "attack", "behavior", "strategy"]),
            ("curiosidades", ["trivia", "notes", "lore"]),
        ],
        "bucket_padrao": "outras informações",
    },
    "endemic_life": {
        "breadcrumbs": ["endemic life", "spiribirds", "spiribird"],
        "icon": "🕷️", "label": "vida endêmica",
        "ficha_titulo": "ficha técnica",
        # 📍 destaque especial — a localização merece aparecer logo de cara
        "campo_destaque": (["location"], "Encontrado em"),
        "ficha_keys": [
            (["location"], "Locations"),
            (["effect", "use"], "Effect / Use"),
            (["capture", "method"], "Capture Method"),
        ],
        "buckets": [
            ("comportamento & spawns", ["behavior", "location", "spawn", "habitat"]),
            ("uso & captura", ["capture", "use", "effect", "reward"]),
        ],
        "bucket_padrao": "detalhes da vida endêmica",
    },
    "location": {
        "breadcrumbs": ["locations"],
        "icon": "🕯️", "label": "localidade",
        "ficha_titulo": "visão geral",
        "ficha_keys": [(["region"], "Region"), (["camp"], "Camps"), (["tempered"], "Tempered Lv.")],
        "buckets": [
            ("monstros & vida selvagem", ["monster", "endemic"]),
            ("recursos & coleta", ["gathering", "mining", "bug", "fishing", "resource"]),
            ("acampamentos & áreas", ["camp", "area", "region"]),
        ],
        "bucket_padrao": "outras informações",
    },
    "quest": {
        "breadcrumbs": ["quests"],
        "icon": "📜", "label": "missão",
        "ficha_titulo": "ficha da missão",
        "ficha_keys": [
            (["client"], "Client"), (["location"], "Location"), (["target"], "Target"),
            (["type"], "Type"), (["zenny"], "Zenny Reward"), (["time limit"], "Time Limit"),
            (["fainting"], "Fainting Limit"),
        ],
        "buckets": [("objetivos & recompensas", ["objective", "reward", "target", "condition"])],
        "bucket_padrao": "detalhes da missão",
    },
    "npc": {
        "breadcrumbs": ["npcs", "merchants"],
        "icon": "👻", "label": "personagem",
        "ficha_titulo": "sobre o personagem",
        "ficha_keys": [(["role"], "Role"), (["location"], "Location")],
        "buckets": [("diálogos & lore", ["dialogue", "lore", "note", "trivia"])],
        "bucket_padrao": "outras informações",
    },
    "lore": {
        "breadcrumbs": ["lore"],
        "icon": "⚰️", "label": "lore",
        "ficha_titulo": "história",
        "ficha_keys": [],
        "buckets": [],
        "bucket_padrao": "história",
    },
    "skill": {
        "breadcrumbs": ["skills", "rampage skills"],
        "icon": "✨", "label": "skill",
        "ficha_titulo": "ficha técnica",
        "ficha_keys": [(["effect"], "Effect")],
        "buckets": [],
        "bucket_padrao": "detalhes da skill",
    },
    "guide": {
        "breadcrumbs": ["guides"],
        "icon": "📖", "label": "guia",
        "ficha_titulo": "resumo do guia",
        "ficha_keys": [],
        "buckets": [],
        "bucket_padrao": "conteúdo do guia",
    },
    "general": {
        "breadcrumbs": ["general"],
        "icon": "🕳️", "label": "informação geral",
        "ficha_titulo": "resumo",
        "ficha_keys": [],
        "buckets": [],
        "bucket_padrao": "informações gerais",
    },
    "generic": {
        "breadcrumbs": [],
        "icon": "🌘", "label": "página",
        "ficha_titulo": "informações",
        "ficha_keys": [],
        "buckets": [],
        "bucket_padrao": "informações completas",
    },
}

_CAMPOS_LISTA_PIPE = {"Elements", "Ailments", "Weakness", "Resistances"}

# ────────────────────────────────────────────────────────────────
# 🕵️  DETECÇÃO ALTERNATIVA — usada quando a fonte não expõe breadcrumb
# confiável (MediaWiki sem catlinks, Kiranico com "eyebrow" genérico).
# ────────────────────────────────────────────────────────────────

CONTENT_SIGNATURE_ORDER = [
    "monster", "weapon", "armor", "decoration", "talisman",
    "item", "endemic_life", "location", "quest", "skill",
]

CONTENT_SIGNATURES = {
    "monster": ["ailment weakness", "carves", "habitat", "threat level"],
    "weapon": ["cost to forge", "cost to upgrade", "sharpness", "elderseal"],
    "armor": ["defense bonus", "set bonus", "skill points", "resistances"],
    "decoration": ["slot level", "decoration effect"],
    "talisman": ["talisman"],
    "item": ["sell price", "buy price", "carry limit"],
    "endemic_life": ["capture method", "endemic life"],
    "location": ["camps", "region"],
    "quest": ["zenny reward", "fainting limit"],
    "skill": ["skill effect"],
}

# kiranico organiza tudo por URL (/data/<categoria>/<id>) — muito mais
# confiável pra esse site do que tentar adivinhar pelo conteúdo.
KIRANICO_URL_CATEGORY_MAP = {
    "weapons": "weapon", "armor": "armor", "monsters": "monster",
    "decorations": "decoration", "skills": "skill", "rampage-skills": "skill",
    "items": "item", "talismans": "talisman",
    "buddy-equipment": "companion_gear", "palico-equipment": "companion_gear",
    "locations": "location", "quests": "quest", "endemic-life": "endemic_life",
}

# ────────────────────────────────────────────────────────────────
# 🕯️  FONTES DE WIKI — só o mhr tem mais de uma opção por enquanto.
# ────────────────────────────────────────────────────────────────

WIKI_SOURCES = {
    "mhr": {
        "fextra": {
            "label": "Fextralife",
            "domain": "monsterhunterrise.wiki.fextralife.com",
            "path_prefix": "",
            "spacer": "+",
            "parser": "fextralife",
            "guess_direct_url": True,
        },
        "mhwiki": {
            "label": "Monster Hunter Wiki",
            "domain": "monsterhunterwiki.org",
            "path_prefix": "wiki/",
            "spacer": "_",
            "preserve_case": True,  # mediawiki só capitaliza a 1ª letra, não o título inteiro
            "parser": "mediawiki",
            "guess_direct_url": True,
            # páginas dessa wiki costumam ter sufixo de desambiguação por jogo
            "page_suffixes": ["_(MHRS)"],
            "search_hint": "MHRS",  # empurra o google pra achar a página certa do jogo certo
        },
        "kiranico": {
            "label": "Kiranico",
            "domain": "mhrise.kiranico.com",
            "path_prefix": "",
            "spacer": "-",
            "parser": "kiranico",
            # kiranico usa IDs numéricos na URL — impossível adivinhar pelo nome
            "guess_direct_url": False,
        },
    },
    "mhw": {
        "fextra": {
            "label": "Fextralife",
            "domain": "monsterhunterworld.wiki.fextralife.com",
            "path_prefix": "",
            "spacer": "+",
            "parser": "fextralife",
            "guess_direct_url": True,
        },
    },
    "mhwilds": {
        "fextra": {
            "label": "Fextralife",
            "domain": "monsterhunterwilds.wiki.fextralife.com",
            "path_prefix": "",
            "spacer": "_",
            "parser": "fextralife",
            "guess_direct_url": True,
        },
    },
}

DEFAULT_SOURCE = "fextra"
PREF_FILE = "data/wiki_preferences.json"

# ────────────────────────────────────────────────────────────────
# 🔪  ATALHOS
# ────────────────────────────────────────────────────────────────

SHORTCUTS = {
    "weak": {
        "buckets": {"monster": "fraquezas & status"},
        "vazio": "Nenhuma fraqueza detalhada encontrada por aqui...",
    },
    "drop": {
        "buckets": {"monster": "drops & carves"},
        "vazio": "Nenhum material de drop encontrado...",
    },
    "craft": {
        "buckets": {
            "weapon": "craft & upgrades",
            "armor": "craft & materiais",
            "companion_gear": "craft & materiais",
            "decoration": "onde conseguir",
            "talisman": "onde conseguir",
            "layered_armor": "como obter",
        },
        "vazio": "Nenhum material de criação encontrado...",
    },
    "skills": {
        "buckets": {"armor": "skills & habilidades"},
        "vazio": "Nenhuma skill encontrada por aqui...",
    },
    "set": {
        "buckets": {"armor": "conjunto & set"},
        "vazio": "Esse equipamento não parece pertencer a um conjunto com bônus...",
    },
}
SHORTCUTS["upgrades"] = SHORTCUTS["craft"]