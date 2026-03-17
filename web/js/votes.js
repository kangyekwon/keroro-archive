/* === Keroro Archive - Votes === */

var voteCharacters = [];

async function initVotes() {
    var rankingList = document.getElementById('votes-ranking-list');
    rankingList.innerHTML = '<div class="loading"><div class="spinner"></div>투표 랭킹 로딩 중...</div>';
    var charGrid = document.getElementById('votes-character-grid');
    charGrid.innerHTML = '<div class="loading"><div class="spinner"></div>캐릭터 로딩 중...</div>';

    try {
        var results = await Promise.all([
            api('/api/votes/ranking'),
            api('/api/characters')
        ]);
        var ranking = results[0].ranking || results[0] || [];
        voteCharacters = results[1].characters || results[1] || [];

        renderVoteRanking(ranking);
        renderVoteCharacters();
    } catch (e) {
        rankingList.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">투표 데이터 로드 실패: ' + esc(e.message) + '</p>';
        charGrid.innerHTML = '';
    }
}

function renderVoteRanking(ranking) {
    var list = document.getElementById('votes-ranking-list');
    if (!ranking || ranking.length === 0) {
        list.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:1rem;">아직 투표 데이터가 없습니다.</p>';
        return;
    }

    var maxVotes = ranking[0].vote_count || ranking[0].votes || 1;
    var html = '';

    ranking.slice(0, 10).forEach(function(item, idx) {
        var votes = item.vote_count || item.votes || 0;
        var barWidth = Math.max(5, (votes / maxVotes) * 100);
        var rankColors = ['#ffd700', '#c0c0c0', '#cd7f32'];
        var barColor = idx < 3 ? rankColors[idx] : 'var(--accent-light)';

        html += '<div class="vote-ranking-item">';
        html += '<span class="vote-rank-num">' + (idx + 1) + '</span>';
        if (item.image_url) {
            html += '<img src="' + esc(item.image_url) + '" alt="' + esc(item.character_name || '') + '" class="char-avatar vote-rank-avatar" width="40" height="40">';
        }
        html += '<div class="vote-rank-info">';
        html += '<span class="vote-rank-name">' + esc(item.character_name || '') + '</span>';
        html += '<div class="vote-bar"><div class="vote-bar-fill" style="width:' + barWidth + '%;background:' + barColor + ';"></div></div>';
        html += '</div>';
        html += '<span class="vote-rank-count">' + votes + '표</span>';
        html += '</div>';
    });

    list.innerHTML = html;
}

function renderVoteCharacters() {
    var grid = document.getElementById('votes-character-grid');
    var html = '';

    voteCharacters.forEach(function(c) {
        html += '<div class="vote-char-card">';
        if (c.image_url) {
            html += '<img src="' + esc(c.image_url) + '" alt="' + esc(c.name || '') + '" class="char-avatar vote-char-avatar" width="60" height="60">';
        }
        html += '<div class="vote-char-name">' + esc(c.name || '') + '</div>';
        html += '<button class="vote-button" onclick="castVote(' + (c.id || 0) + ', this)">투표하기</button>';
        html += '</div>';
    });

    grid.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">캐릭터 정보가 없습니다.</p>';
}

async function castVote(characterId, btnEl) {
    var nickname = (document.getElementById('vote-nickname') || {}).value || '';
    if (!nickname.trim()) {
        showToast('닉네임을 입력해주세요.', 'error');
        return;
    }

    btnEl.disabled = true;
    btnEl.textContent = '투표 중...';

    try {
        var resp = await fetch('/api/votes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_id: characterId,
                nickname: nickname.trim()
            })
        });

        if (!resp.ok) {
            var errData = await resp.json().catch(function() { return {}; });
            throw new Error(errData.detail || errData.message || 'Vote failed');
        }

        showToast('투표 완료!', 'success');
        btnEl.textContent = '투표 완료';

        // Refresh ranking
        try {
            var rankData = await api('/api/votes/ranking');
            var ranking = rankData.ranking || rankData || [];
            renderVoteRanking(ranking);
        } catch (e) { /* ignore refresh error */ }

        setTimeout(function() {
            btnEl.disabled = false;
            btnEl.textContent = '투표하기';
        }, 3000);
    } catch (e) {
        showToast('투표 실패: ' + e.message, 'error');
        btnEl.disabled = false;
        btnEl.textContent = '투표하기';
    }
}
