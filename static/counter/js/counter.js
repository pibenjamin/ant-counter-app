const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const speciesInput = document.getElementById('species');
const canvasContainer = document.getElementById('canvasContainer');
const zoomSlider = document.getElementById('zoomLevel');
const zoomDisplay = document.getElementById('zoomDisplay');
const gridSelect = document.getElementById('gridSize');

let clicks = [];
let image = null;
let startTime = null;
let currentZoom = 1.0;
let currentGrid = 4;
let baseWidth = 0;
let baseHeight = 0;
let isDragging = false;
let startX = 0;
let startY = 0;
let scrollLeft = 0;
let scrollTop = 0;
let hasMoved = false;

function loadImage() {
    const img = new Image();
    img.onload = function () {
        const maxWidth = 1200;
        const maxHeight = 800;
        let w = img.width;
        let h = img.height;

        if (w > maxWidth) { h = (h * maxWidth) / w; w = maxWidth; }
        if (h > maxHeight) { w = (w * maxHeight) / h; h = maxHeight; }

        baseWidth = Math.round(w);
        baseHeight = Math.round(h);
        image = img;
        startTime = new Date();

        clicks = (window.EXISTING_ANNOTATIONS || []).map(a => ({ x: a.x, y: a.y, label: a.label }));
        clicks.sort((a, b) => a.label - b.label);

        canvas.style.display = 'block';
        updateCanvasSize();
        redraw();
        updateStats();
    };
    img.src = window.IMAGE_URL;
}

// Drag
canvasContainer.addEventListener('mousedown', function (e) {
    if (currentZoom <= 1) return;
    isDragging = true;
    hasMoved = false;
    canvasContainer.classList.add('dragging');
    startX = e.pageX - canvasContainer.offsetLeft;
    startY = e.pageY - canvasContainer.offsetTop;
    scrollLeft = canvasContainer.scrollLeft;
    scrollTop = canvasContainer.scrollTop;
});

canvasContainer.addEventListener('mouseleave', function () {
    isDragging = false;
    canvasContainer.classList.remove('dragging');
});

canvasContainer.addEventListener('mouseup', function () {
    isDragging = false;
    canvasContainer.classList.remove('dragging');
});

canvasContainer.addEventListener('mousemove', function (e) {
    if (!isDragging) return;
    e.preventDefault();
    hasMoved = true;
    const x = e.pageX - canvasContainer.offsetLeft;
    const y = e.pageY - canvasContainer.offsetTop;
    canvasContainer.scrollLeft = scrollLeft - (x - startX) * 2;
    canvasContainer.scrollTop = scrollTop - (y - startY) * 2;
});

// Click to add
canvas.addEventListener('click', function (e) {
    if (!image || hasMoved) { hasMoved = false; return; }
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / currentZoom;
    const y = (e.clientY - rect.top) / currentZoom;
    clicks.push({ x: Math.round(x), y: Math.round(y) });
    updateStats();
    redraw();
});

// Right-click to remove
canvas.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    if (!image || clicks.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / currentZoom;
    const y = (e.clientY - rect.top) / currentZoom;

    let closest = -1, minDist = Infinity;
    clicks.forEach((c, i) => {
        const d = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
        if (d < 20 && d < minDist) { minDist = d; closest = i; }
    });
    if (closest !== -1) {
        clicks.splice(closest, 1);
        updateStats();
        redraw();
    }
});

// Zoom
zoomSlider.addEventListener('input', function () {
    currentZoom = this.value / 100;
    zoomDisplay.textContent = this.value + '%';
    updateCanvasSize();
    redraw();
});

// Grid
gridSelect.addEventListener('change', function () {
    currentGrid = parseInt(this.value);
    redraw();
});

speciesInput.addEventListener('input', updateStats);

function updateCanvasSize() {
    canvas.width = baseWidth * currentZoom;
    canvas.height = baseHeight * currentZoom;
    if (currentZoom > 1) {
        canvas.classList.add('draggable');
    } else {
        canvas.classList.remove('draggable');
    }
}

