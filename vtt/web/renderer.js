const canvas = document.getElementById('map-canvas');
const container = document.getElementById('map-container');
const ctx = canvas.getContext('2d');

// Game state (matches Python engine format)
let state = {
  map_size: [60, 60],
  tokens: {},
  initiative: [],
  turn: null,
  round: 0,
  fog: [],
  map_background: null,
  lights: [],
  walls: [],
  difficult_terrain: [],
  combat_active: false
};

let zoom = 1;
let showGrid = true;
let showFog = false;
let dragToken = null;
let dragOffset = { x: 0, y: 0 };
const CELL_SIZE = 40;

// Measurement state
let rulerMode = false;
let rulerStart = null;
let rulerEnd = null;
let templateMode = null; // 'sphere', 'cube', 'cone', 'line'
let templateOrigin = null;
let templateSize = 3; // radius in cells
let templateCells = [];

// Wall drawing state
let wallMode = null; // 'wall' or 'door'
let wallStart = null;

// Selection state
let selectedTokens = [];
let clipboard = null;
let selectionBox = null;
let hoveredToken = null;

// Token animation
let tokenAnimations = {}; // { token_id: { fromX, fromY, toX, toY, progress } }
const ANIM_SPEED = 0.15; // Progress per frame

// Visual effects
let effects = []; // { type, x, y, radius, color, life, maxLife }
const EFFECT_DECAY = 0.02;

// --- WebSocket ---
let ws;
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => addChat('System', 'Connected to VTT');
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    handleMessage(msg);
  };
  ws.onclose = () => { addChat('System', 'Disconnected. Reconnecting...'); setTimeout(connect, 2000); };
}

function handleMessage(msg) {
  if (msg.type === 'state') {
    state = msg.data;
    render();
    updateTokenList();
  } else if (msg.type === 'event') {
    handleEvent(msg.event);
  } else if (msg.type === 'token_added') {
    if (msg.token) state.tokens[msg.token.id] = msg.token;
    render(); updateTokenList();
  } else if (msg.type === 'token_moved') {
    if (state.tokens[msg.id]) {
      const t = state.tokens[msg.id];
      tokenAnimations[msg.id] = { fromX: t.x, fromY: t.y, toX: msg.x, toY: msg.y, progress: 0 };
      t.x = msg.x;
      t.y = msg.y;
      animateLoop();
    }
  } else if (msg.type === 'token_removed') {
    delete state.tokens[msg.id]; render(); updateTokenList();
  } else if (msg.type === 'token_updated') {
    if (msg.token) state.tokens[msg.token.id] = msg.token;
    render(); updateTokenList();
  } else if (msg.type === 'chat') {
    addChat(msg.message.sender, msg.message.text, msg.message.isRoll);
  } else if (msg.type === 'map_background') {
    state.map_background = msg.url; render();
  } else if (msg.type === 'combat_started') {
    state.combat_active = true; state.initiative = msg.initiative || []; state.turn = msg.turn; state.round = msg.round || 1;
    render(); updateInitiative();
  } else if (msg.type === 'turn_ended') {
    state.turn = msg.current_turn; state.round = msg.round;
    render(); updateInitiative();
  } else if (msg.type === 'damage_applied') {
    if (state.tokens[msg.token_id]) { state.tokens[msg.token_id].hp = msg.hp; render(); updateTokenList(); }
  } else if (msg.type === 'effect') {
    const e = msg.effect;
    effects.push({ type: e.type, x: e.x, y: e.y, radius: e.radius || 2, life: 1, maxLife: 1 });
    animateLoop();
  }
}

