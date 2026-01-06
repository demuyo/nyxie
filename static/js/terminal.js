// static/js/terminal.js

const output = document.getElementById('output');
const input = document.getElementById('input');

// ==================== CARREGA QUOTES E ASCII ALEATÓRIOS ====================
window.onload = async () => {
    try {
        // Busca quote e ASCII aleatórios do servidor (já vem filtrado pelo backend)
        const response = await fetch('/quotes');
        const data = await response.json();
        
        console.log('📦 Dados carregados:', data);
        console.log('📱 Mobile:', data.is_mobile);
        console.log('🎨 ASCII:', data.ascii_name);
        
        // Monta o banner com o ASCII que veio do backend
        const banner = `${data.ascii_art}

NYXIE TERMINAL v1.3
> ${data.quote}
${data.is_mobile ? "> digite 'help'" : "> digite 'help' para comandos secretos"}
        `;
        
        const line = document.createElement('div');
        line.className = 'output-line bot-response ascii-art';
        line.textContent = banner;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
        
    } catch (error) {
        console.error('❌ Erro ao carregar quotes:', error);
        
        // Fallback se der erro
        addLine('━━━━━━━━━━━━━━━━━━━━', 'bot-response');
        addLine('   NYXIE TERMINAL   ', 'bot-response');
        addLine('━━━━━━━━━━━━━━━━━━━━', 'bot-response');
        addLine('', 'bot-response');
        addLine('⛧ close the world, open the nExt', 'bot-response');
        addLine('', 'bot-response');
        addLine("digite 'help'", 'bot-response');
    }
};

// ==================== COMANDOS SECRETOS ====================
const secretCommands = {
    'clear': () => {
        output.innerHTML = '';
        addLine('terminal limpo', 'bot-response');
    },
    'glitch': () => {
        const crt = document.getElementById('crt');
        crt.classList.add('glitch');
        addLine('█▀▀ █░░ █ ▀█▀ █▀▀ █░█', 'error');
        addLine('█▄█ █▄▄ █ ░█░ █▄▄ █▀█', 'error');
        
        setTimeout(() => {
            crt.classList.remove('glitch');
            addLine('...estabilizado', 'bot-response');
        }, 500);
    },
    'matrix': () => {
        addLine('WAKE UP, NEO...', 'bot-response');
        setTimeout(() => addLine('the matrix has you...', 'bot-response'), 1000);
    },
    'lain': () => {
        addLine('PRESENT DAY... PRESENT TIME... HAHAHAHAHA', 'bot-response');
    },
    'reload': async () => {
        addLine('recarregando...', 'bot-response');
        try {
            const response = await fetch('/quotes');
            const data = await response.json();
            addLine('', 'bot-response');
            
            // Mostra nova ASCII e quote
            const line = document.createElement('div');
            line.className = 'output-line bot-response ascii-art';
            line.textContent = `${data.ascii_art}\n\n> ${data.quote}`;
            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        } catch (error) {
            addLine('erro ao carregar nova quote', 'error');
        }
    },
    'void': () => {
        addLine('//void//void//void', 'bot-response');
        addLine('∅ null.null.null', 'bot-response');
    },
    'debug': async () => {
        try {
            const response = await fetch('/quotes');
            const data = await response.json();
            addLine(`is_mobile: ${data.is_mobile}`, 'bot-response');
            addLine(`ascii_name: ${data.ascii_name}`, 'bot-response');
            addLine(`quote: ${data.quote}`, 'bot-response');
        } catch (error) {
            addLine('erro no debug', 'error');
        }
    },
    'theme': () => {
        const validThemes = ['lain', 'matrix', 'cyberpunk', 'void', 'marimo', 'custom'];
        addLine('temas disponíveis:', 'bot-response');
        validThemes.forEach(t => addLine(`• ${t}`, 'bot-response'));
        addLine('', 'bot-response');
        addLine('use: theme lain, theme matrix, etc', 'bot-response');
    },
    'help': () => {
        const helpText = `
comandos secretos:
• clear - limpa o terminal
• glitch - efeito glitch (0.5s)
• matrix - ???
• lain - reference
• reload - nova quote + ascii
• void - ...
• debug - mostra info
• theme [nome] - troca tema
• help - esta mensagem

use: theme lain, theme matrix, etc
        `;
        addLine(helpText, 'bot-response');
    }
};

