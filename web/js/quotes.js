/* === Keroro Archive - Quotes === */

var allQuotes = [];

async function initQuotes() {
    var grid = document.getElementById('quotes-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>명대사 로딩 중...</div>';

    // Wire up character filter
    var filterSelect = document.getElementById('quotes-character-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            renderQuotes(filterSelect.value);
        });
    }

    // Wire up random button
    var randomBtn = document.getElementById('random-quote-btn');
    if (randomBtn) {
        randomBtn.addEventListener('click', showRandomQuote);
    }

    try {
        var data = await api('/api/quotes');
        allQuotes = data.quotes || data || [];
        populateCharacterFilter();
        renderQuotes('');
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">명대사 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function populateCharacterFilter() {
    var filterSelect = document.getElementById('quotes-character-filter');
    if (!filterSelect) return;

    // Collect unique character names
    var chars = {};
    allQuotes.forEach(function(q) {
        var name = q.character_name || q.character || '';
        if (name && !chars[name]) chars[name] = true;
    });

    var names = Object.keys(chars).sort(function(a, b) {
        return a.localeCompare(b, 'ko');
    });

    names.forEach(function(name) {
        var opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        filterSelect.appendChild(opt);
    });
}

function renderQuotes(characterFilter) {
    var grid = document.getElementById('quotes-grid');

    var filtered = allQuotes;
    if (characterFilter) {
        filtered = allQuotes.filter(function(q) {
            return (q.character_name || q.character || '') === characterFilter;
        });
    }

    if (!filtered.length) {
        grid.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">명대사가 없습니다.</p>';
        return;
    }

    var CHAR_BORDER_COLORS = {
        '케로로': '#4a7c59',
        '기로로': '#cc3333',
        '타마마': '#3366cc',
        '쿠루루': '#ffd700',
        '도로로': '#66bbee',
        '나츠미': '#ff9f43',
        '후유키': '#88aa88',
        '모모카': '#fd79a8'
    };

    var html = '';
    filtered.forEach(function(q) {
        var text = q.text || q.quote || '';
        var charName = q.character_name || q.character || '';
        var episode = q.episode || '';
        var borderColor = CHAR_BORDER_COLORS[charName] || 'var(--accent-yellow)';

        html += '<div class="quote-card" style="border-left-color:' + esc(borderColor) + ';">';
        html += '<div class="quote-text">' + esc(text) + '</div>';
        html += '<div class="quote-source">';
        html += '- ' + esc(charName);
        if (episode) html += ', ' + esc(episode);
        html += '</div>';
        html += '</div>';
    });

    grid.innerHTML = html;
}

function showRandomQuote() {
    if (!allQuotes.length) return;

    var grid = document.getElementById('quotes-grid');
    var randomIndex = Math.floor(Math.random() * allQuotes.length);
    var q = allQuotes[randomIndex];

    var text = q.text || q.quote || '';
    var charName = q.character_name || q.character || '';
    var episode = q.episode || '';

    var CHAR_BORDER_COLORS = {
        '케로로': '#4a7c59',
        '기로로': '#cc3333',
        '타마마': '#3366cc',
        '쿠루루': '#ffd700',
        '도로로': '#66bbee',
        '나츠미': '#ff9f43',
        '후유키': '#88aa88',
        '모모카': '#fd79a8'
    };
    var borderColor = CHAR_BORDER_COLORS[charName] || 'var(--accent-yellow)';

    var html = '<div class="quote-card" style="border-left-color:' + esc(borderColor) + ';border-left-width:6px;transform:scale(1.02);">';
    html += '<div class="quote-text" style="font-size:1.3rem;">' + esc(text) + '</div>';
    html += '<div class="quote-source" style="font-size:0.95rem;">';
    html += '- ' + esc(charName);
    if (episode) html += ', ' + esc(episode);
    html += '</div>';
    html += '</div>';

    // Show random quote at top, then the rest
    html += '<hr style="border:none;border-top:1px solid var(--border);margin:1.5rem 0;">';

    // Reset filter select
    var filterSelect = document.getElementById('quotes-character-filter');
    if (filterSelect) filterSelect.value = '';

    // Show all quotes below
    allQuotes.forEach(function(quote, idx) {
        if (idx === randomIndex) return; // skip the featured one
        var t = quote.text || quote.quote || '';
        var cn = quote.character_name || quote.character || '';
        var ep = quote.episode || '';
        var bc = CHAR_BORDER_COLORS[cn] || 'var(--accent-yellow)';

        html += '<div class="quote-card" style="border-left-color:' + esc(bc) + ';">';
        html += '<div class="quote-text">' + esc(t) + '</div>';
        html += '<div class="quote-source">- ' + esc(cn);
        if (ep) html += ', ' + esc(ep);
        html += '</div></div>';
    });

    grid.innerHTML = html;
}