function redraw() {
    if (!image) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

    // Grid
    if (currentGrid > 0) {
        ctx.strokeStyle = 'rgba(255, 165, 0, 0.7)';
        ctx.lineWidth = 2;
        const cw = canvas.width / currentGrid;
        const ch = canvas.height / currentGrid;
        for (let i = 1; i < currentGrid; i++) {
            ctx.beginPath(); ctx.moveTo(i * cw, 0); ctx.lineTo(i * cw, canvas.height); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(0, i * ch); ctx.lineTo(canvas.width, i * ch); ctx.stroke();
        }
        ctx.font = `bold ${Math.max(16, 20 * currentZoom)}px Arial`;
        ctx.fillStyle = 'rgba(255, 165, 0, 0.9)';
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.lineWidth = 3;
        let zn = 1;
        for (let r = 0; r < currentGrid; r++) {
            for (let c = 0; c < currentGrid; c++) {
                const tx = c * cw + 15, ty = r * ch + 30;
                const text = String.fromCharCode(64 + zn);
                ctx.strokeText(text, tx, ty);
                ctx.fillText(text, tx, ty);
                zn++;
            }
        }
    }

    // Markers
    clicks.forEach((c, i) => {
        const hue = (i * 40) % 360;
        const ms = 5 * currentZoom;
        const fs = Math.max(6, 8 * currentZoom);
        ctx.beginPath();
        ctx.arc(c.x * currentZoom, c.y * currentZoom, ms, 0, 2 * Math.PI);
        ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.font = `bold ${fs}px Arial`;
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 3;
        const label = String(i + 1);
        ctx.strokeText(label, c.x * currentZoom + 15, c.y * currentZoom + 5);
        ctx.fillText(label, c.x * currentZoom + 15, c.y * currentZoom + 5);
    });
}

function updateStats() {
    const count = clicks.length;
    const species = speciesInput.value || 'fourmis';
    document.getElementById('totalCount').textContent = count;
    document.getElementById('speciesDisplay').textContent = species;
    document.getElementById('statCount').textContent = count;
    document.getElementById('statSpecies').textContent = species;
    if (startTime) {
        const elapsed = Math.floor((new Date() - startTime) / 1000);
        const m = Math.floor(elapsed / 60);
        const s = elapsed % 60;
        document.getElementById('statTime').textContent = `${m}:${s.toString().padStart(2, '0')}`;
    }
}

function undoLast() {
    if (clicks.length > 0) { clicks.pop(); updateStats(); redraw(); }
}

function resetAll() {
    if (confirm('Réinitialiser tous les marqueurs ?')) { clicks = []; updateStats(); redraw(); }
}

function saveAnnotations() {
    const data = {
        annotations: clicks.map((c, i) => ({ x: Math.round(c.x), y: Math.round(c.y), label: i + 1 })),
        species: speciesInput.value,
    };
    fetch(window.SAVE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(d => alert(`✅ ${d.count} annotations sauvegardées !`))
        .catch(() => alert('❌ Erreur lors de la sauvegarde'));
}

function downloadResults() {
    if (!image) { alert('Chargez d\'abord une image'); return; }
    const link = document.createElement('a');
    link.download = `counted_${speciesInput.value.replace(/\s+/g, '_')}_${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();

    const jsonData = {
        species: speciesInput.value,
        count: clicks.length,
        timestamp: new Date().toISOString(),
        image_id: window.IMAGE_ID,
        clicks: clicks.map((c, i) => ({ id: i + 1, x: c.x, y: c.y })),
    };
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
    const jl = document.createElement('a');
    jl.download = `data_${speciesInput.value.replace(/\s+/g, '_')}_${Date.now()}.json`;
    jl.href = URL.createObjectURL(blob);
    jl.click();
    alert(`✅ Téléchargement terminé !\n🐜 ${clicks.length} fourmis comptées`);
}

setInterval(updateStats, 1000);
loadImage();