// ==================== EVENT LISTENER PRINCIPAL ====================
input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const message = input.value;
        if (!message.trim()) return;
        
        // Checa se é comando "theme nomeTema"
        const themeMatch = message.match(/^theme\s+(\w+)$/i);
        if (themeMatch) {
            const themeName = themeMatch[1].toLowerCase();
            const validThemes = ['lain', 'matrix', 'cyberpunk', 'void', 'marimo', 'custom'];
            
            addLine(`> ${message}`, 'user-input');
            input.value = '';
            
            if (validThemes.includes(themeName)) {
                document.documentElement.setAttribute('data-theme', themeName);
                localStorage.setItem('nyxie_theme', themeName);
                
                document.querySelectorAll('.theme-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.getAttribute('data-theme') === themeName);
                });
                
                // Mostra/esconde menu custom
                if (themeName === 'custom') {
                    toggleCustomMenu(true);
                } else {
                    toggleCustomMenu(false);
                }
                
                addLine(`> tema alterado: ${themeName}`, 'bot-response');
            } else {
                addLine('tema inválido', 'error');
                addLine('', 'bot-response');
                secretCommands['theme']();
            }
            return;
        }
        
        // Checa comandos secretos PRIMEIRO
        if (secretCommands[message.toLowerCase()]) {
            addLine(`> ${message}`, 'user-input');
            await secretCommands[message.toLowerCase()]();
            input.value = '';
            return;
        }
        
        // Mostra input do usuário
        addLine(`> ${message}`, 'user-input');
        input.value = '';
        
        // Mostra "pensando..."
        const thinkingLine = document.createElement('div');
        thinkingLine.className = 'output-line bot-response';
        thinkingLine.textContent = '...';
        thinkingLine.id = 'thinking';
        output.appendChild(thinkingLine);
        
        // Envia pro backend
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    message: message
                })
            });
            
            // Remove "pensando..."
            document.getElementById('thinking')?.remove();
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erro HTTP:', response.status, errorText);
                addLine(`ERROR ${response.status}: servidor retornou erro`, 'error');
                return;
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Resposta não é JSON:', text);
                addLine('CONNECTION_ERROR: resposta inválida do servidor', 'error');
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                addLine(`ERROR: ${data.error}`, 'error');
                return;
            }
            
            // Efeito de digitação
            typeWriter(data.response);
            
        } catch (error) {
            document.getElementById('thinking')?.remove();
            console.error('Erro completo:', error);
            addLine('CONNECTION_ERROR: ' + error.message, 'error');
        }
    }
});

// ==================== FUNÇÕES AUXILIARES ====================

function getUserId() {
    let userId = localStorage.getItem('nyxie_user_id');
    if (!userId) {
        userId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('nyxie_user_id', userId);
        console.log('🆔 Novo user_id criado:', userId);
    }
    return userId;
}

function addLine(text, className = '') {
    const line = document.createElement('div');
    line.className = `output-line ${className}`;
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function typeWriter(text, index = 0) {
    if (index === 0) {
        const line = document.createElement('div');
        line.className = 'output-line bot-response';
        line.id = 'current-typing';
        output.appendChild(line);
    }
    
    const currentLine = document.getElementById('current-typing');
    if (index < text.length) {
        currentLine.textContent += text.charAt(index);
        output.scrollTop = output.scrollHeight;
        setTimeout(() => typeWriter(text, index + 1), 30);
    } else {
        currentLine.id = '';
    }
}

// ==================== MENU LATERAL E TEMAS ====================

// Abre/fecha menu
document.getElementById('menu-toggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('sidebar-hidden');
});

document.getElementById('close-menu').addEventListener('click', () => {
    document.getElementById('sidebar').classList.add('sidebar-hidden');
});

// Fecha menu ao clicar fora
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('menu-toggle');
    
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.add('sidebar-hidden');
    }
});

// Tema padrão
const savedTheme = localStorage.getItem('nyxie_theme') || 'lain';
document.documentElement.setAttribute('data-theme', savedTheme);

// Marca botão ativo
document.querySelectorAll('.theme-btn').forEach(btn => {
    if (btn.getAttribute('data-theme') === savedTheme) {
        btn.classList.add('active');
    }
});

