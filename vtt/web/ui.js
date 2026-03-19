// --- Dice Rolling ---
document.querySelectorAll('.dice').forEach(btn => {
  btn.addEventListener('click', () => {
    fetch('/api/roll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notation: btn.dataset.notation, roller: 'Player' })
    });
  });
});

// --- Chat ---
function addChat(sender, text, isRoll) {
  const log = document.getElementById('chat-log');
  const div = document.createElement('div');
  div.className = 'chat-msg' + (isRoll ? ' roll' : '');
  div.innerHTML = `<strong>${sender}:</strong> ${text}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

document.getElementById('chat-send').addEventListener('click', sendChat);
document.getElementById('chat-text').addEventListener('keypress', (e) => { if (e.key === 'Enter') sendChat(); });

function sendChat() {
  const input = document.getElementById('chat-text');
  const text = input.value.trim();
  if (!text) return;

  // Chat commands
  if (text.startsWith('/')) {
    handleChatCommand(text);
    input.value = '';
    return;
  }

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender: 'Player', text })
  });
  input.value = '';
}

function handleChatCommand(text) {
  const parts = text.split(' ');
  const cmd = parts[0].toLowerCase();

  switch (cmd) {
    case '/roll':
    case '/r':
      const notation = parts.slice(1).join(' ') || '1d20';
      fetch('/api/roll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notation, roller: 'Player' })
      });
      break;
    case '/w':
    case '/whisper':
      const target = parts[1];
      const msg = parts.slice(2).join(' ');
      if (target && msg) {
        addChat(`Whisper → ${target}`, msg);
      }
      break;
    case '/emote':
    case '/me':
      const action = parts.slice(1).join(' ');
      if (action) {
        fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sender: 'Player', text: `*${action}*` })
        });
      }
      break;
    case '/clear':
      document.getElementById('chat-log').innerHTML = '';
      break;
    case '/help':
      addChat('System', 'Commands: /roll [dice], /w [target] [msg], /me [action], /clear, /help');
      break;
    default:
      addChat('System', `Unknown command: ${cmd}. Type /help for commands.`);
  }
}

// --- Token Modal ---
document.getElementById('btn-add-token').addEventListener('click', () => document.getElementById('token-modal').classList.remove('hidden'));
document.getElementById('token-cancel').addEventListener('click', () => document.getElementById('token-modal').classList.add('hidden'));
document.getElementById('token-add').addEventListener('click', () => {
  fetch('/api/token/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: document.getElementById('token-name').value,
      x: parseInt(document.getElementById('token-x').value),
      y: parseInt(document.getElementById('token-y').value),
      color: document.getElementById('token-color').value,
      hp: parseInt(document.getElementById('token-hp')?.value || 10),
      ac: parseInt(document.getElementById('token-ac')?.value || 10),
      size: document.getElementById('token-size')?.value || 'medium',
      hidden: document.getElementById('token-hidden')?.checked || false
    })
  });
  document.getElementById('token-modal').classList.add('hidden');
});

// --- Toolbar ---
document.getElementById('btn-grid').addEventListener('click', () => { showGrid = !showGrid; document.getElementById('btn-grid').classList.toggle('active'); render(); });
document.getElementById('btn-fog').addEventListener('click', () => { showFog = !showFog; document.getElementById('btn-fog').classList.toggle('active'); render(); });
document.getElementById('btn-tokens-layer')?.addEventListener('click', () => { showTokens = !showTokens; document.getElementById('btn-tokens-layer').classList.toggle('active'); render(); });
document.getElementById('btn-walls-layer')?.addEventListener('click', () => { showWalls = !showWalls; document.getElementById('btn-walls-layer').classList.toggle('active'); render(); });
document.getElementById('btn-effects-layer')?.addEventListener('click', () => { showEffects = !showEffects; document.getElementById('btn-effects-layer').classList.toggle('active'); render(); });
document.getElementById('btn-zoom-in').addEventListener('click', () => setZoom(zoom + 0.25));
document.getElementById('btn-zoom-out').addEventListener('click', () => setZoom(zoom - 0.25));

// --- Token Size Rendering ---
const TOKEN_SIZES = { tiny: 0.5, small: 1, medium: 1, large: 2, huge: 3, gargantuan: 4 };

// --- Character Sheet ---
let selectedToken = null;

canvas.addEventListener('click', (e) => {
  if (rulerMode || templateMode || dragToken) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);

  const token = Object.values(state.tokens).find(t => {
    const size = TOKEN_SIZES[t.size] || 1;
    return gx >= t.x && gx < t.x + size && gy >= t.y && gy < t.y + size;
  });

  if (token) {
    selectedToken = token;
    renderCharSheet(token);
  } else {
    selectedToken = null;
    document.getElementById('char-sheet').innerHTML = '<div class="char-empty">Click a token to view details</div>';
  }
});

function renderCharSheet(t) {
  const sheet = document.getElementById('char-sheet');
  const hpPct = t.max_hp ? Math.max(0, (t.hp / t.max_hp) * 100) : 100;
  const hpColor = hpPct > 50 ? '#27ae60' : hpPct > 25 ? '#f39c12' : '#e74c3c';
  const conditions = (t.conditions || []).map(c => `<span class="char-condition" onclick="removeCondition('${t.id}','${c}')" title="Click to remove">${c} ✕</span>`).join('');

  sheet.innerHTML = `
    <div class="char-name" style="color:${t.color}">${t.name}</div>
    <div class="char-size">${(t.size || 'medium').charAt(0).toUpperCase() + (t.size || 'medium').slice(1)} · AC ${t.ac || '?'}</div>
    <div class="char-hp">
      <span>${t.hp || 0}/${t.max_hp || '?'}</span>
      <div class="char-hp-bar"><div class="char-hp-fill" style="width:${hpPct}%;background:${hpColor}"></div></div>
    </div>
    <div class="char-conditions">${conditions}</div>
    <div style="margin-top:8px;display:flex;gap:4px;">
      <button onclick="quickDamage('${t.id}',5)" style="flex:1;background:#c0392b;border:none;color:white;padding:4px;border-radius:4px;cursor:pointer;font-size:11px;">-5 HP</button>
      <button onclick="quickDamage('${t.id}',1)" style="flex:1;background:#e67e22;border:none;color:white;padding:4px;border-radius:4px;cursor:pointer;font-size:11px;">-1 HP</button>
      <button onclick="quickHeal('${t.id}',5)" style="flex:1;background:#27ae60;border:none;color:white;padding:4px;border-radius:4px;cursor:pointer;font-size:11px;">+5 HP</button>
    </div>
    ${t.concentration ? `<div style="margin-top:6px;background:#8e44ad22;padding:4px 6px;border-radius:4px;font-size:11px;border:1px solid #8e44ad;">🔮 Concentrating: ${escapeHtml(t.concentration.spell || '?')} (DC ${t.concentration.dc || 10}) <button onclick="breakConcentration('${t.id}')" style="background:none;border:none;color:#e74c3c;cursor:pointer;">✕</button></div>` : ''}
    ${t.hp !== undefined && t.hp <= 0 ? `<div style="margin-top:6px;background:#c0392b22;padding:4px 6px;border-radius:4px;font-size:11px;border:1px solid #c0392b;">💀 Death Saves: ${'✅'.repeat(t.death_saves?.successes || 0)}${'⬜'.repeat(3 - (t.death_saves?.successes || 0))} | ${'❌'.repeat(t.death_saves?.failures || 0)}${'⬜'.repeat(3 - (t.death_saves?.failures || 0))}<div style="display:flex;gap:4px;margin-top:4px;"><button onclick="deathSave('${t.id}',true)" style="flex:1;background:#27ae60;border:none;color:white;padding:2px;border-radius:3px;cursor:pointer;font-size:10px;">Success</button><button onclick="deathSave('${t.id}',false)" style="flex:1;background:#c0392b;border:none;color:white;padding:2px;border-radius:3px;cursor:pointer;font-size:10px;">Failure</button></div></div>` : ''}
    ${t.notes ? `<div style="margin-top:6px;background:#1a1a2e;padding:6px;border-radius:4px;font-size:11px;color:#aaa;max-height:60px;overflow-y:auto;">📝 ${escapeHtml(t.notes)}</div>` : ''}
    <div style="margin-top:6px;">
      <button onclick="editNotes('${t.id}')" style="flex:1;background:#2d2d44;border:1px solid #444;color:#e0e0e0;padding:3px;border-radius:4px;cursor:pointer;font-size:10px;width:100%;">📝 Edit Notes</button>
    </div>
    <div style="margin-top:6px;">
      <select onchange="addCondition('${t.id}',this.value);this.value='';" style="width:100%;background:#2d2d44;border:1px solid #444;color:#e0e0e0;padding:3px;border-radius:4px;font-size:11px;">
        <option value="">+ Add Condition</option>
        <option value="blinded">Blinded</option>
        <option value="charmed">Charmed</option>
        <option value="deafened">Deafened</option>
        <option value="frightened">Frightened</option>
        <option value="grappled">Grappled</option>
        <option value="incapacitated">Incapacitated</option>
        <option value="invisible">Invisible</option>
        <option value="paralyzed">Paralyzed</option>
        <option value="petrified">Petrified</option>
        <option value="poisoned">Poisoned</option>
        <option value="prone">Prone</option>
        <option value="restrained">Restrained</option>
        <option value="stunned">Stunned</option>
        <option value="unconscious">Unconscious</option>
      </select>
    </div>
  `;
}

window.quickDamage = (id, amount) => {
  fetch('/api/combat/damage', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_id: id, amount }) });
};
window.quickHeal = (id, amount) => {
  fetch('/api/combat/heal', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_id: id, amount }) });
};
window.addCondition = (id, condition) => {
  if (!condition) return;
  fetch('/api/combat/condition/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token_id: id, condition })
  }).then(() => {
    // Refresh state
    fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); if (selectedToken) renderCharSheet(state.tokens[selectedToken.id] || selectedToken); });
  });
};
window.breakConcentration = (id) => {
  fetch('/api/combat/concentration/break', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_id: id }) })
    .then(() => fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); if (selectedToken) renderCharSheet(state.tokens[selectedToken.id] || selectedToken); }));
};

window.deathSave = (id, success) => {
  fetch('/api/combat/death-save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_id: id, success }) })
    .then(r => r.json()).then(data => {
      if (data.stabilized) addChat('System', `${state.tokens[id]?.name || 'Token'} is stabilized!`);
      if (data.dead) addChat('System', `${state.tokens[id]?.name || 'Token'} has died!`);
      fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); if (selectedToken) renderCharSheet(state.tokens[selectedToken.id] || selectedToken); });
    });
};

window.editNotes = (id) => {
  const token = state.tokens[id];
  if (!token) return;
  const notes = prompt('Token notes:', token.notes || '');
  if (notes !== null) {
    fetch('/api/token/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token_id: id, notes })
    }).then(() => {
      token.notes = notes;
      renderCharSheet(token);
    });
  }
};

window.removeCondition = (id, condition) => {
  fetch('/api/combat/condition/remove', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token_id: id, condition })
  }).then(() => {
    fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); if (selectedToken) renderCharSheet(state.tokens[selectedToken.id] || selectedToken); });
  });
};

// --- Token List ---
function updateTokenList() {
  const list = document.getElementById('token-list');
  list.innerHTML = '';
  Object.values(state.tokens).forEach(t => {
    const div = document.createElement('div');
    div.className = 'token-item';
    const hpText = t.hp !== undefined ? ` [${t.hp}/${t.max_hp || t.hp}]` : '';
    div.innerHTML = `<span style="color:${t.color}">●</span> ${t.name}${hpText} (${t.x},${t.y}) <button onclick="removeToken('${t.id}')">✕</button>`;
    list.appendChild(div);
  });
}

window.removeToken = (id) => {
  fetch('/api/token/remove', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
};

// --- Initiative Tracker ---
function updateInitiative() {
  const panel = document.getElementById('initiative-panel');
  if (!panel) return;
  panel.innerHTML = '';
  if (!state.combat_active) {
    panel.innerHTML = '<div class="init-empty">No active combat</div>';
    return;
  }
  panel.innerHTML = `<div class="init-header">Round ${state.round}</div>`;
  state.initiative.forEach((tid, i) => {
    const t = state.tokens[tid];
    if (!t) return;
    const div = document.createElement('div');
    div.className = 'init-item' + (state.turn === tid ? ' active' : '');
    div.innerHTML = `${i + 1}. ${t.name} (${t.hp}/${t.max_hp || '?'})`;
    panel.appendChild(div);
  });
}

// --- Combat Buttons ---
document.getElementById('btn-start-combat')?.addEventListener('click', () => {
  const tokenIds = Object.keys(state.tokens);
  if (tokenIds.length < 2) { addChat('System', 'Need at least 2 tokens for combat'); return; }
  fetch('/api/combat/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_ids: tokenIds }) });
});

document.getElementById('btn-end-turn')?.addEventListener('click', () => {
  fetch('/api/combat/end-turn', { method: 'POST' });
});

document.getElementById('btn-auto-init')?.addEventListener('click', () => {
  const tokenIds = Object.keys(state.tokens);
  if (tokenIds.length < 2) { addChat('System', 'Need at least 2 tokens'); return; }
  fetch('/api/combat/roll-initiative', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_ids: tokenIds }) })
    .then(r => r.json()).then(data => {
      const rolls = Object.entries(data.rolls).map(([id, r]) => `${r.name}: ${r.roll}+${r.modifier}=${r.total}`).join(', ');
      addChat('Initiative', `🎲 ${rolls}`);
      updateInitiative();
    });
});

document.getElementById('btn-reroll-init')?.addEventListener('click', () => {
  const tokenIds = state.initiative.length > 0 ? state.initiative : Object.keys(state.tokens);
  if (tokenIds.length < 2) { addChat('System', 'Need at least 2 tokens'); return; }
  fetch('/api/combat/roll-initiative', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_ids: tokenIds }) })
    .then(r => r.json()).then(data => {
      const rolls = Object.entries(data.rolls).map(([id, r]) => `${r.name}: ${r.roll}+${r.modifier}=${r.total}`).join(', ');
      addChat('Initiative', `🔄 Reroll: ${rolls}`);
      updateInitiative();
    });
});

document.getElementById('btn-concentrate')?.addEventListener('click', () => {
  if (!selectedToken) { addChat('System', 'Select a token first'); return; }
  const spell = prompt('Spell name:', '');
  if (spell !== null) {
    const dc = parseInt(prompt('Concentration DC:', '10')) || 10;
    fetch('/api/combat/concentration', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token_id: selectedToken.id, spell, dc }) })
      .then(() => fetch('/api/state').then(r => r.json()).then(s => { state = s; renderCharSheet(state.tokens[selectedToken.id] || selectedToken); }));
  }
});

document.getElementById('btn-short-rest')?.addEventListener('click', () => {
  if (!confirm('Take a short rest? (All tokens)')) return;
  fetch('/api/combat/short-rest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .then(r => r.json()).then(() => { addChat('System', '😴 Short rest taken'); fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); updateTokenList(); }); });
});

document.getElementById('btn-long-rest')?.addEventListener('click', () => {
  if (!confirm('Take a long rest? (Full heal, reset all)')) return;
  fetch('/api/combat/long-rest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .then(r => r.json()).then(() => { addChat('System', '🛏️ Long rest taken — all HP restored!'); fetch('/api/state').then(r => r.json()).then(s => { state = s; render(); updateTokenList(); }); });
});

// --- Grid Size ---
document.getElementById('btn-grid-size')?.addEventListener('click', () => {
  document.getElementById('grid-width').value = state.map_size[0];
  document.getElementById('grid-height').value = state.map_size[1];
  document.getElementById('grid-modal').classList.remove('hidden');
});
document.getElementById('grid-cancel')?.addEventListener('click', () => document.getElementById('grid-modal').classList.add('hidden'));
document.getElementById('grid-apply')?.addEventListener('click', () => {
  const w = parseInt(document.getElementById('grid-width').value);
  const h = parseInt(document.getElementById('grid-height').value);
  fetch('/api/grid/size', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ width: w, height: h }) })
    .then(r => r.json()).then(data => {
      state.map_size = [data.width, data.height];
      render();
      document.getElementById('grid-modal').classList.add('hidden');
    });
});

// --- Export Map ---
document.getElementById('btn-export')?.addEventListener('click', () => {
  const link = document.createElement('a');
  link.download = `vtt-map-${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
  addChat('System', 'Map exported as PNG!');
});

