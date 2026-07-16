// static/js/color-picker.js

class CustomColorPicker {
    constructor() {
        this.currentColor = { r: 177, g: 156, b: 217 };
        this.currentHue = 270;
        this.currentTarget = null;
        
        this.modal = document.getElementById('color-picker-modal');
        this.colorCanvas = document.getElementById('color-canvas');
        this.hueCanvas = document.getElementById('hue-canvas');
        this.preview = document.getElementById('picker-preview');
        this.hexInput = document.getElementById('picker-hex-input');
        this.rInput = document.getElementById('picker-r');
        this.gInput = document.getElementById('picker-g');
        this.bInput = document.getElementById('picker-b');
        this.hueSelector = document.getElementById('hue-selector');
        
        this.colorCtx = this.colorCanvas.getContext('2d');
        this.hueCtx = this.hueCanvas.getContext('2d');
        
        this.init();
    }
    
    init() {
        this.drawHueSlider();
        this.drawColorCanvas();
        
        // Event listeners
        this.colorCanvas.addEventListener('mousedown', (e) => {
            this.onColorCanvasClick(e);
            this.isDragging = true;
        });
        
        this.colorCanvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                this.onColorCanvasClick(e);
            }
        });
        
        document.addEventListener('mouseup', () => {
            this.isDragging = false;
        });
        
        this.colorCanvas.addEventListener('touchstart', (e) => this.onColorCanvasClick(e));
        this.colorCanvas.addEventListener('touchmove', (e) => this.onColorCanvasClick(e));
        
        this.hueCanvas.addEventListener('mousedown', (e) => this.onHueCanvasClick(e));
        this.hueCanvas.addEventListener('touchstart', (e) => this.onHueCanvasClick(e));
        
        this.hexInput.addEventListener('input', (e) => this.onHexInput(e));
        this.rInput.addEventListener('input', (e) => this.onRGBInput());
        this.gInput.addEventListener('input', (e) => this.onRGBInput());
        this.bInput.addEventListener('input', (e) => this.onRGBInput());
        
        document.getElementById('close-picker').addEventListener('click', () => this.close());
        document.getElementById('picker-confirm').addEventListener('click', () => this.close());
        
        // Fecha ao clicar fora
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }
    
    open(targetId, currentColor) {
        this.currentTarget = targetId;
        
        // Parse da cor atual
        const hex = currentColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        this.currentColor = { r, g, b };
        this.updateAllInputs();
        
        this.modal.classList.remove('picker-modal-hidden');
    }
    
    close() {
        this.modal.classList.add('picker-modal-hidden');
    }
    
    applyRealtime() {
        if (this.currentTarget && window.pickerCallback) {
            const hex = this.rgbToHex(this.currentColor.r, this.currentColor.g, this.currentColor.b);
            window.pickerCallback(this.currentTarget, hex);
        }
    }
    
    drawHueSlider() {
        const width = this.hueCanvas.width;
        const height = this.hueCanvas.height;
        
        const gradient = this.hueCtx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, '#ff0000');
        gradient.addColorStop(0.17, '#ffff00');
        gradient.addColorStop(0.33, '#00ff00');
        gradient.addColorStop(0.5, '#00ffff');
        gradient.addColorStop(0.67, '#0000ff');
        gradient.addColorStop(0.83, '#ff00ff');
        gradient.addColorStop(1, '#ff0000');
        
        this.hueCtx.fillStyle = gradient;
        this.hueCtx.fillRect(0, 0, width, height);
    }
    
    drawColorCanvas() {
        const width = this.colorCanvas.width;
        const height = this.colorCanvas.height;
        
        const hueColor = this.hueToRgb(this.currentHue);
        
        const horizGradient = this.colorCtx.createLinearGradient(0, 0, width, 0);
        horizGradient.addColorStop(0, '#ffffff');
        horizGradient.addColorStop(1, `rgb(${hueColor.r}, ${hueColor.g}, ${hueColor.b})`);
        
        this.colorCtx.fillStyle = horizGradient;
        this.colorCtx.fillRect(0, 0, width, height);
        
        const vertGradient = this.colorCtx.createLinearGradient(0, 0, 0, height);
        vertGradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
        vertGradient.addColorStop(1, 'rgba(0, 0, 0, 1)');
        
        this.colorCtx.fillStyle = vertGradient;
        this.colorCtx.fillRect(0, 0, width, height);
    }
    
    onColorCanvasClick(e) {
        e.preventDefault();
        const rect = this.colorCanvas.getBoundingClientRect();
        const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
        const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
        
        const scaleX = this.colorCanvas.width / rect.width;
        const scaleY = this.colorCanvas.height / rect.height;
        
        const canvasX = Math.max(0, Math.min(this.colorCanvas.width - 1, x * scaleX));
        const canvasY = Math.max(0, Math.min(this.colorCanvas.height - 1, y * scaleY));
        
        const imageData = this.colorCtx.getImageData(canvasX, canvasY, 1, 1).data;
        
        let color = {
            r: imageData[0],
            g: imageData[1],
            b: imageData[2]
        };
        
        // ⬇️ ADICIONA ISSO - Bloqueia preto
        color = this.adjustIfTooDark(color);
        
        this.currentColor = color;
        
        this.updateAllInputs();
        this.applyRealtime();
    }
    
    onHueCanvasClick(e) {
        e.preventDefault();
        const rect = this.hueCanvas.getBoundingClientRect();
        const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
        
        const scaleX = this.hueCanvas.width / rect.width;
        const canvasX = Math.max(0, Math.min(this.hueCanvas.width - 1, x * scaleX));
        
        this.currentHue = (canvasX / this.hueCanvas.width) * 360;
        this.hueSelector.style.left = `${x}px`;
        
        this.drawColorCanvas();
        this.applyRealtime();
    }
    
    onHexInput(e) {
        let value = e.target.value.trim();
        
        if (!value.startsWith('#')) {
            value = '#' + value;
        }
        
        if (/^#[0-9A-F]{6}$/i.test(value)) {
            const hex = value.replace('#', '');
            let color = {
                r: parseInt(hex.substr(0, 2), 16),
                g: parseInt(hex.substr(2, 2), 16),
                b: parseInt(hex.substr(4, 2), 16)
            };
            
            // ⬇️ ADICIONA ISSO - Bloqueia preto
            color = this.adjustIfTooDark(color);
            
            this.currentColor = color;
            this.updateRGBInputs();
            this.updatePreview();
            this.applyRealtime();
        }
    }
    
    onRGBInput() {
        const r = parseInt(this.rInput.value) || 0;
        const g = parseInt(this.gInput.value) || 0;
        const b = parseInt(this.bInput.value) || 0;
        
        let color = {
            r: Math.max(0, Math.min(255, r)),
            g: Math.max(0, Math.min(255, g)),
            b: Math.max(0, Math.min(255, b))
        };
        
        // ⬇️ ADICIONA ISSO - Bloqueia preto
        color = this.adjustIfTooDark(color);
        
        this.currentColor = color;
        
        this.updateHexInput();
        this.updatePreview();
        this.applyRealtime();
    }
    
    updateAllInputs() {
        this.updateHexInput();
        this.updateRGBInputs();
        this.updatePreview();
    }
    
    updateHexInput() {
        const hex = this.rgbToHex(this.currentColor.r, this.currentColor.g, this.currentColor.b);
        this.hexInput.value = hex;
    }
    
    updateRGBInputs() {
        this.rInput.value = this.currentColor.r;
        this.gInput.value = this.currentColor.g;
        this.bInput.value = this.currentColor.b;
    }
    
    updatePreview() {
        const hex = this.rgbToHex(this.currentColor.r, this.currentColor.g, this.currentColor.b);
        this.preview.style.background = hex;
    }
    
    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('').toUpperCase();
    }
    
    hueToRgb(hue) {
        const h = hue / 60;
        const c = 255;
        const x = c * (1 - Math.abs(h % 2 - 1));
        
        let r = 0, g = 0, b = 0;
        
        if (h >= 0 && h < 1) { r = c; g = x; }
        else if (h >= 1 && h < 2) { r = x; g = c; }
        else if (h >= 2 && h < 3) { g = c; b = x; }
        else if (h >= 3 && h < 4) { g = x; b = c; }
        else if (h >= 4 && h < 5) { r = x; b = c; }
        else if (h >= 5 && h < 6) { r = c; b = x; }
        
        return { r: Math.round(r), g: Math.round(g), b: Math.round(b) };
    }

    isColorTooDark(r, g, b) {
    // Calcula luminosidade (0-255)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
    
    // Se for muito escuro (menos de 20 de luminosidade), retorna true
    return luminance < 20;
    }

    adjustIfTooDark(color) {
        if (this.isColorTooDark(color.r, color.g, color.b)) {
            // Flash de aviso
            if (this.preview) {
                this.preview.style.animation = 'shake 0.3s';
                setTimeout(() => {
                    this.preview.style.animation = '';
                }, 300);
            }
            
            // Retorna cinza escuro ao invés de preto
            return { r: 30, g: 30, b: 30 };
        }
        return color;
    }
}

// Inicializa o picker quando o DOM carregar
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Inicializando color picker...');
    window.colorPicker = new CustomColorPicker();
    console.log('✅ Color picker pronto!');
});