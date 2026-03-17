/* === Keroro Archive - Invasion Plans === */

var allInvasionPlans = [];

var RESULT_COLORS = {
    'failure': { bg: 'rgba(231,76,60,0.15)', color: '#e74c3c', label: '실패' },
    'partial': { bg: 'rgba(255,215,0,0.15)', color: '#ffd700', label: '부분 성공' },
    'interrupted': { bg: 'rgba(136,136,136,0.15)', color: '#888', label: '중단' },
    'success': { bg: 'rgba(85,239,196,0.15)', color: '#55efc4', label: '성공' }
};

async function initInvasionPlans() {
    var timeline = document.getElementById('invasion-timeline');
    timeline.innerHTML = '<div class="loading"><div class="spinner"></div>침략 작전 로딩 중...</div>';

    try {
        var data = await api('/api/invasion-plans');
        allInvasionPlans = data.invasion_plans || data || [];
        renderInvasionPlans();
        setupInvasionFilters();
    } catch (e) {
        timeline.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">침략 작전 로드 실패: ' + esc(e.message) + '</p>';
    }
}

function setupInvasionFilters() {
    var filterBtns = document.querySelectorAll('#page-invasion-plans .invasion-filter-bar .category-tab');
    filterBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            filterBtns.forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            renderInvasionPlans();
        });
    });

    // Modal close
    var closeBtn = document.getElementById('invasion-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('invasion-modal-overlay').style.display = 'none';
        });
    }
    var overlay = document.getElementById('invasion-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.style.display = 'none';
        });
    }
}

function renderInvasionPlans() {
    var timeline = document.getElementById('invasion-timeline');
    var activeFilter = document.querySelector('#page-invasion-plans .invasion-filter-bar .category-tab.active');
    var filterResult = activeFilter ? activeFilter.dataset.result : '';

    var filtered = allInvasionPlans.filter(function(p) {
        if (filterResult && (p.result || '') !== filterResult) return false;
        return true;
    });

    // Failure counter
    var failureCount = allInvasionPlans.filter(function(p) { return p.result === 'failure'; }).length;
    var counterEl = document.getElementById('invasion-failure-counter');
    if (counterEl) {
        counterEl.innerHTML = '<div class="failure-counter-box">' +
            '<span class="failure-counter-number">' + failureCount + '</span>' +
            '<span class="failure-counter-label">총 실패 횟수</span>' +
            '<span class="failure-counter-sub">케로로 소대의 영광스러운(?) 기록</span>' +
            '</div>';
    }

    var html = '';
    filtered.forEach(function(plan, idx) {
        var resultInfo = RESULT_COLORS[plan.result] || RESULT_COLORS['failure'];
        html += '<div class="invasion-card" onclick="showInvasionDetail(' + (plan.id || idx) + ')">';
        html += '<div class="invasion-card-marker" style="background:' + resultInfo.color + ';"></div>';
        html += '<div class="invasion-card-body">';
        html += '<div class="invasion-card-header">';
        html += '<span class="invasion-card-name">' + esc(plan.name_kr || plan.name || '') + '</span>';
        html += '<span class="invasion-result-badge" style="background:' + resultInfo.bg + ';color:' + resultInfo.color + ';">' + resultInfo.label + '</span>';
        html += '</div>';
        if (plan.method) {
            html += '<div class="invasion-card-method">' + esc(plan.method) + '</div>';
        }
        if (plan.result_reason) {
            html += '<div class="invasion-card-reason">' + esc(plan.result_reason) + '</div>';
        }
        html += '</div></div>';
    });

    timeline.innerHTML = html || '<p style="color:var(--text-secondary);text-align:center;padding:2rem;">조건에 맞는 작전이 없습니다.</p>';
}

function showInvasionDetail(id) {
    var plan = allInvasionPlans.find(function(p) { return p.id === id; }) || allInvasionPlans[id];
    if (!plan) return;

    var resultInfo = RESULT_COLORS[plan.result] || RESULT_COLORS['failure'];

    var html = '';
    html += '<h2 style="color:var(--accent-yellow);">' + esc(plan.name_kr || plan.name || '') + '</h2>';
    if (plan.name && plan.name_kr && plan.name !== plan.name_kr) {
        html += '<p style="color:var(--text-secondary);font-size:0.9rem;">' + esc(plan.name) + '</p>';
    }
    html += '<div style="margin:1rem 0;">';
    html += '<span class="invasion-result-badge" style="background:' + resultInfo.bg + ';color:' + resultInfo.color + ';font-size:0.9rem;padding:0.3rem 0.8rem;">' + resultInfo.label + '</span>';
    html += '</div>';
    if (plan.episode_number) {
        html += '<div style="margin:0.5rem 0;color:var(--text-secondary);font-size:0.9rem;">에피소드: ' + esc(String(plan.episode_number)) + '</div>';
    }
    if (plan.method) {
        html += '<div class="detail-section"><h3>작전 방법</h3><p class="detail-desc">' + esc(plan.method) + '</p></div>';
    }
    if (plan.description) {
        html += '<div class="detail-section"><h3>상세 설명</h3><p class="detail-desc">' + esc(plan.description) + '</p></div>';
    }
    if (plan.result_reason) {
        html += '<div class="detail-section"><h3>결과 사유</h3><p class="detail-desc">' + esc(plan.result_reason) + '</p></div>';
    }

    document.getElementById('invasion-modal-body').innerHTML = html;
    document.getElementById('invasion-modal-overlay').style.display = 'flex';
}