// --- Map Management ---
document.getElementById('btn-save-map')?.addEventListener('click', () => {
  const name = prompt('Map name:', state.current_map || 'default');
  if (name) {
    fetch('/api/map/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
      .then(r => r.json()).then(d => addChat('System', `Map "${d.name}" saved!`));
  }
});

document.getElementById('btn-switch-map')?.addEventListener('click', async () => {
  const resp = await fetch('/api/map/list');
  const data = await resp.json();
  const list = document.getElementById('map-list');
  list.innerHTML = '';
  if (data.maps.length === 0) {
    list.innerHTML = '<div style="color:#888;padding:12px;">No saved maps. Save your current map first.</div>';
  }
  data.maps.forEach(m => {
    const div = document.createElement('div');
    div.style.cssText = 'padding:8px;margin:4px 0;background:#2d2d44;border-radius:4px;cursor:pointer;display:flex;align-items:center;gap:8px;';
    div.style.border = m.name === data.current ? '2px solid #3498db' : '2px solid #444';
    div.innerHTML = `<span>${m.name === data.current ? '📍' : '🗺️'}</span><span>${m.name}</span>`;
    div.addEventListener('click', () => {
      fetch('/api/map/switch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: m.name }) })
        .then(r => r.json()).then(() => {
          addChat('System', `Switched to map "${m.name}"`);
          document.getElementById('map-modal').classList.add('hidden');
        });
    });
    list.appendChild(div);
  });
  document.getElementById('map-modal').classList.remove('hidden');
});
document.getElementById('map-close')?.addEventListener('click', () => document.getElementById('map-modal').classList.add('hidden'));

// --- Spell Effects ---
let spellMode = null;

document.querySelectorAll('.spell-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const effect = btn.dataset.effect;
    if (spellMode === effect) {
      spellMode = null;
      btn.classList.remove('active');
    } else {
      spellMode = effect;
      document.querySelectorAll('.spell-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    canvas.style.cursor = spellMode ? 'crosshair' : 'default';
  });
});

// Spell effect click handler
canvas.addEventListener('click', (e) => {
  if (!spellMode) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);

  const colors = { fire: '#ff6600', lightning: '#ffff66', frost: '#96c8ff', acid: '#64c800', thunder: '#c8c8ff', radiant: '#ffffc8', heal: '#2ecc71' };
  const radii = { fire: 4, lightning: 1, frost: 3, acid: 2, thunder: 3, radiant: 2, heal: 1 };

  effects.push({
    type: spellMode,
    x: gx, y: gy,
    radius: radii[spellMode] || 2,
    color: colors[spellMode] || '#fff',
    life: 1, maxLife: 1
  });

  // Broadcast to other clients
  fetch('/api/effect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: spellMode, x: gx, y: gy, radius: radii[spellMode] || 2 })
  });

  animateLoop();
});