function handleEvent(event) {
  const d = event.data || {};
  switch (event.type) {
    case 'token_spawned': if (d.token) { state.tokens[d.token.id] = d.token; render(); updateTokenList(); } break;
    case 'token_moved': if (state.tokens[d.token_id]) { state.tokens[d.token_id].x = d.to[0]; state.tokens[d.token_id].y = d.to[1]; render(); } break;
    case 'token_removed': if (d.token) { delete state.tokens[d.token.id]; render(); updateTokenList(); } break;
    case 'damage_applied':
      if (state.tokens[d.token_id]) {
        state.tokens[d.token_id].hp = d.hp;
        const t = state.tokens[d.token_id];
        effects.push({ type: 'blood', x: t.x, y: t.y, radius: 1, life: 1, maxLife: 1 });
        render(); updateTokenList();
      }
      break;
    case 'heal_applied':
      if (state.tokens[d.token_id]) {
        state.tokens[d.token_id].hp = d.hp;
        const t = state.tokens[d.token_id];
        effects.push({ type: 'heal', x: t.x, y: t.y, radius: 0, life: 1, maxLife: 1 });
        render(); updateTokenList();
      }
      break;
    case 'combat_started': state.combat_active = true; state.initiative = d.initiative || []; state.turn = d.turn; render(); updateInitiative(); break;
    case 'turn_ended': state.turn = d.current_turn; state.round = d.round; render(); updateInitiative(); break;
    case 'dice_rolled': break;
  }
}

