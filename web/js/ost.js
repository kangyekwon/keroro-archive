/* === Keroro Archive - OST / Music === */

var allOST = [];

var OST_TYPE_INFO = {
    'opening': { color: '#e74c3c', label: '오프닝' },
    'ending': { color: '#4fc3f7', label: '엔딩' },
    'insert': { color: '#55efc4', label: '삽입곡' },
    'character': { color: '#ffd700', label: '캐릭터송' }
};

async function initOST() {
    var list = document.getElementById('ost-list');
    list.innerHTML = '<div class="loading"><div class="spinner"></div>OST 로딩 중...</div>';

    try {
        var data = await api('/api/ost');
        allOST = data.ost || data || [];
        renderOST();
        setupOSTFilters();
    } catch (e) {
        list.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">OST 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function setupOSTFilters() {
    var typeFilter = document.getElementById('ost-type-filter');
    if (typeFilter) typeFilter.addEventListener('change', renderOST);

    var seasonFilter = document.getElementById('ost-season-filter');
    if (seasonFilter) seasonFilter.addEventListener('change', renderOST);
}

function renderOST() {
    var list = document.getElementById('ost-list');
    var typeFilter = (document.getElementById('ost-type-filter') || {}).value || '';
    var seasonFilter = (document.getElementById('ost-season-filter') || {}).value || '';

    var filtered = allOST.filter(function(o) {
        if (typeFilter && (o.type || '') !== typeFilter) return false;
        if (seasonFilter && String(o.season || '') !== seasonFilter) return false;
        return true;
    });

    // Group by season
    var grouped = {};
    filtered.forEach(function(o) {
        var key = o.season ? ('시즌 ' + o.season) : '기타';
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(o);
    });

    var html = '';
    var keys = Object.keys(grouped).sort();

    keys.forEach(function(seasonKey) {
        html += '<div class="ost-season-group">';
        html += '<h3 class="ost-season-title">' + esc(seasonKey) + '</h3>';
        grouped[seasonKey].forEach(function(o) {
            var typeInfo = OST_TYPE_INFO[o.type] || { color: '#888', label: o.type || '' };
            html += '<div class="ost-card">';
            html += '<div class="ost-card-icon">&#x1F3B5;</div>';
            html += '<div class="ost-card-body">';
            html += '<div class="ost-card-header">';
            html += '<span class="ost-card-title">' + esc(o.title || '') + '</span>';
            html += '<span class="ost-type-badge" style="background:' + typeInfo.color + '22;color:' + typeInfo.color + ';border:1px solid ' + typeInfo.color + '44;">' + esc(typeInfo.label) + '</span>';
            html += '</div>';
            if (o.artist) {
                html += '<div class="ost-card-artist">' + esc(o.artist) + '</div>';
            }
            var meta = [];
            if (o.episodes) meta.push('에피소드: ' + esc(o.episodes));
            if (o.year) meta.push(esc(String(o.year)) + '년');
            if (meta.length) {
                html += '<div class="ost-card-meta">' + meta.join(' | ') + '</div>';
            }
            html += '</div></div>';
        });
        html += '</div>';
    });

    list.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">조건에 맞는 OST가 없습니다.</p>';
}
