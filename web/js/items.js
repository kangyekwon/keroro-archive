/* === Keroro Archive - Items === */

var allItems = [];
var currentCategory = '';

async function initItems() {
    var grid = document.getElementById('items-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>아이템 로딩 중...</div>';

    // Wire up category tabs
    document.querySelectorAll('#category-tabs .category-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('#category-tabs .category-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            currentCategory = tab.dataset.category;
            renderItems();
        });
    });

    // Modal close
    var closeBtn = document.getElementById('item-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('item-modal-overlay').style.display = 'none';
        });
    }
    var overlay = document.getElementById('item-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.style.display = 'none';
        });
    }

    try {
        var data = await api('/api/items');
        allItems = data.items || data || [];
        renderItems();
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">아이템 로드 실패: ' + esc(e.message) + '</p>';
    }
}

var CATEGORY_COLORS = {
    'weapon': { bg: '#cc333322', color: '#cc3333', label: '무기' },
    'gadget': { bg: '#ffd70022', color: '#ffd700', label: '가젯' },
    'vehicle': { bg: '#4fc3f722', color: '#4fc3f7', label: '탈것' },
    'other': { bg: '#a29bfe22', color: '#a29bfe', label: '기타' }
};

function getCategoryStyle(category) {
    var cat = (category || '').toLowerCase();
    return CATEGORY_COLORS[cat] || CATEGORY_COLORS['other'];
}

function renderItems() {
    var grid = document.getElementById('items-grid');

    var filtered = allItems;
    if (currentCategory) {
        filtered = allItems.filter(function(item) {
            return (item.category || '').toLowerCase() === currentCategory;
        });
    }

    if (!filtered.length) {
        grid.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">아이템이 없습니다.</p>';
        return;
    }

    var html = '';
    filtered.forEach(function(item) {
        var catStyle = getCategoryStyle(item.category);

        html += '<div class="item-card" onclick="showItemDetail(' + (item.id || 0) + ')">';
        html += '<span class="item-category-badge" style="background:' + catStyle.bg + ';color:' + catStyle.color + ';">' + esc(catStyle.label) + '</span>';
        html += '<div class="item-name">' + esc(item.name || '') + '</div>';
        if (item.description) html += '<div class="item-desc">' + esc(item.description) + '</div>';
        html += '</div>';
    });

    grid.innerHTML = html;
}

async function showItemDetail(id) {
    // Try to find locally first
    var item = allItems.find(function(i) { return i.id === id; });

    if (!item) {
        showToast('아이템 정보를 찾을 수 없습니다.', 'error');
        return;
    }

    var catStyle = getCategoryStyle(item.category);

    var html = '';
    html += '<h2 style="color:var(--accent-yellow);">' + esc(item.name || '') + '</h2>';

    html += '<div class="detail-badges">';
    html += '<span class="detail-badge" style="background:' + catStyle.bg + ';color:' + catStyle.color + ';border:1px solid ' + catStyle.color + '44;">' + esc(catStyle.label) + '</span>';
    if (item.creator) html += '<span class="detail-badge" style="background:var(--bg-card);color:var(--text-secondary);border:1px solid var(--border);">제작: ' + esc(item.creator) + '</span>';
    html += '</div>';

    if (item.description) {
        html += '<p class="detail-desc">' + esc(item.description) + '</p>';
    }

    if (item.effect) {
        html += '<div class="detail-section">';
        html += '<h3>효과</h3>';
        html += '<p class="detail-desc">' + esc(item.effect) + '</p>';
        html += '</div>';
    }

    if (item.episodes && item.episodes.length) {
        html += '<div class="detail-section">';
        html += '<h3>등장 에피소드</h3>';
        html += '<div class="detail-related-list">';
        item.episodes.forEach(function(ep) {
            html += '<span class="detail-related-chip">' + esc(ep) + '</span>';
        });
        html += '</div></div>';
    }

    var body = document.getElementById('item-modal-body');
    body.innerHTML = html;
    document.getElementById('item-modal-overlay').style.display = 'flex';
}
