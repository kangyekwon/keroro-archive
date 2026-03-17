/* === Keroro Archive - Episodes === */

var allEpisodes = [];
var currentSeason = '';

async function initEpisodes() {
    var list = document.getElementById('episodes-list');
    list.innerHTML = '<div class="loading"><div class="spinner"></div>에피소드 로딩 중...</div>';

    // Wire up season tabs
    document.querySelectorAll('#season-tabs .season-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('#season-tabs .season-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            currentSeason = tab.dataset.season;
            renderEpisodes();
        });
    });

    // Modal close
    var closeBtn = document.getElementById('ep-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('ep-modal-overlay').style.display = 'none';
        });
    }
    var overlay = document.getElementById('ep-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.style.display = 'none';
        });
    }

    try {
        var data = await api('/api/episodes');
        allEpisodes = data.episodes || data || [];
        renderEpisodes();
    } catch (e) {
        list.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">에피소드 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function renderEpisodes() {
    var list = document.getElementById('episodes-list');

    var filtered = allEpisodes;
    if (currentSeason) {
        filtered = allEpisodes.filter(function(ep) {
            return String(ep.season) === currentSeason;
        });
    }

    if (!filtered.length) {
        list.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">에피소드가 없습니다.</p>';
        return;
    }

    var html = '';
    filtered.forEach(function(ep) {
        var epNum = ep.episode_number || ep.number || '';
        var title = ep.title || '';
        var airDate = ep.air_date || '';
        var arc = ep.arc || '';
        var season = ep.season || '';

        html += '<div class="episode-card" onclick="showEpisodeDetail(' + (ep.id || 0) + ')">';
        html += '<div class="episode-number">#' + esc(String(epNum)) + '</div>';
        html += '<div class="episode-info">';
        html += '<div class="episode-title">' + esc(title) + '</div>';
        html += '<div class="episode-meta">';
        if (season) html += '<span>시즌 ' + esc(String(season)) + '</span>';
        if (airDate) html += '<span> | ' + esc(airDate) + '</span>';
        html += '</div>';
        if (arc) html += '<span class="episode-arc">' + esc(arc) + '</span>';
        html += '</div>';
        html += '</div>';
    });

    list.innerHTML = html;
}

async function showEpisodeDetail(id) {
    try {
        var ep = await api('/api/episodes/' + id);

        var html = '';
        html += '<h2 style="color:var(--accent-yellow);">';
        if (ep.episode_number || ep.number) html += '#' + esc(String(ep.episode_number || ep.number)) + ' ';
        html += esc(ep.title || '') + '</h2>';

        html += '<div class="detail-badges">';
        if (ep.season) html += '<span class="detail-badge" style="background:var(--accent-dark);color:var(--accent-light);border:1px solid var(--accent);">시즌 ' + esc(String(ep.season)) + '</span>';
        if (ep.air_date) html += '<span class="detail-badge" style="background:var(--bg-card);color:var(--text-secondary);border:1px solid var(--border);">' + esc(ep.air_date) + '</span>';
        if (ep.arc) html += '<span class="detail-badge" style="background:var(--accent-yellow);color:#000;border:1px solid var(--accent-yellow);">' + esc(ep.arc) + '</span>';
        html += '</div>';

        if (ep.summary || ep.description) {
            html += '<div class="detail-section">';
            html += '<h3>줄거리</h3>';
            html += '<p class="detail-desc">' + esc(ep.summary || ep.description || '') + '</p>';
            html += '</div>';
        }

        // Featured characters
        if (ep.characters && ep.characters.length) {
            html += '<div class="detail-section">';
            html += '<h3>등장 캐릭터</h3>';
            html += '<div class="detail-related-list">';
            ep.characters.forEach(function(ch) {
                var name = ch.name || ch;
                html += '<span class="detail-related-chip">' + esc(name) + '</span>';
            });
            html += '</div></div>';
        }

        var body = document.getElementById('ep-modal-body');
        body.innerHTML = html;
        document.getElementById('ep-modal-overlay').style.display = 'flex';
    } catch (e) {
        console.error('Episode detail error:', e);
        showToast('에피소드 정보를 불러올 수 없습니다.', 'error');
    }
}
