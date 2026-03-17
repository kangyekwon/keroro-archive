/* === Keroro Archive - Military Ranks === */

var allRanks = [];

async function initRanks() {
    var pyramid = document.getElementById('ranks-pyramid');
    pyramid.innerHTML = '<div class="loading"><div class="spinner"></div>계급 정보 로딩 중...</div>';

    try {
        var data = await api('/api/ranks');
        allRanks = data.ranks || data || [];
        renderRanks();
    } catch (e) {
        pyramid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">계급 정보 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function renderRanks() {
    var pyramid = document.getElementById('ranks-pyramid');

    // Sort by level (highest first)
    var sorted = allRanks.slice().sort(function(a, b) {
        return (b.level || 0) - (a.level || 0);
    });

    var maxLevel = sorted.length > 0 ? (sorted[0].level || sorted.length) : 1;

    var html = '<div class="ranks-ladder">';

    sorted.forEach(function(rank, idx) {
        var level = rank.level || (sorted.length - idx);
        var widthPercent = 40 + ((sorted.length - idx) / sorted.length) * 55;
        var starCount = Math.max(1, Math.min(5, Math.ceil(level / (maxLevel / 5))));
        var hasHolders = rank.holders && rank.holders.length > 0;

        html += '<div class="rank-card' + (hasHolders ? ' rank-card-notable' : '') + '" style="width:' + widthPercent + '%;">';
        html += '<div class="rank-card-stars">';
        for (var s = 0; s < starCount; s++) {
            html += '<span class="rank-star">&#x2605;</span>';
        }
        html += '</div>';
        html += '<div class="rank-card-info">';
        html += '<div class="rank-card-name">' + esc(rank.name || '') + '</div>';
        if (rank.name_kr && rank.name_kr !== rank.name) {
            html += '<div class="rank-card-name-kr">' + esc(rank.name_kr) + '</div>';
        }
        if (rank.description) {
            html += '<div class="rank-card-desc">' + esc(rank.description) + '</div>';
        }
        html += '</div>';

        if (hasHolders) {
            html += '<div class="rank-card-holders">';
            rank.holders.forEach(function(h) {
                var holderName = h.name || h.character_name || h;
                html += '<span class="rank-holder-chip">';
                if (h.image_url) {
                    html += '<img src="' + esc(h.image_url) + '" alt="' + esc(String(holderName)) + '" class="rank-holder-avatar" width="24" height="24">';
                }
                html += esc(String(holderName));
                html += '</span>';
            });
            html += '</div>';
        }

        html += '</div>';
    });

    html += '</div>';

    pyramid.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">계급 정보가 없습니다.</p>';
}