// Handle incoming effects
const origHandleMessage = handleMessage;
// Effects are handled in the WebSocket message handler

// --- Rules Reference ---
document.getElementById('btn-rules')?.addEventListener('click', async () => {
  const resp = await fetch('/api/rules/list');
  const files = await resp.json();
  const list = document.getElementById('rules-file-list');
  list.innerHTML = '';
  files.forEach(f => {
    const btn = document.createElement('button');
    btn.textContent = f.name.replace('.md', '').replace(/-/g, ' ');
    btn.style.cssText = 'background:#2d2d44;border:1px solid #444;color:#e0e0e0;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;';
    btn.addEventListener('click', async () => {
      const resp = await fetch(`/api/rules/get/${f.name}`);
      const data = await resp.json();
      document.getElementById('rules-content').innerHTML = `<pre style="white-space:pre-wrap;word-wrap:break-word;">${escapeHtml(data.content)}</pre>`;
    });
    list.appendChild(btn);
  });
  document.getElementById('rules-content').innerHTML = '<div style="color:#888;">Click a reference file or search below</div>';
  document.getElementById('rules-modal').classList.remove('hidden');
});
document.getElementById('rules-close')?.addEventListener('click', () => document.getElementById('rules-modal').classList.add('hidden'));

document.getElementById('rules-search-btn')?.addEventListener('click', searchRules);
document.getElementById('rules-search')?.addEventListener('keypress', (e) => { if (e.key === 'Enter') searchRules(); });