// --- Rendering ---
function render() {
  const [w, h] = state.map_size;
  const cs = CELL_SIZE;
  canvas.width = w * cs;
  canvas.height = h * cs;
  canvas.style.transform = `scale(${zoom})`;
  canvas.style.width = (w * cs) + 'px';
  canvas.style.height = (h * cs) + 'px';

  // Background
  if (state.map_background) {
    const img = new Image();
    img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    img.onerror = () => { ctx.fillStyle = '#1a1a2e'; ctx.fillRect(0, 0, canvas.width, canvas.height); };
    img.src = state.map_background;
  } else {
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // Grid
  if (showGrid) {
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= w; x++) { ctx.beginPath(); ctx.moveTo(x * cs, 0); ctx.lineTo(x * cs, h * cs); ctx.stroke(); }
    for (let y = 0; y <= h; y++) { ctx.beginPath(); ctx.moveTo(0, y * cs); ctx.lineTo(w * cs, y * cs); ctx.stroke(); }
  }

  // Lights
  state.lights.forEach(l => {
    const grd = ctx.createRadialGradient(l.x * cs + cs/2, l.y * cs + cs/2, 0, l.x * cs + cs/2, l.y * cs + cs/2, l.radius * cs);
    grd.addColorStop(0, l.color + '40');
    grd.addColorStop(1, 'transparent');
    ctx.fillStyle = grd;
    ctx.beginPath();
    ctx.arc(l.x * cs + cs/2, l.y * cs + cs/2, l.radius * cs, 0, Math.PI * 2);
    ctx.fill();
  });

  // Tokens
  Object.values(state.tokens).forEach(t => {
    // Skip hidden tokens (for players — GM sees all)
    if (t.hidden) {
      ctx.globalAlpha = 0.3;
    }

    const size = TOKEN_SIZES[t.size] || 1;
    const tokenW = size * cs;
    const tokenH = size * cs;

    // Animation
    let drawX = t.x;
    let drawY = t.y;
    if (tokenAnimations[t.id]) {
      const anim = tokenAnimations[t.id];
      anim.progress = Math.min(1, anim.progress + ANIM_SPEED);
      drawX = anim.fromX + (anim.toX - anim.fromX) * anim.progress;
      drawY = anim.fromY + (anim.toY - anim.fromY) * anim.progress;
      if (anim.progress >= 1) {
        delete tokenAnimations[t.id];
      }
    }

    const tx = drawX * cs + tokenW / 2;
    const ty = drawY * cs + tokenH / 2;
    const r = tokenW * 0.4;

    if (t.image) {
      const img = new Image();
      img.onload = () => { ctx.drawImage(img, tx - r, ty - r, r * 2, r * 2); drawTokenLabel(t, tx, ty, r, cs); };
      img.onerror = () => { drawTokenCircle(t, tx, ty, r, cs); };
      img.src = t.image;
    } else {
      drawTokenCircle(t, tx, ty, r, cs);
    }

    // HP bar
    if (t.hp !== undefined && t.max_hp) {
      const barW = cs * 0.8;
      const barH = 4;
      const barX = tx - barW / 2;
      const barY = ty - r - 10;
      const pct = Math.max(0, t.hp / t.max_hp);
      ctx.fillStyle = '#333';
      ctx.fillRect(barX, barY, barW, barH);
      ctx.fillStyle = pct > 0.5 ? '#27ae60' : pct > 0.25 ? '#f39c12' : '#e74c3c';
      ctx.fillRect(barX, barY, barW * pct, barH);
    }

    // Turn indicator
    if (state.combat_active && state.turn === t.id) {
      ctx.strokeStyle = '#f1c40f';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(tx, ty, r + 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Reset alpha
    ctx.globalAlpha = 1;
  });

  // Sound Zones
  (state.sound_zones || []).forEach(zone => {
    const grd = ctx.createRadialGradient(
      zone.x * cs + cs/2, zone.y * cs + cs/2, 0,
      zone.x * cs + cs/2, zone.y * cs + cs/2, zone.radius * cs
    );
    grd.addColorStop(0, 'rgba(155, 89, 182, 0.2)');
    grd.addColorStop(1, 'transparent');
    ctx.fillStyle = grd;
    ctx.beginPath();
    ctx.arc(zone.x * cs + cs/2, zone.y * cs + cs/2, zone.radius * cs, 0, Math.PI * 2);
    ctx.fill();

    // Speaker icon
    ctx.fillStyle = 'rgba(155, 89, 182, 0.8)';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('🔊', zone.x * cs + cs/2, zone.y * cs + cs/2 + 5);
  });

  // Difficult Terrain
  (state.difficult_terrain || []).forEach(([tx, ty]) => {
    ctx.fillStyle = 'rgba(139, 69, 19, 0.3)';
    ctx.fillRect(tx * cs, ty * cs, cs, cs);
    // Hatching pattern
    ctx.strokeStyle = 'rgba(139, 69, 19, 0.5)';
    ctx.lineWidth = 1;
    for (let i = 0; i < cs; i += 6) {
      ctx.beginPath();
      ctx.moveTo(tx * cs + i, ty * cs);
      ctx.lineTo(tx * cs, ty * cs + i);
      ctx.stroke();
    }
  });

  // Walls
  state.walls.forEach(w => {
    ctx.strokeStyle = w.type === 'door' ? '#8B4513' : '#666';
    ctx.lineWidth = w.type === 'door' ? 4 : 3;
    ctx.beginPath();
    ctx.moveTo(w.x1 * cs + cs/2, w.y1 * cs + cs/2);
    ctx.lineTo(w.x2 * cs + cs/2, w.y2 * cs + cs/2);
    ctx.stroke();

    // Door indicator
    if (w.type === 'door') {
      const mx = (w.x1 + w.x2) / 2 * cs + cs/2;
      const my = (w.y1 + w.y2) / 2 * cs + cs/2;
      ctx.fillStyle = w.open ? '#27ae60' : '#c0392b';
      ctx.beginPath();
      ctx.arc(mx, my, 6, 0, Math.PI * 2);
      ctx.fill();
    }
  });

  // Measurement: Template
  if (templateCells.length > 0) {
    ctx.fillStyle = 'rgba(231, 76, 60, 0.3)';
    templateCells.forEach(([cx, cy]) => {
      ctx.fillRect(cx * cs, cy * cs, cs, cs);
    });
    ctx.strokeStyle = 'rgba(231, 76, 60, 0.8)';
    ctx.lineWidth = 2;
    templateCells.forEach(([cx, cy]) => {
      ctx.strokeRect(cx * cs, cy * cs, cs, cs);
    });
  }

  // Measurement: Ruler
  if (rulerStart && rulerEnd) {
    const x1 = rulerStart.x * cs + cs / 2;
    const y1 = rulerStart.y * cs + cs / 2;
    const x2 = rulerEnd.x * cs + cs / 2;
    const y2 = rulerEnd.y * cs + cs / 2;

    ctx.strokeStyle = '#f1c40f';
    ctx.lineWidth = 3;
    ctx.setLineDash([8, 4]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Distance label
    const dx = Math.abs(rulerEnd.x - rulerStart.x);
    const dy = Math.abs(rulerEnd.y - rulerStart.y);
    const diag = Math.min(dx, dy);
    const straight = Math.max(dx, dy) - diag;
    const feet = Math.round((diag * 7.5) + (straight * 5));

    ctx.fillStyle = '#f1c40f';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${feet} ft.`, (x1 + x2) / 2, (y1 + y2) / 2 - 10);
  }

  // Visual Effects
  effects = effects.filter(e => {
    e.life -= EFFECT_DECAY;
    if (e.life <= 0) return false;
    const alpha = e.life / e.maxLife;
    ctx.globalAlpha = alpha;

    if (e.type === 'blood') {
      ctx.fillStyle = `rgba(180, 0, 0, ${alpha * 0.6})`;
      for (let i = 0; i < 5; i++) {
        const angle = (i / 5) * Math.PI * 2 + e.x;
        const dist = e.radius * 0.3 * (1 - alpha);
        ctx.beginPath();
        ctx.arc(e.x * cs + cs/2 + Math.cos(angle) * dist * cs, e.y * cs + cs/2 + Math.sin(angle) * dist * cs, 3 + Math.random() * 4, 0, Math.PI * 2);
        ctx.fill();
      }
    } else if (e.type === 'heal') {
      ctx.fillStyle = `rgba(46, 204, 113, ${alpha * 0.5})`;
      ctx.font = `bold ${16 + (1 - alpha) * 10}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText('+', e.x * cs + cs/2, e.y * cs + cs/2 - (1 - alpha) * 20);
    } else if (e.type === 'fire') {
      ctx.fillStyle = `rgba(255, 100, 0, ${alpha * 0.4})`;
      ctx.beginPath();
      ctx.arc(e.x * cs + cs/2, e.y * cs + cs/2, e.radius * cs * alpha, 0, Math.PI * 2);
      ctx.fill();
    } else if (e.type === 'lightning') {
      ctx.strokeStyle = `rgba(255, 255, 100, ${alpha})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(e.x * cs + cs/2, e.y * cs);
      ctx.lineTo(e.x * cs + cs/2 - 5, e.y * cs + cs/2);
      ctx.lineTo(e.x * cs + cs/2 + 5, e.y * cs + cs/2 + 5);
      ctx.lineTo(e.x * cs + cs/2, e.y * cs + cs);
      ctx.stroke();
    } else if (e.type === 'frost') {
      ctx.fillStyle = `rgba(150, 200, 255, ${alpha * 0.3})`;
      ctx.beginPath();
      ctx.arc(e.x * cs + cs/2, e.y * cs + cs/2, e.radius * cs * (1 - alpha) * 0.5, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.globalAlpha = 1;
    return true;
  });

  // Map Pins
  (state.pins || []).forEach(pin => {
    const px = pin.x * cs + cs / 2;
    const py = pin.y * cs;
    ctx.fillStyle = pin.color || '#f1c40f';
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px - 6, py - 16);
    ctx.lineTo(px + 6, py - 16);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.arc(px, py - 20, 8, 0, Math.PI * 2);
    ctx.fill();
    if (pin.label) {
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(pin.label, px, py - 32);
    }
  });

  // Weather overlay
  if (state.weather && state.weather !== 'none') {
    drawWeather(state.weather, state.weather_intensity || 1, canvas.width, canvas.height);
  }

  // Token Tooltip
  if (hoveredToken && !dragToken) {
    const t = hoveredToken;
    const tx = t.x * cs + cs / 2;
    const ty = t.y * cs;
    const tooltipW = 140;
    const tooltipH = 60;
    const tipX = tx - tooltipW / 2;
    const tipY = ty - tooltipH - 20;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
    ctx.beginPath();
    ctx.roundRect(tipX, tipY, tooltipW, tooltipH, 6);
    ctx.fill();
    ctx.strokeStyle = t.color || '#e74c3c';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(t.name, tx, tipY + 16);

    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#aaa';
    const hpText = t.hp !== undefined ? `HP: ${t.hp}/${t.max_hp || '?'}` : '';
    const acText = t.ac ? `AC: ${t.ac}` : '';
    ctx.fillText(`${hpText} ${acText}`, tx, tipY + 32);

    if (t.conditions && t.conditions.length > 0) {
      ctx.fillStyle = '#e74c3c';
      ctx.fillText(t.conditions.join(', '), tx, tipY + 48);
    }

    // Arrow pointing to token
    ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
    ctx.beginPath();
    ctx.moveTo(tx - 6, tipY + tooltipH);
    ctx.lineTo(tx + 6, tipY + tooltipH);
    ctx.lineTo(tx, tipY + tooltipH + 8);
    ctx.closePath();
    ctx.fill();
  }

  // Fog
  if (showFog) {
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    state.fog.forEach(f => {
      if (f.type === 'reveal') {
        ctx.save();
        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.arc(f.x * cs + cs/2, f.y * cs + cs/2, f.radius * cs, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    });
  }
}

function drawTokenCircle(t, tx, ty, r, cs) {
  const size = TOKEN_SIZES[t.size] || 1;
  const rotation = (t.rotation || 0) * Math.PI / 180;

  ctx.save();
  ctx.translate(tx, ty);
  ctx.rotate(rotation);

  if (size > 1) {
    // Larger tokens get a square with rounded corners
    const w = size * cs * 0.8;
    const h = size * cs * 0.8;
    ctx.fillStyle = t.color || '#e74c3c';
    ctx.beginPath();
    ctx.roundRect(tx - w/2, ty - h/2, w, h, 8);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.arc(tx, ty, r, 0, Math.PI * 2);
    ctx.fillStyle = t.color || '#e74c3c';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  ctx.restore();
  drawTokenLabel(t, tx, ty, r, cs);
}

function drawTokenLabel(t, tx, ty, r, cs) {
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${Math.max(10, cs * 0.3)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.fillText(t.name || '?', tx, ty + r + 14);
}

// --- Token Interaction ---
canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);

  // Ruler mode
  if (rulerMode) {
    rulerStart = { x: gx, y: gy };
    rulerEnd = null;
    canvas.style.cursor = 'crosshair';
    return;
  }

  // Wall/Door drawing mode
  if (wallMode) {
    if (!wallStart) {
      wallStart = { x: gx, y: gy };
      canvas.style.cursor = 'crosshair';
    } else {
      const wallType = wallMode === 'door' ? 'door' : 'stone';
      fetch('/api/wall/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x1: wallStart.x, y1: wallStart.y, x2: gx, y2: gy, wall_type: wallType })
      }).then(r => r.json()).then(wall => {
        state.walls.push(wall);
        render();
      });
      wallStart = null;
    }
    return;
  }

  // Template mode
  if (templateMode) {
    templateOrigin = { x: gx, y: gy };
    fetch('/api/area', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shape: templateMode, x: gx, y: gy, size: templateSize })
    }).then(r => r.json()).then(data => {
      templateCells = data.cells || [];
      render();
    });
    return;
  }

  // Token drag
  const token = Object.values(state.tokens).find(t => t.x === gx && t.y === gy);
  if (token) {
    dragToken = token;
    dragOffset = { x: mx - token.x * CELL_SIZE, y: my - token.y * CELL_SIZE };
    canvas.style.cursor = 'grabbing';
    e.stopPropagation();
  }
});

canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);

  if (rulerMode && rulerStart) {
    rulerEnd = { x: gx, y: gy };
    render();
    return;
  }

  // Hover detection for tooltips
  const hoverToken = Object.values(state.tokens).find(t => {
    const size = TOKEN_SIZES[t.size] || 1;
    return gx >= t.x && gx < t.x + size && gy >= t.y && gy < t.y + size;
  });
  if (hoverToken !== hoveredToken) {
    hoveredToken = hoverToken;
    render();
  }

  if (dragToken) {
    dragToken.x = Math.max(0, Math.min(state.map_size[0] - 1, gx));
    dragToken.y = Math.max(0, Math.min(state.map_size[1] - 1, gy));
    render();
  }
});

canvas.addEventListener('mousemove', (e) => {
  if (dragToken) {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / zoom;
    const my = (e.clientY - rect.top) / zoom;
    dragToken.x = Math.max(0, Math.min(state.map_size[0] - 1, Math.floor((mx - dragOffset.x + CELL_SIZE / 2) / CELL_SIZE)));
    dragToken.y = Math.max(0, Math.min(state.map_size[1] - 1, Math.floor((my - dragOffset.y + CELL_SIZE / 2) / CELL_SIZE)));
    render();
  }
});

canvas.addEventListener('mouseup', () => {
  if (dragToken) {
    fetch('/api/token/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token_id: dragToken.id, x: dragToken.x, y: dragToken.y })
    });
    dragToken = null;
    canvas.style.cursor = 'default';
  }
});

// Zoom
function setZoom(newZoom) {
  zoom = Math.max(0.25, Math.min(3, newZoom));
  document.getElementById('zoom-level').textContent = Math.round(zoom * 100) + '%';
  canvas.style.transform = `scale(${zoom})`;
}

// --- Weather Effects ---
let raindrops = [];
let snowflakes = [];

function drawWeather(type, intensity, w, h) {
  if (type === 'rain') {
    ctx.strokeStyle = 'rgba(100, 150, 255, 0.3)';
    ctx.lineWidth = 1;
    const count = intensity * 50;
    if (raindrops.length < count) {
      for (let i = raindrops.length; i < count; i++) {
        raindrops.push({ x: Math.random() * w, y: Math.random() * h, speed: 4 + Math.random() * 4 });
      }
    }
    raindrops.forEach(d => {
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x - 1, d.y + 8);
      ctx.stroke();
      d.y += d.speed;
      d.x -= 0.5;
      if (d.y > h) { d.y = -10; d.x = Math.random() * w; }
    });
  } else if (type === 'snow') {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    const count = intensity * 30;
    if (snowflakes.length < count) {
      for (let i = snowflakes.length; i < count; i++) {
        snowflakes.push({ x: Math.random() * w, y: Math.random() * h, speed: 0.5 + Math.random(), size: 1 + Math.random() * 2 });
      }
    }
    snowflakes.forEach(f => {
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.size, 0, Math.PI * 2);
      ctx.fill();
      f.y += f.speed;
      f.x += Math.sin(f.y * 0.02) * 0.5;
      if (f.y > h) { f.y = -5; f.x = Math.random() * w; }
    });
  } else if (type === 'fog') {
    ctx.fillStyle = `rgba(200, 200, 200, ${0.1 * intensity})`;
    ctx.fillRect(0, 0, w, h);
  } else if (type === 'night') {
    ctx.fillStyle = `rgba(0, 0, 30, ${0.2 * intensity})`;
    ctx.fillRect(0, 0, w, h);
  }
}

// --- Animation Loop ---
let animFrameId = null;
function animateLoop() {
  if (animFrameId) return;
  animFrameId = requestAnimationFrame(function loop() {
    render();
    if (Object.keys(tokenAnimations).length > 0) {
      animFrameId = requestAnimationFrame(loop);
    } else {
      animFrameId = null;
    }
  });
}

// --- Init ---
connect();
render();
