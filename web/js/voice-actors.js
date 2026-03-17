/* === Keroro Archive - Voice Actors === */

var allVoiceActors = [];

async function initVoiceActors() {
    var grid = document.getElementById('voice-actors-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div>성우 정보 로딩 중...</div>';

    try {
        var data = await api('/api/voice-actors');
        allVoiceActors = data.voice_actors || data || [];
        renderVoiceActors();
        setupVAFilters();
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">성우 정보 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function setupVAFilters() {
    var langFilter = document.getElementById('va-lang-filter');
    if (langFilter) langFilter.addEventListener('change', renderVoiceActors);
}

function renderVoiceActors() {
    var grid = document.getElementById('voice-actors-grid');
    var langFilter = (document.getElementById('va-lang-filter') || {}).value || '';

    // Group by character
    var charMap = {};
    allVoiceActors.forEach(function(va) {
        var charName = va.character_name || '기타';
        if (!charMap[charName]) {
            charMap[charName] = { character_name: charName, character_image_url: va.character_image_url || '', ja: [], ko: [] };
        }
        if (va.language === 'ja') charMap[charName].ja.push(va);
        else if (va.language === 'ko') charMap[charName].ko.push(va);
        else {
            charMap[charName].ja.push(va);
        }
    });

    var characters = Object.keys(charMap).sort(function(a, b) { return a.localeCompare(b, 'ko'); });

    var html = '';
    characters.forEach(function(charName) {
        var info = charMap[charName];
        var showJA = !langFilter || langFilter === 'ja';
        var showKO = !langFilter || langFilter === 'ko';

        if (langFilter === 'ja' && info.ja.length === 0) return;
        if (langFilter === 'ko' && info.ko.length === 0) return;

        html += '<div class="voice-actor-row">';
        html += '<div class="va-character-info">';
        if (info.character_image_url) {
            html += '<img src="' + esc(info.character_image_url) + '" alt="' + esc(charName) + '" class="char-avatar" width="60" height="60">';
        }
        html += '<span class="va-character-name">' + esc(charName) + '</span>';
        html += '</div>';
        html += '<div class="va-actors-columns">';

        if (showJA && info.ja.length > 0) {
            html += '<div class="va-column">';
            html += '<div class="va-column-header"><span class="language-badge language-badge-ja">日</span> 일본어</div>';
            info.ja.forEach(function(va) {
                html += '<div class="va-actor-item">';
                html += '<span class="va-actor-name">' + esc(va.actor_name || '') + '</span>';
                if (va.other_roles) {
                    html += '<div class="va-other-roles">다른 역할: ' + esc(va.other_roles) + '</div>';
                }
                html += '</div>';
            });
            html += '</div>';
        }

        if (showKO && info.ko.length > 0) {
            html += '<div class="va-column">';
            html += '<div class="va-column-header"><span class="language-badge language-badge-ko">韓</span> 한국어</div>';
            info.ko.forEach(function(va) {
                html += '<div class="va-actor-item">';
                html += '<span class="va-actor-name">' + esc(va.actor_name || '') + '</span>';
                if (va.other_roles) {
                    html += '<div class="va-other-roles">다른 역할: ' + esc(va.other_roles) + '</div>';
                }
                html += '</div>';
            });
            html += '</div>';
        }

        html += '</div></div>';
    });

    grid.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">성우 정보가 없습니다.</p>';
}