async function searchRules() {
  const query = document.getElementById('rules-search').value.trim();
  if (!query) return;
  const resp = await fetch('/api/rules/search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) });
  const results = await resp.json();
  const content = document.getElementById('rules-content');
  if (results.length === 0) {
    content.innerHTML = '<div style="color:#888;">No results found</div>';
    return;
  }
  content.innerHTML = results.map(r => `
    <div style="margin-bottom:12px;">
      <div style="color:#3498db;font-weight:bold;margin-bottom:4px;">📄 ${r.file}</div>
      ${r.matches.map(m => `<div style="background:#1a1a2e;padding:8px;border-radius:4px;margin-bottom:4px;white-space:pre-wrap;">${escapeHtml(m)}</div>`).join('')}
    </div>
  `).join('');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// --- Party Tracker ---
const RESOURCE_ICONS = { gold: '🪙', silver: '🪙', copper: '🪙', rations: '🍖', water: '💧', torches: '🔥', arrows: '🏹', bolts: '🏹' };

document.getElementById('btn-party')?.addEventListener('click', async () => {
  const resp = await fetch('/api/party/resources');
  const resources = await resp.json();
  const grid = document.getElementById('party-resources');
  grid.innerHTML = '';
  Object.entries(resources).forEach(([key, val]) => {
    const icon = RESOURCE_ICONS[key] || '📦';
    grid.innerHTML += `
      <div style="background:#2d2d44;padding:8px;border-radius:6px;text-align:center;">
        <div style="font-size:20px;">${icon}</div>
        <div style="font-size:12px;color:#888;">${key}</div>
        <div style="display:flex;align-items:center;justify-content:center;gap:4px;margin-top:4px;">
          <button onclick="adjustResource('${key}',-1)" style="background:#c0392b;border:none;color:white;width:24px;height:24px;border-radius:4px;cursor:pointer;">-</button>
          <span style="font-size:16px;font-weight:bold;min-width:30px;" id="res-${key}">${val}</span>
          <button onclick="adjustResource('${key}',1)" style="background:#27ae60;border:none;color:white;width:24px;height:24px;border-radius:4px;cursor:pointer;">+</button>
        </div>
      </div>
    `;
  });
  document.getElementById('party-modal').classList.remove('hidden');
});
document.getElementById('party-close')?.addEventListener('click', () => document.getElementById('party-modal').classList.add('hidden'));

window.adjustResource = async (resource, delta) => {
  const el = document.getElementById(`res-${resource}`);
  const current = parseInt(el.textContent);
  const newVal = Math.max(0, current + delta);
  el.textContent = newVal;
  await fetch('/api/party/resource', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resource, amount: newVal }) });
};

