// static/js/terminal.js

// ==================== ELEMENTOS DO DOM ====================
const output = document.getElementById('output');
const input = document.getElementById('input');

// ==================== SISTEMA DE MÚLTIPLOS CHATS (ISOLADOS) ====================

class ChatManager {
    constructor() {
        this.chats = this.loadChats();
        this.currentChatId = this.loadCurrentChatId();
        this.pendingConfirmation = null; // ⬅️ SISTEMA DE CONFIRMAÇÃO
        
        // ⬅️ NÃO CARREGA NADA AQUI - só cria se necessário
        if (Object.keys(this.chats).length === 0) {
            const chatId = this.generateChatId();
            const timestamp = new Date().toISOString();
            
            this.chats[chatId] = {
                id: chatId,
                title: `Chat 1`,
                created: timestamp,
                modified: timestamp,
                messages: [],
                history: [],
                model: 'llama-3.3-70b-versatile'
            };
            
            this.currentChatId = chatId;
            this.saveChats();
            this.saveCurrentChatId();
        }
        
        this.initializeSidebar();
    }

    // ==================== CRIAÇÃO E GERENCIAMENTO ====================

    generateChatId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    createNewChat(title = null) {
        const chatId = this.generateChatId();
        const timestamp = new Date().toISOString();
        
        this.chats[chatId] = {
            id: chatId,
            title: title || `Chat ${Object.keys(this.chats).length + 1}`,
            created: timestamp,
            modified: timestamp,
            messages: [],
            history: [],
            model: getCurrentModel()
        };
        
        this.currentChatId = chatId;
        this.pendingConfirmation = null; // ⬅️ LIMPA CONFIRMAÇÃO
        this.saveChats();
        this.saveCurrentChatId();
        this.renderChatList();
        this.loadChatMessages(chatId);
        
        return chatId;
    }

    addMessage(role, content) {
        if (!this.currentChatId) return;
        
        const chat = this.chats[this.currentChatId];
        if (!chat) return;
        
        const message = {
            role: role,
            content: content,
            timestamp: new Date().toISOString()
        };
        
        chat.messages.push(message);
        
        if (!chat.history) chat.history = [];
        chat.history.push({
            role: role,
            content: content
        });
        
        chat.modified = new Date().toISOString();
        
        // Auto-rename baseado na primeira mensagem
        if (chat.messages.filter(m => m.role === 'user').length === 1 && role === 'user') {
            chat.title = content.substring(0, 30) + (content.length > 30 ? '...' : '');
        }
        
        this.saveChats();
        this.renderChatList();
    }

    getCurrentChatHistory() {
        if (!this.currentChatId) return [];
        
        const chat = this.chats[this.currentChatId];
        if (!chat) return [];
        
        if (!chat.history) chat.history = [];
        
        return chat.history;
    }

    // ==================== CARREGAMENTO E EXIBIÇÃO ====================

    async loadChatMessages(chatId) {
        const chat = this.chats[chatId];
        if (!chat) return;
        
        this.currentChatId = chatId;
        this.pendingConfirmation = null; // ⬅️ LIMPA CONFIRMAÇÃO AO TROCAR CHAT
        this.saveCurrentChatId();
        
        // Carrega modelo do chat e atualiza indicador
        if (chat.model) {
            localStorage.setItem('nyxie_model', chat.model);
            if (window.updateModelIndicator) {
                await window.updateModelIndicator();
            }
        }
    
        // LIMPA COMPLETAMENTE O OUTPUT
        output.innerHTML = '';
        
        // SEMPRE CARREGA ASCII ALEATÓRIO
        try {
            const response = await fetch('/quotes');
            const data = await response.json();
            
            const banner = `${data.ascii_art}

    NYXIE TERMINAL v1.4
    > ${data.quote}
    ${data.is_mobile ? "> digite '/help'" : "> digite '/help' para comandos"}
        `;
            
            const line = document.createElement('div');
            line.className = 'output-line bot-response ascii-art';
            line.textContent = banner;
            output.appendChild(line);
            
        } catch (error) {
            addLine('━━━━━━━━━━━━━━━━━━━━', 'bot-response');
            addLine('   NYXIE TERMINAL   ', 'bot-response');
            addLine('━━━━━━━━━━━━━━━━━━━━', 'bot-response');
            addLine('', 'bot-response');
            addLine('⛧ close the world, open the nExt', 'bot-response');
        }
        
        // ⬅️ CARREGA MENSAGENS COM SYNTAX HIGHLIGHT
        chat.messages.forEach(msg => {
            if (msg.role === 'user') {
                addLine(`> ${msg.content}`, 'user-input');
            } else {
                renderMarkdownMessage(msg.content);
            }
        });
        
        this.renderChatList();
        scrollToBottom();
    }