// Função pra mostrar/esconder menu custom
const toggleCustomMenu = (show) => {
    const customSection = document.getElementById('custom-colors-section');
    if (show) {
        customSection.classList.remove('custom-hidden');
    } else {
        customSection.classList.add('custom-hidden');
    }
};

// Se o tema salvo for custom, mostra a seção
if (savedTheme === 'custom') {
    toggleCustomMenu(true);
}

// Troca de tema
document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const theme = btn.getAttribute('data-theme');
        
        // Atualiza tema
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('nyxie_theme', theme);
        
        // Atualiza botão ativo
        document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Mostra/esconde menu custom
        if (theme === 'custom') {
            toggleCustomMenu(true);
        } else {
            toggleCustomMenu(false);
        }
        
        // Feedback visual
        addLine(`> tema alterado: ${theme}`, 'bot-response');
    });
});

// ==================== CUSTOM COLOR PICKER ====================

// Callback quando confirmar cor no picker
// Callback quando confirmar cor no picker
window.pickerCallback = (targetId, hex) => {
    const colorType = targetId.replace('-preview', '');
    
    document.getElementById(`${colorType}-color`).value = hex;
    document.getElementById(`${colorType}-hex`).value = hex;
    document.getElementById(`${colorType}-preview`).style.background = hex;
    
    // ⬇️ ADICIONA ISSO - Salva e aplica automaticamente
    saveAndApplyColors();
};

// Configuração dos color pickers
const colorInputs = [
    { preview: 'primary-preview', text: 'primary-hex', picker: 'primary-color' },
    { preview: 'secondary-preview', text: 'secondary-hex', picker: 'secondary-color' },
    { preview: 'prompt-preview', text: 'prompt-hex', picker: 'prompt-color' },
    { preview: 'error-preview', text: 'error-hex', picker: 'error-color' }
];

colorInputs.forEach(({ preview, text, picker }) => {
    const previewEl = document.getElementById(preview);
    const textEl = document.getElementById(text);
    const pickerEl = document.getElementById(picker);
    
    // Clica no preview pra abrir o picker CUSTOMIZADO
    previewEl.addEventListener('click', () => {
        if (window.colorPicker) {
            window.colorPicker.open(preview, pickerEl.value);
        }
    });
    
    // Quando digita no text, atualiza preview
    textEl.addEventListener('input', (e) => {
        let value = e.target.value.trim();
        
        if (value && !value.startsWith('#')) {
            value = '#' + value;
        }
        
        if (/^#[0-9A-F]{3}$/i.test(value)) {
            const r = value[1];
            const g = value[2];
            const b = value[3];
            value = `#${r}${r}${g}${g}${b}${b}`;
        }
        
        if (/^#[0-9A-F]{6}$/i.test(value)) {
            pickerEl.value = value;
            previewEl.style.background = value;
            textEl.value = value.toUpperCase();
            
            // ⬇️ ADICIONA ISSO
            saveAndApplyColors();
        }
    });
    
    textEl.addEventListener('blur', (e) => {
        let value = e.target.value.trim();
        
        if (!value.startsWith('#')) {
            value = '#' + value;
        }
        
        if (!/^#[0-9A-F]{6}$/i.test(value) && !/^#[0-9A-F]{3}$/i.test(value)) {
            textEl.value = pickerEl.value.toUpperCase();
            previewEl.style.background = pickerEl.value;
        }
    });
});

// Carrega cores customizadas salvas
const loadCustomColors = () => {
    const saved = localStorage.getItem('nyxie_custom_colors');
    if (saved) {
        try {
            const colors = JSON.parse(saved);
            
            document.getElementById('primary-color').value = colors.primary;
            document.getElementById('primary-hex').value = colors.primary.toUpperCase();
            document.getElementById('primary-preview').style.background = colors.primary;
            
            document.getElementById('secondary-color').value = colors.secondary;
            document.getElementById('secondary-hex').value = colors.secondary.toUpperCase();
            document.getElementById('secondary-preview').style.background = colors.secondary;
            
            document.getElementById('prompt-color').value = colors.prompt;
            document.getElementById('prompt-hex').value = colors.prompt.toUpperCase();
            document.getElementById('prompt-preview').style.background = colors.prompt;
            
            document.getElementById('error-color').value = colors.error;
            document.getElementById('error-hex').value = colors.error.toUpperCase();
            document.getElementById('error-preview').style.background = colors.error;
            
            applyCustomColors(colors);
        } catch (e) {
            console.error('Erro ao carregar cores customizadas:', e);
        }
    }
};