// --- Calendar ---
const MONTH_NAMES = ["Hammer", "Alturiak", "Ches", "Tarsakh", "Mirtul", "Kythorn", "Eleasis", "Eleint", "Marpenoth", "Uktar", "Nightal", "Nightal"];

document.getElementById('btn-calendar')?.addEventListener('click', async () => {
  await updateCalendarDisplay();
  document.getElementById('calendar-modal').classList.remove('hidden');
});
document.getElementById('calendar-close')?.addEventListener('click', () => document.getElementById('calendar-modal').classList.add('hidden'));

document.querySelectorAll('.cal-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const hours = parseInt(btn.dataset.hours);
    await fetch('/api/calendar/advance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hours }) });
    await updateCalendarDisplay();
  });
});

async function updateCalendarDisplay() {
  const resp = await fetch('/api/calendar');
  const cal = await resp.json();
  const monthName = MONTH_NAMES[cal.month - 1] || 'Unknown';
  const timeStr = `${String(cal.hour).padStart(2, '0')}:${String(cal.minute).padStart(2, '0')}`;
  const seasonIcon = { winter: '❄️', spring: '🌸', summer: '☀️', autumn: '🍂' }[cal.season] || '';
  document.getElementById('calendar-display').innerHTML = `
    <div>${seasonIcon} ${monthName} ${cal.day}, ${cal.year} DR</div>
    <div style="font-size:14px;color:#888;margin-top:4px;">${timeStr} · ${cal.season}</div>
  `;
}

