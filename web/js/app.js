/* === Keroro Archive - Main App Logic === */

/* === Global Security Functions === */
function esc(text) {
    if (!text) return '';
    var map = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'};
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

function escapeAttr(text) {
    return esc(text).replace(/'/g, "\\'");
}

/* === API Helper === */
async function api(path) {
    var resp = await fetch(path);
    if (!resp.ok) throw new Error('API error: ' + resp.status);
    return resp.json();
}

/* === Toast Notification === */
function showToast(message, type) {
    type = type || 'info';
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    var container = document.getElementById('toast-container');
    if (container) {
        container.appendChild(toast);
        setTimeout(function() { toast.classList.add('show'); }, 10);
        setTimeout(function() {
            toast.classList.remove('show');
            setTimeout(function() { toast.remove(); }, 300);
        }, 3000);
    }
}

/* === Format Date === */
function formatDate(dateString) {
    if (!dateString) return '';
    var date = new Date(dateString);
    var now = new Date();
    var diffMs = now - date;
    var diffMins = Math.floor(diffMs / 60000);
    var diffHours = Math.floor(diffMs / 3600000);
    var diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return diffMins + '분 전';
    if (diffHours < 24) return diffHours + '시간 전';
    if (diffDays < 7) return diffDays + '일 전';

    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

document.addEventListener('DOMContentLoaded', function() {

    var navButtons = document.querySelectorAll('#nav-tabs .nav-tab');
    var pages = document.querySelectorAll('.page');

    var charactersInitialized = false;
    var episodesInitialized = false;
    var quotesInitialized = false;
    var itemsInitialized = false;
    var invasionInitialized = false;
    var abilitiesInitialized = false;
    var ostInitialized = false;
    var voiceActorsInitialized = false;
    var ranksInitialized = false;
    var analyticsInitialized = false;
    var graphInitialized = false;
    var worldInitialized = false;
    var votesInitialized = false;
    var quizInitialized = false;
    var communityInitialized = false;

    /* === Navigation === */
    navButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var target = btn.dataset.page;
            navButtons.forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            pages.forEach(function(p) { p.classList.remove('active'); });
            document.getElementById('page-' + target).classList.add('active');
            document.getElementById('nav-tabs').classList.remove('open');

            // Hash routing
            window.location.hash = '#' + target;

            // Lazy init
            if (target === 'characters' && !charactersInitialized) {
                charactersInitialized = true;
                if (typeof initEncyclopedia === 'function') initEncyclopedia();
            }
            if (target === 'episodes' && !episodesInitialized) {
                episodesInitialized = true;
                if (typeof initEpisodes === 'function') initEpisodes();
            }
            if (target === 'quotes' && !quotesInitialized) {
                quotesInitialized = true;
                if (typeof initQuotes === 'function') initQuotes();
            }
            if (target === 'items' && !itemsInitialized) {
                itemsInitialized = true;
                if (typeof initItems === 'function') initItems();
            }
            if (target === 'invasion-plans' && !invasionInitialized) {
                invasionInitialized = true;
                if (typeof initInvasionPlans === 'function') initInvasionPlans();
            }
            if (target === 'abilities' && !abilitiesInitialized) {
                abilitiesInitialized = true;
                if (typeof initAbilities === 'function') initAbilities();
            }
            if (target === 'ost' && !ostInitialized) {
                ostInitialized = true;
                if (typeof initOST === 'function') initOST();
            }
            if (target === 'voice-actors' && !voiceActorsInitialized) {
                voiceActorsInitialized = true;
                if (typeof initVoiceActors === 'function') initVoiceActors();
            }
            if (target === 'ranks' && !ranksInitialized) {
                ranksInitialized = true;
                if (typeof initRanks === 'function') initRanks();
            }
            if (target === 'analytics' && !analyticsInitialized) {
                analyticsInitialized = true;
                if (typeof initAnalytics === 'function') initAnalytics();
            }
            if (target === 'graph' && !graphInitialized) {
                graphInitialized = true;
                if (typeof initGraph === 'function') initGraph();
            }
            if (target === 'world' && !worldInitialized) {
                worldInitialized = true;
                if (typeof initWorld === 'function') initWorld();
            }
            if (target === 'votes' && !votesInitialized) {
                votesInitialized = true;
                if (typeof initVotes === 'function') initVotes();
            }
            if (target === 'quiz' && !quizInitialized) {
                quizInitialized = true;
                if (typeof initQuiz === 'function') initQuiz();
            }
            if (target === 'community' && !communityInitialized) {
                communityInitialized = true;
                if (typeof initCommunity === 'function') initCommunity();
            }
        });
    });

    /* === Mobile Nav Toggle === */
    var mobileToggle = document.getElementById('nav-mobile-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            document.getElementById('nav-tabs').classList.toggle('open');
        });
    }

    /* === Hash-based routing on load === */
    function handleHash() {
        var hash = window.location.hash.replace('#', '');
        if (hash) {
            var targetBtn = document.querySelector('.nav-tab[data-page="' + hash + '"]');
            if (targetBtn) targetBtn.click();
        }
    }
    handleHash();
    window.addEventListener('hashchange', handleHash);

    /* === Load Stats === */
    async function loadStats() {
        try {
            var stats = await api('/api/stats');
            var e1 = document.getElementById('stat-characters');
            var e2 = document.getElementById('stat-episodes');
            var e3 = document.getElementById('stat-quotes');
            if (e1) e1.textContent = (stats.characters || 0).toLocaleString();
            if (e2) e2.textContent = (stats.episodes || 0).toLocaleString();
            if (e3) e3.textContent = (stats.quotes || 0).toLocaleString();

            var c1 = document.getElementById('stat-card-characters');
            var c2 = document.getElementById('stat-card-episodes');
            var c3 = document.getElementById('stat-card-quotes');
            var c4 = document.getElementById('stat-card-items');
            if (c1) c1.textContent = (stats.characters || 0).toLocaleString();
            if (c2) c2.textContent = (stats.episodes || 0).toLocaleString();
            if (c3) c3.textContent = (stats.quotes || 0).toLocaleString();
            if (c4) c4.textContent = (stats.items || 0).toLocaleString();
        } catch (e) {
            console.log('Stats load failed:', e);
        }
    }

    /* === Load Visitor Count === */
    async function loadVisitor() {
        try {
            // Record visit
            await fetch('/api/visitor', { method: 'POST' });
            var data = await api('/api/visitor');
            var el = document.getElementById('visitor-count');
            if (el) el.textContent = (data.count || 0).toLocaleString();
        } catch (e) {
            console.log('Visitor count failed:', e);
        }
    }

    /* === Hero Particles === */
    function initHeroParticles() {
        var container = document.getElementById('hero-particles');
        if (!container) return;
        var colors = [
            'rgba(74,124,89,0.7)', 'rgba(255,215,0,0.6)',
            'rgba(106,173,122,0.5)', 'rgba(255,255,255,0.4)'
        ];
        for (var i = 0; i < 35; i++) {
            var p = document.createElement('div');
            p.className = 'hero-particle';
            p.style.left = Math.random() * 100 + '%';
            p.style.top = Math.random() * 100 + '%';
            p.style.background = colors[Math.floor(Math.random() * colors.length)];
            p.style.animationDelay = (Math.random() * 6) + 's';
            p.style.animationDuration = (4 + Math.random() * 4) + 's';
            var size = 2 + Math.random() * 4;
            p.style.width = size + 'px';
            p.style.height = size + 'px';
            p.style.boxShadow = '0 0 ' + (size * 3) + 'px ' + p.style.background;
            container.appendChild(p);
        }
    }

    /* === Init === */
    loadStats();
    loadVisitor();
    initHeroParticles();

}); // end DOMContentLoaded