const saveAndApplyColors = () => {
    const colors = {
        primary: document.getElementById('primary-color').value,
        secondary: document.getElementById('secondary-color').value,
        prompt: document.getElementById('prompt-color').value,
        error: document.getElementById('error-color').value
    };
    
    const isTooDark = (hex) => {
        const r = parseInt(hex.substr(1, 2), 16);
        const g = parseInt(hex.substr(3, 2), 16);
        const b = parseInt(hex.substr(5, 2), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
        return luminance < 20;
    };
    
    // Substitui cores muito escuras por #1E1E1E
    Object.keys(colors).forEach(key => {
        if (isTooDark(colors[key])) {
            colors[key] = '#1E1E1E';
            addLine('> cor muito escura detectada, ajustando...', 'error');
        }
    });
    
    // Salva no localStorage
    localStorage.setItem('nyxie_custom_colors', JSON.stringify(colors));
    
    // Aplica as cores
    applyCustomColors(colors);
    
    // Muda pra tema custom automaticamente
    if (document.documentElement.getAttribute('data-theme') !== 'custom') {
        document.documentElement.setAttribute('data-theme', 'custom');
        localStorage.setItem('nyxie_theme', 'custom');
        
        // Atualiza botão ativo
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme') === 'custom');
        });
        
        toggleCustomMenu(true);
        addLine('> tema custom ativado', 'bot-response');
    }
};

// Aplica cores customizadas
const applyCustomColors = (colors) => {
    document.documentElement.style.setProperty('--custom-primary', colors.primary);
    document.documentElement.style.setProperty('--custom-secondary', colors.secondary);
    document.documentElement.style.setProperty('--custom-prompt', colors.prompt);
    document.documentElement.style.setProperty('--custom-error', colors.error);
};

// Botão aplicar
/*document.getElementById('apply-custom').addEventListener('click', () => {
    const colors = {
        primary: document.getElementById('primary-color').value,
        secondary: document.getElementById('secondary-color').value,
        prompt: document.getElementById('prompt-color').value,
        error: document.getElementById('error-color').value
    };
    
    localStorage.setItem('nyxie_custom_colors', JSON.stringify(colors));
    applyCustomColors(colors);
    
    document.documentElement.setAttribute('data-theme', 'custom');
    localStorage.setItem('nyxie_theme', 'custom');
    
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-theme') === 'custom');
    });
    
    addLine('> tema custom aplicado', 'bot-response');
});*/

// Botão resetar
document.getElementById('reset-custom').addEventListener('click', () => {
    const defaultColors = {
        primary: '#b19cd9',
        secondary: '#ff6ec7',
        prompt: '#d4a5ff',
        error: '#ff4444'
    };
    
    document.getElementById('primary-color').value = defaultColors.primary;
    document.getElementById('primary-hex').value = defaultColors.primary.toUpperCase();
    document.getElementById('primary-preview').style.background = defaultColors.primary;
    
    document.getElementById('secondary-color').value = defaultColors.secondary;
    document.getElementById('secondary-hex').value = defaultColors.secondary.toUpperCase();
    document.getElementById('secondary-preview').style.background = defaultColors.secondary;
    
    document.getElementById('prompt-color').value = defaultColors.prompt;
    document.getElementById('prompt-hex').value = defaultColors.prompt.toUpperCase();
    document.getElementById('prompt-preview').style.background = defaultColors.prompt;
    
    document.getElementById('error-color').value = defaultColors.error;
    document.getElementById('error-hex').value = defaultColors.error.toUpperCase();
    document.getElementById('error-preview').style.background = defaultColors.error;
    
    applyCustomColors(defaultColors);
    localStorage.setItem('nyxie_custom_colors', JSON.stringify(defaultColors));
    
    addLine('> cores resetadas', 'bot-response');
});

// Carrega cores customizadas ao iniciar
loadCustomColors();

// Se o tema salvo for custom, aplica as cores
if (savedTheme === 'custom') {
    loadCustomColors();
}