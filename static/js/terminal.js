// static/js/terminal.js

const output = document.getElementById('output');
const input = document.getElementById('input');

// ==================== ASCII ART INICIALIZAÇÃO ====================
window.onload = () => {
    const asciiArt = `
███╗   ██╗██╗   ██╗██╗  ██╗██╗███████╗
████╗  ██║╚██╗ ██╔╝╚██╗██╔╝██║██╔════╝
██╔██╗ ██║ ╚████╔╝  ╚███╔╝ ██║█████╗  
██║╚██╗██║  ╚██╔╝   ██╔██╗ ██║██╔══╝  
██║ ╚████║   ██║   ██╔╝ ██╗██║███████╗
╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝

NYXIE TERMINAL v1.0
> PRESENT DAY... PRESENT TIME...
> digite 'help' para comandos secretos
    `;
    
    addLine(asciiArt, 'bot-response');
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
        addLine('error');
        addLine('error');
        
        setTimeout(() => {
            crt.classList.remove('glitch');
            addLine('...estabilizado', 'bot-response');
        }, 500);  // ⬅️ 0.5 segundos - PISCOU PERDEU
    },
    'matrix': () => {
        addLine('WAKE UP, NEO...', 'bot-response');
        setTimeout(() => addLine('the matrix has you...', 'bot-response'), 1000);
    },
    'lain': () => {
        addLine('PRESENT DAY... PRESENT TIME... HAHAHAHAHA', 'bot-response');
    },
    'help': () => {
        const helpText = `
            comandos secretos:
            • clear - limpa o terminal
            • glitch - efeito glitch
            • matrix - ???
            • lain - reference
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
            secretCommands[message.toLowerCase()]();
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
            
            // Checa se a resposta é OK
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erro HTTP:', response.status, errorText);
                addLine(`ERROR ${response.status}: servidor retornou erro`, 'error');
                return;
            }
            
            // Tenta parsear JSON
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
            // Remove "pensando..." se ainda existir
            document.getElementById('thinking')?.remove();
            
            console.error('Erro completo:', error);
            addLine('CONNECTION_ERROR: ' + error.message, 'error');
        }
    }
});

// ==================== FUNÇÕES AUXILIARES ====================

// Gera/recupera ID único do usuário (persiste no localStorage)
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