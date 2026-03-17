/* === Keroro Archive - Abilities === */

var allAbilities = [];

var ABILITY_TYPE_INFO = {
    'attack': { color: '#e74c3c', label: '공격' },
    'defense': { color: '#4fc3f7', label: '방어' },
    'support': { color: '#55efc4', label: '지원' },
    'passive': { color: '#a29bfe', label: '패시브' },
    'special': { color: '#ffd700', label: '스페셜' }
};

async function initAbilities() {
    var grid = document.getElementById('abilities-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>필살기 로딩 중...</div>';

    try {
        var data = await api('/api/abilities');
        allAbilities = data.abilities || data || [];
        populateAbilityCharFilter();
        renderAbilities();
        setupAbilityFilters();
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">필살기 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function populateAbilityCharFilter() {
    var select = document.getElementById('ability-char-filter');
    if (!select) return;
    var chars = [];
    allAbilities.forEach(function(a) {
        var name = a.character_name || '';
        if (name && chars.indexOf(name) === -1) chars.push(name);
    });
    chars.sort(function(a, b) { return a.localeCompare(b, 'ko'); });
    chars.forEach(function(c) {
        var opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        select.appendChild(opt);
    });
}

function setupAbilityFilters() {
    var typeFilter = document.getElementById('ability-type-filter');
    if (typeFilter) typeFilter.addEventListener('change', renderAbilities);

    var charFilter = document.getElementById('ability-char-filter');
    if (charFilter) charFilter.addEventListener('change', renderAbilities);

    // Modal close
    var closeBtn = document.getElementById('ability-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('ability-modal-overlay').style.display = 'none';
        });
    }
    var overlay = document.getElementById('ability-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.style.display = 'none';
        });
    }
}

function renderAbilities() {
    var grid = document.getElementById('abilities-grid');
    var typeFilter = (document.getElementById('ability-type-filter') || {}).value || '';
    var charFilter = (document.getElementById('ability-char-filter') || {}).value || '';

    var filtered = allAbilities.filter(function(a) {
        if (typeFilter && (a.type || '') !== typeFilter) return false;
        if (charFilter && (a.character_name || '') !== charFilter) return false;
        return true;
    });

    var html = '';
    filtered.forEach(function(a, idx) {
        var typeInfo = ABILITY_TYPE_INFO[a.type] || { color: '#888', label: a.type || '' };
        var power = a.power_level || 0;

        html += '<div class="ability-card" onclick="showAbilityDetail(' + idx + ')">';
        html += '<div class="ability-card-header">';
        html += '<span class="ability-card-name">' + esc(a.name_kr || a.name || '') + '</span>';
        html += '<span class="ability-type-badge" style="background:' + typeInfo.color + '22;color:' + typeInfo.color + ';border:1px solid ' + typeInfo.color + '44;">' + esc(typeInfo.label) + '</span>';
        html += '</div>';
        if (a.character_name) {
            html += '<div class="ability-card-char">' + esc(a.character_name) + '</div>';
        }
        // Star rating
        html += '<div class="star-rating">';
        for (var s = 1; s <= 10; s++) {
            html += '<span class="star ' + (s <= power ? 'star-filled' : '') + '">&#x2605;</span>';
        }
        html += '</div>';
        // Power bar
        var barPercent = (power / 10) * 100;
        var barColor = power <= 3 ? '#55efc4' : (power <= 6 ? '#ffd700' : '#e74c3c');
        html += '<div class="power-bar"><div class="power-bar-fill" style="width:' + barPercent + '%;background:' + barColor + ';"></div></div>';
        html += '</div>';
    });

    grid.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">조건에 맞는 필살기가 없습니다.</p>';
}

function showAbilityDetail(idx) {
    var a = allAbilities[idx];
    if (!a) return;

    var typeInfo = ABILITY_TYPE_INFO[a.type] || { color: '#888', label: a.type || '' };
    var power = a.power_level || 0;

    var html = '';
    html += '<h2 style="color:var(--accent-yellow);">' + esc(a.name_kr || a.name || '') + '</h2>';
    if (a.name && a.name_kr && a.name !== a.name_kr) {
        html += '<p style="color:var(--text-secondary);font-size:0.9rem;">' + esc(a.name) + '</p>';
    }
    html += '<div style="margin:0.8rem 0;">';
    html += '<span class="ability-type-badge" style="background:' + typeInfo.color + '22;color:' + typeInfo.color + ';border:1px solid ' + typeInfo.color + '44;font-size:0.9rem;padding:0.3rem 0.8rem;">' + esc(typeInfo.label) + '</span>';
    html += '</div>';
    if (a.character_name) {
        html += '<div style="margin:0.5rem 0;"><strong style="color:var(--accent-light);">캐릭터:</strong> ' + esc(a.character_name) + '</div>';
    }
    html += '<div style="margin:0.5rem 0;"><strong style="color:var(--accent-light);">위력:</strong> ' + power + ' / 10</div>';
    html += '<div class="star-rating" style="margin:0.5rem 0;">';
    for (var s = 1; s <= 10; s++) {
        html += '<span class="star ' + (s <= power ? 'star-filled' : '') + '" style="font-size:1.2rem;">&#x2605;</span>';
    }
    html += '</div>';
    if (a.description) {
        html += '<div class="detail-section"><h3>설명</h3><p class="detail-desc">' + esc(a.description) + '</p></div>';
    }

    document.getElementById('ability-modal-body').innerHTML = html;
    document.getElementById('ability-modal-overlay').style.display = 'flex';
}