    // ==================== OPERAÇÕES DE CHAT ====================

    deleteChat(chatId) {
        if (Object.keys(this.chats).length <= 1) {
            addLine('⚠️ Não é possível deletar o último chat!', 'error');
            return;
        }
        
        delete this.chats[chatId];
        
        if (this.currentChatId === chatId) {
            this.currentChatId = Object.keys(this.chats)[0];
            this.loadChatMessages(this.currentChatId);
        }
        
        this.saveChats();
        this.renderChatList();
    }

    renameChat(chatId, newTitle) {
        if (!newTitle || newTitle.trim() === '') return;
        
        if (this.chats[chatId]) {
            this.chats[chatId].title = newTitle.trim();
            this.chats[chatId].modified = new Date().toISOString();
            this.saveChats();
            this.renderChatList();
        }
    }

    // ==================== INTERFACE E RENDERIZAÇÃO ====================

    getRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'agora';
        if (minutes < 60) return `${minutes}m atrás`;
        if (hours < 24) return `${hours}h atrás`;
        if (days < 7) return `${days}d atrás`;
        
        return time.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }

    renderChatList() {
        const chatList = document.getElementById('chat-list');
        chatList.innerHTML = '';
        
        const sortedChats = Object.values(this.chats).sort((a, b) => 
            new Date(b.modified) - new Date(a.modified)
        );
        
        sortedChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = `chat-item ${chat.id === this.currentChatId ? 'active' : ''}`;
            
            const lastMessage = chat.messages[chat.messages.length - 1];
            const preview = lastMessage ? 
                (lastMessage.content.substring(0, 40) + (lastMessage.content.length > 40 ? '...' : '')) : 
                'Sem mensagens';
            
            const modelEmoji = this.getModelEmoji(chat.model);
            
            chatItem.innerHTML = `
                <div class="chat-item-content" onclick="chatManager.loadChatMessages('${chat.id}')">
                    <div class="chat-item-title">${this.escapeHtml(chat.title)} ${modelEmoji}</div>
                    <div class="chat-item-preview">${this.escapeHtml(preview)}</div>
                    <div class="chat-item-time">${this.getRelativeTime(chat.modified)}</div>
                </div>
                <div class="chat-item-actions">
                    <button onclick="event.stopPropagation(); chatManager.promptRename('${chat.id}')" title="Renomear">✏️</button>
                    <button onclick="event.stopPropagation(); chatManager.promptDelete('${chat.id}')" title="Deletar">🗑️</button>
                </div>
            `;
            
            chatList.appendChild(chatItem);
        });
    }

    getModelEmoji(modelId) {
        if (!modelId) return '';
        
        const emojis = {
            'llama-3.1-8b-instant': '⚡',
            'llama-3.3-70b-versatile': '🤖',
            'openai/gpt-oss-20b': '⚙️',
            'openai/gpt-oss-120b': '🧠'
        };
        
        return emojis[modelId] || '🤖';
    }

    // ==================== PROMPTS E INTERAÇÃO ====================

    promptRename(chatId) {
        const chat = this.chats[chatId];
        if (!chat) return;
        
        const newTitle = prompt('Novo nome do chat:', chat.title);
        if (newTitle) {
            this.renameChat(chatId, newTitle);
        }
    }

    promptDelete(chatId) {
        if (Object.keys(this.chats).length <= 1) {
            alert('⚠️ Não é possível deletar o último chat!');
            return;
        }
        
        if (confirm('Deletar este chat?')) {
            this.deleteChat(chatId);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==================== INICIALIZAÇÃO DA SIDEBAR ====================

    initializeSidebar() {
        const chatSidebar = document.getElementById('chat-sidebar');
        const configSidebar = document.getElementById('sidebar');
        const openChatBtn = document.getElementById('open-sidebar-btn');
        const openConfigBtn = document.getElementById('menu-toggle');
        const toggleChatBtn = document.getElementById('toggle-sidebar-btn');
        const closeConfigBtn = document.getElementById('close-menu');
        const newChatBtn = document.getElementById('new-chat-btn');
        
        openChatBtn.onclick = (e) => {
            e.stopPropagation();
            chatSidebar.classList.remove('sidebar-hidden');
            configSidebar.classList.add('sidebar-hidden');
            openConfigBtn.classList.add('btn-hidden');
            openChatBtn.classList.add('btn-hidden');
        };
        
        toggleChatBtn.onclick = (e) => {
            e.stopPropagation();
            chatSidebar.classList.add('sidebar-hidden');
            openConfigBtn.classList.remove('btn-hidden');
            openChatBtn.classList.remove('btn-hidden');
        };
        
        openConfigBtn.onclick = (e) => {
            e.stopPropagation();
            configSidebar.classList.remove('sidebar-hidden');
            chatSidebar.classList.add('sidebar-hidden');
            openConfigBtn.classList.add('btn-hidden');
            openChatBtn.classList.add('btn-hidden');
        };
        
        closeConfigBtn.onclick = (e) => {
            e.stopPropagation();
            configSidebar.classList.add('sidebar-hidden');
            openConfigBtn.classList.remove('btn-hidden');
            openChatBtn.classList.remove('btn-hidden');
        };
        
        newChatBtn.onclick = (e) => {
            e.stopPropagation();
            this.createNewChat();
            chatSidebar.classList.add('sidebar-hidden');
            openConfigBtn.classList.remove('btn-hidden');
            openChatBtn.classList.remove('btn-hidden');
        };
        
        document.addEventListener('click', (e) => {
            if (chatSidebar.contains(e.target) || 
                configSidebar.contains(e.target) ||
                openChatBtn.contains(e.target) || 
                openConfigBtn.contains(e.target)) {
                return;
            }
            
            const chatWasOpen = !chatSidebar.classList.contains('sidebar-hidden');
            const configWasOpen = !configSidebar.classList.contains('sidebar-hidden');
            
            if (chatWasOpen) {
                chatSidebar.classList.add('sidebar-hidden');
                openConfigBtn.classList.remove('btn-hidden');
                openChatBtn.classList.remove('btn-hidden');
            }
            
            if (configWasOpen) {
                configSidebar.classList.add('sidebar-hidden');
                openConfigBtn.classList.remove('btn-hidden');
                openChatBtn.classList.remove('btn-hidden');
            }
        });
        
        this.renderChatList();
    }

    // ==================== PERSISTÊNCIA (LOCALSTORAGE) ====================

    saveChats() {
        localStorage.setItem('nyxie_chats', JSON.stringify(this.chats));
    }

    loadChats() {
        const saved = localStorage.getItem('nyxie_chats');
        return saved ? JSON.parse(saved) : {};
    }

    saveCurrentChatId() {
        localStorage.setItem('nyxie_current_chat', this.currentChatId);
    }

    loadCurrentChatId() {
        return localStorage.getItem('nyxie_current_chat');
    }

    // ==================== FUNÇÕES ESPECIAIS ====================

    clearAllHistory() {
        if (confirm('⚠️ Isso vai deletar TODOS os chats! Confirma?')) {
            localStorage.removeItem('nyxie_chats');
            localStorage.removeItem('nyxie_current_chat');
            this.chats = {};
            this.pendingConfirmation = null;
            this.createNewChat();
            addLine('✅ Histórico completo apagado!', 'bot-response');
        }
    }

    exportCurrentChat() {
        const currentChat = this.chats[this.currentChatId];
        if (!currentChat) return;
        
        let exportText = `# ${currentChat.title}\n\n`;
        exportText += `Criado em: ${new Date(currentChat.created).toLocaleString('pt-BR')}\n\n`;
        exportText += `---\n\n`;
        
        currentChat.messages.forEach(msg => {
            const time = new Date(msg.timestamp).toLocaleString('pt-BR');
            exportText += `**[${time}] ${msg.role.toUpperCase()}**:\n${msg.content}\n\n`;
        });
        
        const blob = new Blob([exportText], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentChat.title.replace(/[^a-z0-9]/gi, '_')}_${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
        
        addLine('✅ Chat exportado com sucesso!', 'bot-response');
    }

    showStats() {
        const totalChats = Object.keys(this.chats).length;
        const totalMessages = Object.values(this.chats).reduce((sum, chat) => 
            sum + chat.messages.length, 0
        );
        const currentChat = this.chats[this.currentChatId];
        
        addLine('╔═══════════════════════════════════════╗', 'bot-response');
        addLine('║       ESTATÍSTICAS DO HISTÓRICO       ║', 'bot-response');
        addLine('╠═══════════════════════════════════════╣', 'bot-response');
        addLine(`║ Total de chats: ${totalChats.toString().padEnd(19)}║`, 'bot-response');
        addLine(`║ Total de mensagens: ${totalMessages.toString().padEnd(15)}║`, 'bot-response');
        addLine(`║ Mensagens no chat atual: ${currentChat.messages.length.toString().padEnd(10)}║`, 'bot-response');
        addLine('╚═══════════════════════════════════════╝', 'bot-response');
    }
}

// ==================== INSTÂNCIA GLOBAL ====================
let chatManager;

// ==================== 🎨 MARKDOWN & SYNTAX HIGHLIGHT ====================

function renderMarkdownMessage(content) {
    // Detecta blocos de código COM ou SEM linguagem
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = codeBlockRegex.exec(content)) !== null) {
        if (match.index > lastIndex) {
            parts.push({
                type: 'text',
                content: content.substring(lastIndex, match.index)
            });
        }
        
        let language = match[1] || detectLanguage(match[2]);
        
        parts.push({
            type: 'code',
            language: language,
            content: match[2].trim()
        });
        
        lastIndex = match.index + match[0].length;
    }
    
    if (lastIndex < content.length) {
        parts.push({
            type: 'text',
            content: content.substring(lastIndex)
        });
    }
    
    if (parts.length === 0) {
        const lines = content.split('\n');
        lines.forEach(line => {
            if (line.trim()) addLine(line, 'bot-response');
        });
        return;
    }
    
    parts.forEach(part => {
        if (part.type === 'text') {
            const lines = part.content.split('\n');
            lines.forEach(line => {
                if (line.trim()) addLine(line, 'bot-response');
            });
        } else if (part.type === 'code') {
            addCodeBlock(part.content, part.language);
        }
    });
}

