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
        
        // ⬇️ REMOVIDO: Não sobrescreve mais, usa direto o que veio do servidor
        // Monta o banner com o ASCII que veio do backend
        const banner = `${data.ascii_art}

NYXIE TERMINAL v1.0
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
        // ⬇️ NOVO: comando pra debug
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
• help - esta mensagem
        `;
        addLine(helpText, 'bot-response');
    }
};

// ==================== EVENT LISTENER PRINCIPAL ====================
input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const message = input.value;
        if (!message.trim()) return;
        
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