// --- Encounter Builder ---
document.getElementById('btn-encounter')?.addEventListener('click', () => {
  document.getElementById('encounter-modal').classList.remove('hidden');
});
document.getElementById('enc-close')?.addEventListener('click', () => {
  document.getElementById('encounter-modal').classList.add('hidden');
});
document.getElementById('enc-calculate')?.addEventListener('click', async () => {
  const level = parseInt(document.getElementById('enc-party-level').value);
  const size = parseInt(document.getElementById('enc-party-size').value);
  const crs = document.getElementById('enc-monster-crs').value.split(',').map(s => s.trim());

  const xpResp = await fetch('/api/encounter/xp', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cr_list: crs, num_players: size }) });
  const xpData = await xpResp.json();

  const diffResp = await fetch('/api/encounter/difficulty', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ party_level: level, party_size: size, total_xp: xpData.adjusted_xp }) });
  const diffData = await diffResp.json();

  document.getElementById('enc-result').innerHTML = `
    <div style="font-size:18px;margin-bottom:8px;">${diffData.difficulty}</div>
    <div>Base XP: ${xpData.base_xp.toLocaleString()}</div>
    <div>Adjusted XP: ${xpData.adjusted_xp.toLocaleString()} (${xpData.multiplier}x multiplier)</div>
    <div>XP per player: ${xpData.xp_per_player.toLocaleString()}</div>
    <div>Monsters: ${xpData.num_monsters}</div>
  `;
});

// --- Loot Generator ---
document.getElementById('btn-loot')?.addEventListener('click', () => {
  document.getElementById('loot-modal').classList.remove('hidden');
});
document.getElementById('loot-close')?.addEventListener('click', () => {
  document.getElementById('loot-modal').classList.add('hidden');
});
document.getElementById('loot-generate')?.addEventListener('click', async () => {
  const cr = document.getElementById('loot-cr').value;
  const count = parseInt(document.getElementById('loot-count').value);
  const resp = await fetch('/api/loot/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cr, num_items: count }) });
  const data = await resp.json();
  const items = data.items.map(i => `• ${i}`).join('<br>');
  document.getElementById('loot-result').innerHTML = `
    <div style="font-size:16px;margin-bottom:8px;">💰 Loot (CR ${cr})</div>
    <div>🪙 ${data.coins.gp} gp, ${data.coins.sp} sp, ${data.coins.cp} cp</div>
    <div style="margin-top:8px;">${items}</div>
  `;
  addChat('Loot', `💰 ${data.coins.gp}gp ${data.coins.sp}sp ${data.coins.cp}cp | ${data.items.join(', ')}`);
});

// --- Weather ---
document.querySelectorAll('.weather-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const weather = btn.dataset.weather;
    document.querySelectorAll('.weather-btn').forEach(b => b.classList.remove('active'));
    if (weather !== 'none') btn.classList.add('active');
    fetch('/api/weather/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: weather, intensity: 1 })
    }).then(r => r.json()).then(data => {
      state.weather = data.weather;
      state.weather_intensity = data.intensity;
      raindrops = [];
      snowflakes = [];
      render();
    });
  });
});

// --- Map Pins ---
let pinMode = false;

document.getElementById('btn-pin')?.addEventListener('click', () => {
  pinMode = !pinMode;
  document.getElementById('btn-pin').classList.toggle('active', pinMode);
  canvas.style.cursor = pinMode ? 'crosshair' : 'default';
});

// Pin click handler (in renderer mousedown)
const origMousedown = canvas.onmousedown;
canvas.addEventListener('mousedown', (e) => {
  if (!pinMode) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);
  const label = prompt('Pin label (optional):');
  fetch('/api/pin/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x: gx, y: gy, label: label || '', color: '#f1c40f' })
  }).then(r => r.json()).then(pin => {
    if (!state.pins) state.pins = [];
    state.pins.push(pin);
    render();
  });
});

// --- Campaign Save/Load ---
let autoSaveInterval = null;

document.getElementById('btn-save')?.addEventListener('click', () => {
  const name = prompt('Campaign name:', 'default');
  if (name) {
    fetch('/api/campaign/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    }).then(r => r.json()).then(data => {
      addChat('System', `Campaign "${data.name}" saved!`);
      startAutoSave(data.name);
    });
  }
});