// ==================== DETECÇÃO AUTOMÁTICA DE LINGUAGEM ====================

function detectLanguage(code) {
    const c = code.trim().toLowerCase();
    
    if (c.includes('def ') || c.includes('import ') || c.includes('print(')) return 'python';
    if (c.includes('const ') || c.includes('let ') || c.includes('function ')) return 'javascript';
    if (c.includes('<html') || c.includes('<!doctype')) return 'html';
    if (c.includes('{') && c.includes('}') && c.includes(':')) return 'css';
    if (c.startsWith('{') || c.startsWith('[')) return 'json';
    if (c.includes('npm ') || c.includes('sudo ') || c.includes('apt ')) return 'bash';
    if (c.includes('select ') || c.includes('insert ')) return 'sql';
    if (c.includes('public class') || c.includes('import java')) return 'java';
    if (c.includes('#include') || c.includes('int main')) return 'cpp';
    if (c.includes('fn ') || c.includes('let mut')) return 'rust';
    if (c.includes('package ') || c.includes('func ')) return 'go';
    if (c.startsWith('<?php')) return 'php';
    if (c.includes('def ') && c.includes('end')) return 'ruby';
    if (c.startsWith('from ') || c.includes('run ')) return 'dockerfile';
    
    return 'plaintext';
}

