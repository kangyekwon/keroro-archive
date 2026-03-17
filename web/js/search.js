/* === Keroro Archive - Search === */

var searchDebounceTimer = null;

/* === Search Input Handlers === */
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var searchInput = document.getElementById('search-input');
        var searchBtn = document.getElementById('search-btn');

        if (searchInput) {
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') doSearch();
            });

            // Debounced suggest
            searchInput.addEventListener('input', function() {
                clearTimeout(searchDebounceTimer);
                var q = searchInput.value.trim();
                if (q.length < 1) {
                    hideSuggestions();
                    return;
                }
                searchDebounceTimer = setTimeout(function() {
                    loadSuggestions(q);
                }, 300);
            });

            // Hide suggestions on blur (with delay for click)
            searchInput.addEventListener('blur', function() {
                setTimeout(hideSuggestions, 200);
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', doSearch);
        }
    });
})();

function hideSuggestions() {
    var el = document.getElementById('search-suggestions');
    if (el) el.style.display = 'none';
}

async function loadSuggestions(q) {
    try {
        var data = await api('/api/suggest?q=' + encodeURIComponent(q));
        var items = data.suggestions || data.items || [];
        var container = document.getElementById('search-suggestions');
        if (!container || !items.length) {
            hideSuggestions();
            return;
        }

        var html = '';
        items.forEach(function(item) {
            var name = item.name || item.text || item;
            html += '<div class="search-suggestion-item" onclick="selectSuggestion(\'' + escapeAttr(name) + '\')">';
            html += esc(name);
            if (item.category) html += ' <span style="color:var(--text-secondary);font-size:0.8em;">(' + esc(item.category) + ')</span>';
            html += '</div>';
        });
        container.innerHTML = html;
        container.style.display = 'block';
    } catch (e) {
        hideSuggestions();
    }
}

function selectSuggestion(name) {
    var input = document.getElementById('search-input');
    if (input) {
        input.value = name;
        hideSuggestions();
        doSearch();
    }
}

async function doSearch() {
    var q = document.getElementById('search-input').value.trim();
    if (!q) return;

    hideSuggestions();

    var header = document.getElementById('search-results-header');
    var grid = document.getElementById('search-results-grid');
    var container = document.getElementById('search-results-container');
    container.style.display = 'block';
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>검색 중...</div>';
    header.innerHTML = '';

    try {
        var data = await api('/api/search?q=' + encodeURIComponent(q) + '&limit=20');
        var items = data.results || data.items || [];

        if (!items.length) {
            header.innerHTML = '';
            grid.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">검색 결과가 없습니다.</p>';
            return;
        }

        header.innerHTML = '<span>' + esc(items.length) + '개 결과</span>';
        var html = '';
        items.forEach(function(item) {
            var category = item.type || item.category || '';
            var name = item.name || item.title || '';
            var desc = item.description || item.content || '';

            html += '<div class="search-result-card" onclick="handleSearchResultClick(\'' + esc(category) + '\', ' + (item.id || 0) + ', \'' + escapeAttr(name) + '\')">';
            if (category) html += '<div class="src-category">' + esc(category) + '</div>';
            html += '<div class="src-name">' + esc(name) + '</div>';
            if (desc) html += '<div class="src-desc">' + esc(desc.substring(0, 120)) + (desc.length > 120 ? '...' : '') + '</div>';
            html += '</div>';
        });
        grid.innerHTML = html;
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);text-align:center;padding:2rem;">검색 오류: ' + esc(e.message) + '</p>';
    }
}

function handleSearchResultClick(category, id, name) {
    category = (category || '').toLowerCase();
    if (category === 'character' || category === '캐릭터') {
        // Navigate to characters tab and show detail
        var charBtn = document.querySelector('.nav-tab[data-page="characters"]');
        if (charBtn) charBtn.click();
        setTimeout(function() {
            if (typeof showCharacterDetail === 'function') showCharacterDetail(id);
        }, 300);
    } else if (category === 'episode' || category === '에피소드') {
        var epBtn = document.querySelector('.nav-tab[data-page="episodes"]');
        if (epBtn) epBtn.click();
    } else if (category === 'quote' || category === '명대사') {
        var quoteBtn = document.querySelector('.nav-tab[data-page="quotes"]');
        if (quoteBtn) quoteBtn.click();
    } else if (category === 'item' || category === '아이템') {
        var itemBtn = document.querySelector('.nav-tab[data-page="items"]');
        if (itemBtn) itemBtn.click();
    }
}