document.getElementById('btn-load')?.addEventListener('click', async () => {
  const resp = await fetch('/api/campaign/list');
  const campaigns = await resp.json();
  if (campaigns.length === 0) {
    addChat('System', 'No saved campaigns found.');
    return;
  }
  const names = campaigns.map(c => c.name).join(', ');
  const name = prompt(`Load campaign (${names}):`, campaigns[0].name);
  if (name) {
    fetch('/api/campaign/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    }).then(r => r.json()).then(data => {
      if (data.error) {
        addChat('System', `Error: ${data.error}`);
      } else {
        addChat('System', `Campaign "${data.name}" loaded!`);
        startAutoSave(data.name);
      }
    });
  }
});

function startAutoSave(name) {
  if (autoSaveInterval) clearInterval(autoSaveInterval);
  autoSaveInterval = setInterval(() => {
    fetch('/api/campaign/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
  }, 60000); // Auto-save every 60 seconds
}

// --- Sound Zones ---
let soundMode = false;

document.getElementById('btn-sound')?.addEventListener('click', () => {
  soundMode = !soundMode;
  document.getElementById('btn-sound').classList.toggle('active', soundMode);
  canvas.style.cursor = soundMode ? 'crosshair' : 'default';
});

canvas.addEventListener('click', (e) => {
  if (!soundMode) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);
  const sound = prompt('Sound description (e.g., "tavern chatter", "dripping water"):');
  if (sound) {
    fetch('/api/sound/zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x: gx, y: gy, radius: 5, sound })
    }).then(r => r.json()).then(zone => {
      if (!state.sound_zones) state.sound_zones = [];
      state.sound_zones.push(zone);
      render();
    });
  }
});

// --- Symmetry ---
document.querySelectorAll('.symmetry-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const mode = btn.dataset.mode;
    if (symmetryMode === mode) {
      symmetryMode = null;
      btn.classList.remove('active');
    } else {
      symmetryMode = mode;
      document.querySelectorAll('.symmetry-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    render();
  });
});

// --- Difficult Terrain ---
let terrainMode = false;

document.getElementById('btn-terrain')?.addEventListener('click', () => {
  terrainMode = !terrainMode;
  document.getElementById('btn-terrain').classList.toggle('active', terrainMode);
  canvas.style.cursor = terrainMode ? 'crosshair' : 'default';
});

canvas.addEventListener('click', (e) => {
  if (!terrainMode) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);
  fetch('/api/terrain/set', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x: gx, y: gy, difficult: true })
  }).then(r => r.json()).then(data => {
    if (!state.difficult_terrain) state.difficult_terrain = [];
    state.difficult_terrain.push([gx, gy]);
    render();
  });
});

// --- Token Rotation ---
canvas.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / zoom;
  const my = (e.clientY - rect.top) / zoom;
  const gx = Math.floor(mx / CELL_SIZE);
  const gy = Math.floor(my / CELL_SIZE);
  const token = Object.values(state.tokens).find(t => t.x === gx && t.y === gy);
  if (token) {
    fetch('/api/token/rotate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token_id: token.id, degrees: e.shiftKey ? -90 : 90 })
    }).then(r => r.json()).then(data => {
      token.rotation = data.rotation;
      render();
    });
  }
});

// --- Wall Drawing ---
document.getElementById('btn-wall')?.addEventListener('click', () => {
  wallMode = wallMode === 'wall' ? null : 'wall';
  wallStart = null;
  rulerMode = false; templateMode = null;
  document.getElementById('btn-wall').classList.toggle('active', wallMode === 'wall');
  document.getElementById('btn-door')?.classList.remove('active');
  document.getElementById('btn-ruler')?.classList.remove('active');
  document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
  canvas.style.cursor = wallMode ? 'crosshair' : 'default';
});

document.getElementById('btn-door')?.addEventListener('click', () => {
  wallMode = wallMode === 'door' ? null : 'door';
  wallStart = null;
  rulerMode = false; templateMode = null;
  document.getElementById('btn-door').classList.toggle('active', wallMode === 'door');
  document.getElementById('btn-wall')?.classList.remove('active');
  document.getElementById('btn-ruler')?.classList.remove('active');
  document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
  canvas.style.cursor = wallMode ? 'crosshair' : 'default';
});

// --- Measurement Tools ---
document.getElementById('btn-ruler')?.addEventListener('click', () => {
  rulerMode = !rulerMode;
  templateMode = null;
  templateCells = [];
  document.getElementById('btn-ruler').classList.toggle('active', rulerMode);
  document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
  canvas.style.cursor = rulerMode ? 'crosshair' : 'default';
  if (!rulerMode) { rulerStart = null; rulerEnd = null; render(); }
});

document.querySelectorAll('.template-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const shape = btn.dataset.shape;
    if (templateMode === shape) {
      templateMode = null;
      templateCells = [];
      btn.classList.remove('active');
    } else {
      templateMode = shape;
      rulerMode = false;
      document.getElementById('btn-ruler').classList.remove('active');
      document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    canvas.style.cursor = templateMode ? 'crosshair' : 'default';
    render();
  });
});