function addCodeBlock(code, language) {
    const container = document.createElement('div');
    container.className = 'code-block-container';
    
    // Header com linguagem e botão copiar
    const header = document.createElement('div');
    header.className = 'code-block-header';
    header.innerHTML = `
        <span class="code-language">${language}</span>
        <button class="code-copy-btn" onclick="copyCode(this)">
            <span class="copy-text">copiar</span>
        </button>
    `;
    
    // Bloco de código
    const pre = document.createElement('pre');
    const codeEl = document.createElement('code');
    codeEl.className = `language-${language}`;
    codeEl.textContent = code;
    
    pre.appendChild(codeEl);
    container.appendChild(header);
    container.appendChild(pre);
    
    output.appendChild(container);
    
    // ⬅️ APLICA SYNTAX HIGHLIGHT (Prism.js)
    if (window.Prism) {
        Prism.highlightElement(codeEl);
    }
    
    scrollToBottom();
}

function copyCode(button) {
    const container = button.closest('.code-block-container');
    const code = container.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.querySelector('.copy-text').textContent;
        button.querySelector('.copy-text').textContent = 'copiado!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.querySelector('.copy-text').textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    });
}

// ==================== COMANDOS SECRETOS ====================

const secretCommands = {
    'clear': () => {
        chatManager.loadChatMessages(chatManager.currentChatId);
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
            
            const line = document.createElement('div');
            line.className = 'output-line bot-response ascii-art';
            line.textContent = `${data.ascii_art}\n\n> ${data.quote}`;
            output.appendChild(line);
            scrollToBottom();
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
            addLine(`current_chat: ${chatManager.currentChatId}`, 'bot-response');
            addLine(`history_length: ${chatManager.getCurrentChatHistory().length}`, 'bot-response');
            addLine(`pending_confirmation: ${chatManager.pendingConfirmation !== null}`, 'bot-response');
        } catch (error) {
            addLine('erro no debug', 'error');
        }
    },
    
    'theme': () => {
        const validThemes = ['lain', 'matrix', 'cyberpunk', 'void', 'marimo', 'custom'];
        addLine('temas disponíveis:', 'bot-response');
        validThemes.forEach(t => addLine(`• ${t}`, 'bot-response'));
        addLine('', 'bot-response');
        addLine('use: /theme lain, /theme matrix, etc', 'bot-response');
    },

    'model': async () => {
        const currentModel = getCurrentChatModel();
        
        try {
            const response = await fetch('/models');
            const data = await response.json();
            
            addLine('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'bot-response');
            addLine('        ⛧ MODELOS DE IA DISPONÍVEIS ⛧', 'bot-response');
            addLine('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'bot-response');
            addLine('', 'bot-response');
            
            const currentModelName = data.models.find(m => m.model_id === currentModel)?.name || 'Llama 3.3 70B';
            addLine(`› modelo atual: ${currentModelName}`, 'bot-response');
            addLine('', 'bot-response');
            
            data.models.forEach(model => {
                const marker = model.model_id === currentModel ? '→' : ' ';
                addLine(`${marker} ${model.id}. ${model.name}`, 'bot-response');
                addLine(`   ${model.tokens} tokens`, 'bot-response');
                addLine(`   ${model.description}`, 'bot-response');
                addLine(`   ideal para: ${model.best_for}`, 'bot-response');
                addLine('', 'bot-response');
            });
            
            addLine('use: /model 1, /model 2, /model 3 ou /model 4', 'bot-response');
            addLine('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'bot-response');
            
        } catch (error) {
            addLine('erro ao carregar modelos', 'error');
        }
    },
    
    'help': () => {
        const helpText = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ⛧ NYXIE TERMINAL - COMANDOS ⛧
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

› COMANDOS DE CHAT
    • history    - mostra estatísticas
    • export     - exporta chat atual (.md)
    • clearall   - apaga TODO histórico
    • clear      - limpa tela (mantém histórico)

› COMANDOS SECRETOS
    • glitch     - efeito glitch (0.5s)
    • matrix     - ???
    • lain       - reference
    • reload     - nova quote + ascii
    • void       - ...
    • debug      - mostra info
    • theme      - lista temas
    • model      - mostra modelos

› TEMAS
    • /theme [nome]
    • disponíveis: lain, matrix, cyberpunk, void, marimo, custom
    
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        `;
        addLine(helpText, 'bot-response');
    },
    
    'history': () => chatManager.showStats(),
    'export': () => chatManager.exportCurrentChat(),
    'clearall': () => chatManager.clearAllHistory()
};

// ==================== GERENCIAMENTO DE MODELO IA ====================

function getCurrentModel() {
    const savedModel = localStorage.getItem('nyxie_model');
    return savedModel || 'llama-3.3-70b-versatile';
}

function getCurrentChatModel() {
    if (!window.chatManager || !window.chatManager.currentChatId) {
        return getCurrentModel();
    }
    
    const chat = window.chatManager.chats[window.chatManager.currentChatId];
    if (!chat) return getCurrentModel();
    
    if (chat.model) {
        return chat.model;
    }
    
    const defaultModel = getCurrentModel();
    chat.model = defaultModel;
    window.chatManager.saveChats();
    
    return defaultModel;
}

function setModel(modelNumber) {
    const modelMap = {
        '1': 'llama-3.1-8b-instant',
        '2': 'llama-3.3-70b-versatile',
        '3': 'openai/gpt-oss-20b',
        '4': 'openai/gpt-oss-120b'
    };
    
    const modelId = modelMap[modelNumber];
    if (modelId) {
        localStorage.setItem('nyxie_model', modelId);
        
        if (window.chatManager && window.chatManager.currentChatId) {
            const chat = window.chatManager.chats[window.chatManager.currentChatId];
            if (chat) {
                chat.model = modelId;
                chat.modified = new Date().toISOString();
                window.chatManager.saveChats();
                window.chatManager.renderChatList(); // ⬅️ ATUALIZA EMOJI
            }
        }
        
        return modelId;
    }
    return null;
}

async function getModelName(modelId) {
    try {
        const response = await fetch('/models');
        const data = await response.json();
        const model = data.models.find(m => m.model_id === modelId);
        return model ? model.name : 'Desconhecido';
    } catch {
        return 'Desconhecido';
    }
}

window.updateModelIndicator = async function() {
    const modelId = getCurrentChatModel(); 
    const modelName = await getModelName(modelId);
    
    // Atualiza no menu
    const indicator = document.getElementById('model-name');
    if (indicator) {
        indicator.textContent = modelName.replace('Llama ', '').replace('GPT OSS ', 'GPT ');
    }
};

// ==================== EVENT LISTENER PRINCIPAL ====================

input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const message = input.value;
        if (!message.trim()) return;

        // ⬅️ SISTEMA DE CONFIRMAÇÃO DE MODELO
        if (chatManager.pendingConfirmation) {
            const msgLower = message.toLowerCase().trim();
            
            // Confirma
            if (['sim', 's', 'yes', 'pode', 'vai', 'ok', 'beleza', 'troca'].includes(msgLower)) {
                addLine(`> ${message}`, 'user-input');
                input.value = '';
                
                const originalMessage = chatManager.pendingConfirmation.originalMessage;
                const recommendedModel = chatManager.pendingConfirmation.recommendedModel;
                
                // Troca modelo
                const modelNumber = {
                    'llama-3.1-8b-instant': '1',
                    'llama-3.3-70b-versatile': '2',
                    'openai/gpt-oss-20b': '3',
                    'openai/gpt-oss-120b': '4'
                }[recommendedModel];
                
                setModel(modelNumber);
                await window.updateModelIndicator();
                
                const modelName = await getModelName(recommendedModel);
                addLine(`✅ modelo trocado para: ${modelName}`, 'bot-response');
                
                chatManager.pendingConfirmation = null;
                
                // Processa mensagem original
                await processNormalMessage(originalMessage);
                return;
            }
            
            // Rejeita
            if (['não', 'nao', 'n', 'no', 'cancela', 'deixa', 'fica'].includes(msgLower)) {
                addLine(`> ${message}`, 'user-input');
                input.value = '';
                
                const currentModelName = await getModelName(getCurrentChatModel());
                addLine(`ok, mantendo o modelo atual (${currentModelName})`, 'bot-response');
                addLine('se quiser trocar depois: /model', 'bot-response');
                
                chatManager.pendingConfirmation = null;
                return;
            }
            
            // Não entendeu
            addLine(`> ${message}`, 'user-input');
            input.value = '';
            addLine('não entendi. responde:', 'bot-response');
            addLine('• sim / pode / vai → pra trocar pro modelo forte', 'bot-response');
            addLine('• não / cancela → pra manter o atual', 'bot-response');
            return;
        }

        if (message.startsWith('/')) {
            const args = message.slice(1).trim().split(/\s+/);
            const comando = args[0].toLowerCase();
            const parametro = args[1];
            
            addLine(`> ${message}`, 'user-input');
            input.value = '';
            
            chatManager.addMessage('user', message);
            
            if (comando === 'model') {
                if (!parametro) {
                    await secretCommands['model']();
                    chatManager.addMessage('assistant', 'Lista de modelos');
                    return;
                }
                
                if (['1', '2', '3', '4'].includes(parametro)) {
                    const modelId = setModel(parametro);
                    const modelName = await getModelName(modelId);
                    
                    if (window.updateModelIndicator) {
                        await window.updateModelIndicator();
                    }
                    
                    const response = `> modelo alterado: ${modelName}`;
                    addLine(response, 'bot-response');
                    chatManager.addMessage('assistant', response);
                } else {
                    addLine('escolha entre 1-4', 'error');
                    chatManager.addMessage('assistant', 'modelo inválido');
                }
                return;
            }

            if (comando === 'theme') {
                handleThemeCommand(parametro);
                return;
            }
            
            if (secretCommands[comando]) {
                await secretCommands[comando]();
                chatManager.addMessage('assistant', `Comando executado: ${comando}`);
                return;
            }
            
            const response = `comando '/${comando}' não encontrado. digite /help para ver comandos`;
            addLine(response, 'error');
            chatManager.addMessage('assistant', response);
            return;
        }
        
        await processNormalMessage(message);
    }
});

// ==================== FUNÇÕES DE PROCESSAMENTO ====================

function handleThemeCommand(themeName) {
    const validThemes = ['lain', 'matrix', 'cyberpunk', 'void', 'marimo', 'custom'];
    
    if (!themeName) {
        secretCommands['theme']();
        chatManager.addMessage('assistant', 'Lista de temas disponíveis');
        return;
    }
    
    themeName = themeName.toLowerCase();
    
    if (validThemes.includes(themeName)) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('nyxie_theme', themeName);
        
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme') === themeName);
        });
        
        toggleCustomMenu(themeName === 'custom');
        
        const response = `> tema alterado: ${themeName}`;
        addLine(response, 'bot-response');
        chatManager.addMessage('assistant', response);
        
        const openChatBtn = document.getElementById('open-sidebar-btn');
        const openConfigBtn = document.getElementById('menu-toggle');
        openChatBtn.classList.remove('btn-hidden');
        openConfigBtn.classList.remove('btn-hidden');
    } else {
        addLine('tema inválido', 'error');
        addLine('', 'bot-response');
        secretCommands['theme']();
        chatManager.addMessage('assistant', 'tema inválido');
    }
}

async function processNormalMessage(message) {
    addLine(`> ${message}`, 'user-input');
    input.value = '';
    
    chatManager.addMessage('user', message);
    
    const thinkingLine = document.createElement('div');
    thinkingLine.className = 'output-line bot-response';
    thinkingLine.textContent = '...';
    thinkingLine.id = 'thinking';
    output.appendChild(thinkingLine);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: getUserId(),
                message: message,
                history: chatManager.getCurrentChatHistory(),
                model: getCurrentChatModel()
            })
        });
        
        document.getElementById('thinking')?.remove();
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Erro HTTP:', response.status, errorText);
            const errorMsg = `ERROR ${response.status}: servidor retornou erro`;
            addLine(errorMsg, 'error');
            chatManager.addMessage('assistant', errorMsg);
            return;
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Resposta não é JSON:', text);
            const errorMsg = 'CONNECTION_ERROR: resposta inválida do servidor';
            addLine(errorMsg, 'error');
            chatManager.addMessage('assistant', errorMsg);
            return;
        }
        
        const data = await response.json();
        
        if (data.error) {
            const errorMsg = `ERROR: ${data.error}`;
            addLine(errorMsg, 'error');
            chatManager.addMessage('assistant', errorMsg);
            return;
        }
        
        // ⬅️ SISTEMA DE CONFIRMAÇÃO DE MODELO
        if (data.model_recommendation) {
            chatManager.pendingConfirmation = {
                originalMessage: message,
                recommendedModel: data.model_recommendation.model_id,
                reason: data.model_recommendation.reason
            };
            
            addLine('', 'bot-response');
            addLine(`⚠️ ${data.model_recommendation.reason}`, 'bot-response');
            addLine('', 'bot-response');
            addLine(`quer trocar pro ${data.model_recommendation.model_name}?`, 'bot-response');
            addLine('modelo atual: ' + await getModelName(getCurrentChatModel()), 'bot-response');
            addLine('', 'bot-response');
            addLine('responde sim pra trocar ou não pra manter o atual', 'bot-response');
            
            chatManager.addMessage('assistant', data.response);
            return;
        }
        
        chatManager.addMessage('assistant', data.response);
        
        // ⬅️ USA MARKDOWN RENDERER COM SYNTAX HIGHLIGHT
        typeWriterMarkdown(data.response);
        
    } catch (error) {
        document.getElementById('thinking')?.remove();
        console.error('Erro completo:', error);
        const errorMsg = 'CONNECTION_ERROR: ' + error.message;
        addLine(errorMsg, 'error');
        chatManager.addMessage('assistant', errorMsg);
    }
}

// ==================== TYPEWRITER COM MARKDOWN ====================

function typeWriterMarkdown(text) {
    // Detecta blocos de código
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = codeBlockRegex.exec(text)) !== null) {
        // Texto antes do bloco
        if (match.index > lastIndex) {
            parts.push({
                type: 'text',
                content: text.substring(lastIndex, match.index)
            });
        }
        
        // Bloco de código
        parts.push({
            type: 'code',
            language: match[1] || detectLanguage(match[2]),
            content: match[2].trim()
        });
        
        lastIndex = match.index + match[0].length;
    }
    
    // Texto final
    if (lastIndex < text.length) {
        parts.push({
            type: 'text',
            content: text.substring(lastIndex)
        });
    }
    
    // Se não tem código, faz typewriter normal
    if (parts.length === 0) {
        typeWriter(text);
        return;
    }
    
    // Renderiza partes
    let partIndex = 0;
    
    function renderNextPart() {
        if (partIndex >= parts.length) return;
        
        const part = parts[partIndex];
        
        if (part.type === 'code') {
            // Código aparece instantaneamente
            addCodeBlock(part.content, part.language);
            partIndex++;
            renderNextPart();
        } else {
            // Texto faz typewriter
            const lines = part.content.split('\n');
            let lineIndex = 0;
            
            function typeLine() {
                if (lineIndex >= lines.length) {
                    partIndex++;
                    renderNextPart();
                    return;
                }
                
                const line = lines[lineIndex];
                if (line.trim()) {
                    typeWriter(line, 0, () => {
                        lineIndex++;
                        typeLine();
                    });
                } else {
                    lineIndex++;
                    typeLine();
                }
            }
            
            typeLine();
        }
    }
    
    renderNextPart();
}

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

function scrollToBottom() {
    const crt = document.getElementById('crt');
    crt.scrollTo({
        top: crt.scrollHeight,
        behavior: 'smooth' 
    });
}

function addLine(text, className = '') {
    const line = document.createElement('div');
    line.className = `output-line ${className}`;
    line.textContent = text;
    output.appendChild(line);
    scrollToBottom(); 
}

function typeWriter(text, index = 0, callback = null) {
    if (index === 0) {
        const line = document.createElement('div');
        line.className = 'output-line bot-response';
        line.id = 'current-typing';
        output.appendChild(line);
    }
    
    const currentLine = document.getElementById('current-typing');
    if (index < text.length) {
        currentLine.textContent += text.charAt(index);
        scrollToBottom();
        setTimeout(() => typeWriter(text, index + 1, callback), 30);
    } else {
        currentLine.id = '';
        if (callback) callback();
    }
}

// ==================== INICIALIZAÇÃO ====================

window.onload = async () => {
    chatManager = new ChatManager();
    window.chatManager = chatManager;
    
    await chatManager.loadChatMessages(chatManager.currentChatId);
    
    scrollToBottom();
    
    const savedTheme = localStorage.getItem('nyxie_theme') || 'lain';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    document.querySelectorAll('.theme-btn').forEach(btn => {
        if (btn.getAttribute('data-theme') === savedTheme) {
            btn.classList.add('active');
        }
    });
    
    if (savedTheme === 'custom') {
        toggleCustomMenu(true);
        loadCustomColors();
    }
    
    if (window.updateModelIndicator) {
        await window.updateModelIndicator();
    }
};

// ==================== MENU LATERAL E TEMAS ====================

const toggleCustomMenu = (show) => {
    const customSection = document.getElementById('custom-colors-section');
    if (show) {
        customSection.classList.remove('custom-hidden');
    } else {
        customSection.classList.add('custom-hidden');
    }
};

document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        
        const theme = btn.getAttribute('data-theme');
        
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('nyxie_theme', theme);
        
        document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        toggleCustomMenu(theme === 'custom');
        
        addLine(`> tema alterado: ${theme}`, 'bot-response');
    });
});

// ==================== CUSTOM COLOR PICKER ====================

window.pickerCallback = (targetId, hex) => {
    const colorType = targetId.replace('-preview', '');
    
    document.getElementById(`${colorType}-color`).value = hex;
    document.getElementById(`${colorType}-hex`).value = hex;
    document.getElementById(`${colorType}-preview`).style.background = hex;
    
    saveAndApplyColors();
};

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
    
    previewEl.addEventListener('click', () => {
        if (window.colorPicker) {
            window.colorPicker.open(preview, pickerEl.value);
        }
    });
    
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
    
    Object.keys(colors).forEach(key => {
        if (isTooDark(colors[key])) {
            colors[key] = '#1E1E1E';
            addLine('> cor muito escura detectada, ajustando...', 'error');
        }
    });
    
    localStorage.setItem('nyxie_custom_colors', JSON.stringify(colors));
    applyCustomColors(colors);
    
    if (document.documentElement.getAttribute('data-theme') !== 'custom') {
        document.documentElement.setAttribute('data-theme', 'custom');
        localStorage.setItem('nyxie_theme', 'custom');
        
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme') === 'custom');
        });
        
        toggleCustomMenu(true);
        addLine('> tema custom ativado', 'bot-response');
    }
};

const applyCustomColors = (colors) => {
    document.documentElement.style.setProperty('--custom-primary', colors.primary);
    document.documentElement.style.setProperty('--custom-secondary', colors.secondary);
    document.documentElement.style.setProperty('--custom-prompt', colors.prompt);
    document.documentElement.style.setProperty('--custom-error', colors.error);
};

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

loadCustomColors();