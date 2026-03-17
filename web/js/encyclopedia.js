/* === Keroro Archive - Character Encyclopedia === */

var allCharacters = [];
var encyCurrentPage = 0;
var encyPageSize = 30;

/* === Character Color Map === */
var CHAR_COLORS = {
    '케로로': '#4a7c59',
    '기로로': '#cc3333',
    '타마마': '#3366cc',
    '쿠루루': '#ffd700',
    '도로로': '#66bbee',
    '가루루': '#6633cc',
    '케론인': '#4a7c59',
    '인간': '#ff9f43',
    '기타': '#a29bfe'
};

function getCharColor(character) {
    if (!character) return '#888';
    // Check by name first
    var keys = Object.keys(CHAR_COLORS);
    for (var i = 0; i < keys.length; i++) {
        if ((character.name || '').indexOf(keys[i]) !== -1) return CHAR_COLORS[keys[i]];
    }
    // Then by race
    if (character.race) return CHAR_COLORS[character.race] || '#888';
    return '#888';
}

async function initEncyclopedia() {
    var grid = document.getElementById('ency-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>캐릭터 도감 로딩 중...</div>';

    try {
        var data = await api('/api/characters');
        allCharacters = data.characters || data || [];
        renderEncyclopedia();
        setupEncyFilters();
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">도감 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function setupEncyFilters() {
    var searchInput = document.getElementById('ency-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() { encyCurrentPage = 0; renderEncyclopedia(); });
    }

    var raceFilter = document.getElementById('filter-race');
    if (raceFilter) {
        raceFilter.addEventListener('change', function() { encyCurrentPage = 0; renderEncyclopedia(); });
    }

    var platoonFilter = document.getElementById('filter-platoon');
    if (platoonFilter) {
        platoonFilter.addEventListener('change', function() { encyCurrentPage = 0; renderEncyclopedia(); });
    }

    // Modal close
    var closeBtn = document.getElementById('char-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeCharModal);
    }
    var overlay = document.getElementById('char-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closeCharModal();
        });
    }
}

function renderEncyclopedia() {
    var grid = document.getElementById('ency-grid');
    var searchTerm = (document.getElementById('ency-search') || {}).value || '';
    searchTerm = searchTerm.toLowerCase();
    var raceFilter = (document.getElementById('filter-race') || {}).value || '';
    var platoonFilter = (document.getElementById('filter-platoon') || {}).value || '';

    var filtered = allCharacters.filter(function(c) {
        if (raceFilter && (c.race || '') !== raceFilter) return false;
        if (platoonFilter && (c.platoon || '') !== platoonFilter) return false;
        if (searchTerm) {
            var match = (c.name || '').toLowerCase().indexOf(searchTerm) !== -1
                || (c.name_ja || '').toLowerCase().indexOf(searchTerm) !== -1
                || (c.description || '').toLowerCase().indexOf(searchTerm) !== -1;
            if (!match) return false;
        }
        return true;
    });

    // Sort alphabetically
    filtered.sort(function(a, b) { return (a.name || '').localeCompare(b.name || '', 'ko'); });

    var countEl = document.getElementById('ency-count');
    if (countEl) countEl.textContent = filtered.length + ' / ' + allCharacters.length + ' 명';

    var total = filtered.length;
    var start = encyCurrentPage * encyPageSize;
    var pageItems = filtered.slice(start, start + encyPageSize);

    var html = '';
    pageItems.forEach(function(c) {
        var color = getCharColor(c);
        html += '<div class="ency-card" onclick="showCharacterDetail(' + (c.id || 0) + ')">';
        html += '<div class="ency-card-color-bar" style="background:' + esc(color) + ';"></div>';
        html += '<div class="ency-card-body">';
        if (c.image_url) {
            html += '<img src="' + esc(c.image_url) + '" alt="' + esc(c.name || '') + '" class="char-avatar" width="80" height="80">';
        }
        html += '<div class="ency-card-name">' + esc(c.name || '') + '</div>';
        if (c.race) {
            var raceBg = color + '22';
            html += '<span class="ency-card-race" style="background:' + raceBg + ';color:' + esc(color) + ';">' + esc(c.race) + '</span>';
        }
        if (c.platoon) html += '<div class="ency-card-platoon">' + esc(c.platoon) + '</div>';
        if (c.description) html += '<div class="ency-card-desc">' + esc(c.description.substring(0, 80)) + (c.description.length > 80 ? '...' : '') + '</div>';
        html += '</div></div>';
    });

    grid.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">조건에 맞는 캐릭터가 없습니다.</p>';

    // Pagination (simple)
    if (total > encyPageSize) {
        var totalPages = Math.ceil(total / encyPageSize);
        var pagHtml = '<div style="display:flex;justify-content:center;gap:0.3rem;padding:1.5rem 0;">';
        for (var p = 0; p < totalPages; p++) {
            var activeClass = p === encyCurrentPage ? 'background:var(--accent-dark);color:var(--accent-yellow);' : '';
            pagHtml += '<button style="padding:0.4rem 0.7rem;border:1px solid var(--border);border-radius:var(--radius-btn);background:var(--bg-card);color:var(--text-secondary);font-family:var(--font-family);cursor:pointer;' + activeClass + '" onclick="goEncyPage(' + p + ')">' + (p + 1) + '</button>';
        }
        pagHtml += '</div>';
        grid.insertAdjacentHTML('afterend', pagHtml);
    }
}