// Template size with scroll wheel when in template mode
canvas.addEventListener('wheel', (e) => {
  if (templateMode && templateOrigin) {
    e.preventDefault();
    templateSize = Math.max(1, Math.min(15, templateSize + (e.deltaY > 0 ? -1 : 1)));
    fetch('/api/area', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shape: templateMode, x: templateOrigin.x, y: templateOrigin.y, size: templateSize })
    }).then(r => r.json()).then(data => {
      templateCells = data.cells || [];
      render();
    });
  }
});

// --- Keyboard Shortcuts ---
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  switch (e.key.toLowerCase()) {
    case 'r': document.getElementById('btn-ruler')?.click(); break;
    case 'g': document.getElementById('btn-grid')?.click(); break;
    case 'f': document.getElementById('btn-fog')?.click(); break;
    case 's': if (e.ctrlKey) { e.preventDefault(); document.getElementById('btn-save')?.click(); } break;
    case 'z': if (e.ctrlKey && !e.shiftKey) { e.preventDefault(); fetch('/api/undo', { method: 'POST' }).then(r => r.json()).then(d => { if (d.success) addChat('System', `Undo: ${d.action}`); }); }
              if (e.ctrlKey && e.shiftKey) { e.preventDefault(); fetch('/api/redo', { method: 'POST' }).then(r => r.json()).then(d => { if (d.success) addChat('System', 'Redo'); }); } break;
    case 'c': if (e.ctrlKey && selectedToken) { e.preventDefault(); clipboard = {...selectedToken}; addChat('System', `Copied ${selectedToken.name}`); } break;
    case 'v': if (e.ctrlKey && clipboard) {
      e.preventDefault();
      fetch('/api/token/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: clipboard.name + ' (copy)', x: clipboard.x + 1, y: clipboard.y + 1, color: clipboard.color, hp: clipboard.hp, max_hp: clipboard.max_hp, ac: clipboard.ac, size: clipboard.size, image: clipboard.image })
      });
    } break;
    case 'delete':
    case 'backspace':
      if (selectedToken) {
        fetch('/api/token/remove', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: selectedToken.id }) });
        selectedToken = null;
        document.getElementById('char-sheet').innerHTML = '<div class="char-empty">Click a token to view details</div>';
      }
      break;
    case 'n': document.getElementById('btn-add-token')?.click(); break;
    case 'escape':
      rulerMode = false; templateMode = null; templateCells = []; rulerStart = null; rulerEnd = null;
      wallMode = null; wallStart = null;
      document.getElementById('btn-ruler')?.classList.remove('active');
      document.getElementById('btn-wall')?.classList.remove('active');
      document.getElementById('btn-door')?.classList.remove('active');
      document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
      canvas.style.cursor = 'default';
      render();
      break;
  }
});

// --- Map Background ---
document.getElementById('btn-set-bg')?.addEventListener('click', () => {
  const url = prompt('Enter map image URL:');
  if (url) {
    fetch('/api/map/background', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
  }
});

// --- Asset Browser ---
let allAssets = { maps: [], tokens: [], objects: [] };
let currentAssetTab = 'maps';

document.getElementById('btn-assets')?.addEventListener('click', async () => {
  const resp = await fetch('/api/assets');
  allAssets = await resp.json();
  renderAssetGrid('maps');
  document.getElementById('asset-modal').classList.remove('hidden');
});

document.getElementById('asset-close')?.addEventListener('click', () => {
  document.getElementById('asset-modal').classList.add('hidden');
});

document.querySelectorAll('.asset-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.asset-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentAssetTab = tab.dataset.tab;
    renderAssetGrid(currentAssetTab);
  });
});

function renderAssetGrid(tab) {
  const grid = document.getElementById('asset-grid');
  grid.innerHTML = '';
  const items = allAssets[tab] || [];

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'asset-item';
    div.innerHTML = `<img src="${item.url}" alt="${item.name}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23333%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2255%22 text-anchor=%22middle%22 fill=%22%23888%22 font-size=%2212%22>No Preview</text></svg>'"><div class="asset-name">${item.name}</div>`;

    div.addEventListener('click', () => {
      if (tab === 'maps') {
        fetch('/api/map/background', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: item.url }) });
        document.getElementById('asset-modal').classList.add('hidden');
      } else if (tab === 'tokens') {
        // Spawn token with this image
        const name = prompt('Token name:', item.name);
        if (name) {
          fetch('/api/token/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, x: 5, y: 5, image: item.url, color: '#e74c3c' })
          });
        }
        document.getElementById('asset-modal').classList.add('hidden');
      } else if (tab === 'objects') {
        // Place object as a token
        fetch('/api/token/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: item.name, x: 5, y: 5, image: item.url, color: 'transparent', token_type: 'object' })
        });
        document.getElementById('asset-modal').classList.add('hidden');
      }
    });

    grid.appendChild(div);
  });

  if (items.length === 0) {
    grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:#666;padding:20px;">No assets found</div>';
  }
}