function goEncyPage(page) {
    encyCurrentPage = page;
    // Remove old pagination
    var grid = document.getElementById('ency-grid');
    var nextSib = grid.nextElementSibling;
    if (nextSib && nextSib.tagName !== 'DIV') { /* skip */ }
    else if (nextSib && !nextSib.classList.contains('modal-overlay')) nextSib.remove();
    renderEncyclopedia();
    document.getElementById('page-characters').scrollTo({ top: 0, behavior: 'smooth' });
}

async function showCharacterDetail(id) {
    try {
        var c = await api('/api/characters/' + id);
        var color = getCharColor(c);
        var relations = c.relations || [];
        var quotes = c.quotes || [];

        var html = '';
        if (c.image_url) {
            html += '<div style="text-align:center;margin-bottom:1rem;"><img src="' + esc(c.image_url) + '" alt="' + esc(c.name || '') + '" class="char-avatar-large" width="120" height="120"></div>';
        }
        html += '<h2 style="border-left:4px solid ' + esc(color) + ';padding-left:0.8rem;">' + esc(c.name || '');
        if (c.name_ja) html += ' <span style="color:var(--text-secondary);font-weight:400;font-size:0.9em;">(' + esc(c.name_ja) + ')</span>';
        html += '</h2>';

        // Badges
        html += '<div class="detail-badges">';
        if (c.race) html += '<span class="detail-badge" style="background:' + esc(color) + '22;color:' + esc(color) + ';border:1px solid ' + esc(color) + '44;">' + esc(c.race) + '</span>';
        if (c.platoon) html += '<span class="detail-badge" style="background:var(--accent-blue);color:#fff;border:1px solid var(--accent-blue);">' + esc(c.platoon) + '</span>';
        if (c.rank) html += '<span class="detail-badge" style="background:var(--accent-yellow);color:#000;border:1px solid var(--accent-yellow);">' + esc(c.rank) + '</span>';
        html += '</div>';

        // Ability
        if (c.ability) {
            html += '<div style="margin:0.5rem 0;"><strong style="color:var(--accent-yellow);">특기:</strong> ' + esc(c.ability) + '</div>';
        }

        // Description
        if (c.description) {
            html += '<p class="detail-desc">' + esc(c.description) + '</p>';
        }

        // Relations
        if (relations.length) {
            html += '<div class="detail-section">';
            html += '<h3>관계</h3>';
            html += '<div class="detail-related-list">';
            relations.forEach(function(r) {
                var relType = r.relation_type || r.type || '';
                var relName = r.target_name || r.name || '';
                var relId = r.target_id || r.id || 0;
                html += '<span class="detail-related-chip" onclick="showCharacterDetail(' + relId + ')">';
                html += esc(relName);
                if (relType) html += ' <span style="color:var(--text-secondary);font-size:0.8em;">(' + esc(relType) + ')</span>';
                html += '</span>';
            });
            html += '</div></div>';
        }

        // Quotes
        if (quotes.length) {
            html += '<div class="detail-section">';
            html += '<h3>명대사</h3>';
            quotes.forEach(function(q) {
                html += '<div class="detail-quote">' + esc(q.text || q.quote || '') + '</div>';
            });
            html += '</div>';
        }

        var body = document.getElementById('char-modal-body');
        body.innerHTML = html;
        document.getElementById('char-modal-overlay').style.display = 'flex';
    } catch (e) {
        console.error('Character detail error:', e);
        showToast('캐릭터 정보를 불러올 수 없습니다.', 'error');
    }
}

function closeCharModal() {
    document.getElementById('char-modal-overlay').style.display = 'none';
}
