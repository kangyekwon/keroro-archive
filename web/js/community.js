/* === Keroro Archive - Community (Guestbook + Board) === */

var boardPosts = [];
var boardCurrentCat = '';

function initCommunity() {
    setupCommunityTabs();
    loadGuestbook();
    setupGuestbookForm();
    loadBoardPosts();
    setupBoard();
}

/* === Community Tab Switching === */
function setupCommunityTabs() {
    document.querySelectorAll('.community-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.community-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            document.querySelectorAll('.community-section').forEach(function(s) { s.classList.remove('active'); });
            document.getElementById('community-' + tab.dataset.section).classList.add('active');
        });
    });
}

/* ========================================
   GUESTBOOK
   ======================================== */

async function loadGuestbook() {
    var container = document.getElementById('guestbook-entries');
    if (!container) return;
    container.innerHTML = '<div class="loading"><div class="spinner"></div>방명록 로딩 중...</div>';

    try {
        var data = await api('/api/guestbook');
        var entries = data.entries || data.guestbook || data || [];
        renderGuestbook(entries);
    } catch (e) {
        container.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:1rem;">방명록을 불러올 수 없습니다.</p>';
    }
}

function renderGuestbook(entries) {
    var container = document.getElementById('guestbook-entries');
    if (!entries.length) {
        container.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:1rem;">아직 방명록이 없습니다. 첫 번째로 남겨주세요!</p>';
        return;
    }

    var html = '';
    entries.forEach(function(entry) {
        html += '<div class="guestbook-entry">';
        html += '<div class="guestbook-entry-header">';
        html += '<span class="guestbook-entry-name">' + esc(entry.nickname || entry.name || '') + '</span>';
        if (entry.favorite_character || entry.character) {
            html += '<span class="guestbook-entry-char">' + esc(entry.favorite_character || entry.character) + '</span>';
        }
        html += '<span class="guestbook-entry-date">' + formatDate(entry.created_at) + '</span>';
        html += '</div>';
        html += '<div class="guestbook-entry-message">' + esc(entry.message || entry.content || '') + '</div>';
        html += '<button class="guestbook-entry-delete" onclick="deleteGuestbookEntry(' + (entry.id || 0) + ')" title="삭제">x</button>';
        html += '</div>';
    });

    container.innerHTML = html;
}

function setupGuestbookForm() {
    var form = document.getElementById('guestbook-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        var nickname = document.getElementById('guestbook-name').value.trim();
        var character = document.getElementById('guestbook-character').value;
        var message = document.getElementById('guestbook-message').value.trim();

        if (!nickname) { showToast('닉네임을 입력해주세요.', 'error'); return; }
        if (!message) { showToast('메시지를 입력해주세요.', 'error'); return; }

        try {
            var resp = await fetch('/api/guestbook', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nickname: nickname,
                    favorite_character: character,
                    message: message
                })
            });

            if (!resp.ok) throw new Error('Failed to post');

            showToast('방명록이 등록되었습니다!', 'success');
            document.getElementById('guestbook-name').value = '';
            document.getElementById('guestbook-character').value = '';
            document.getElementById('guestbook-message').value = '';
            loadGuestbook();
        } catch (err) {
            showToast('방명록 등록에 실패했습니다.', 'error');
        }
    });
}

async function deleteGuestbookEntry(id) {
    if (!confirm('이 방명록을 삭제하시겠습니까?')) return;

    try {
        var resp = await fetch('/api/guestbook/' + id, { method: 'DELETE' });
        if (!resp.ok) throw new Error('Failed to delete');
        showToast('방명록이 삭제되었습니다.', 'success');
        loadGuestbook();
    } catch (e) {
        // Try alternative endpoint format
        try {
            var resp2 = await fetch('/api/guestbook?id=' + id, { method: 'DELETE' });
            if (!resp2.ok) throw new Error('Failed to delete');
            showToast('방명록이 삭제되었습니다.', 'success');
            loadGuestbook();
        } catch (e2) {
            showToast('삭제에 실패했습니다.', 'error');
        }
    }
}

/* ========================================
   BOARD
   ======================================== */

function setupBoard() {
    // Write button
    var writeBtn = document.getElementById('board-write-btn');
    if (writeBtn) {
        writeBtn.addEventListener('click', showBoardForm);
    }

    // Submit button
    var submitBtn = document.getElementById('board-submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitBoardPost);
    }

    // Cancel button
    var cancelBtn = document.getElementById('board-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', showBoardList);
    }

    // Category tabs
    document.querySelectorAll('#board-category-tabs .board-cat-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('#board-category-tabs .board-cat-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            boardCurrentCat = tab.dataset.cat;
            renderBoardPosts();
        });
    });
}

async function loadBoardPosts() {
    var list = document.getElementById('board-list');
    if (!list) return;
    list.innerHTML = '<div class="loading"><div class="spinner"></div>게시판 로딩 중...</div>';

    try {
        var data = await api('/api/board');
        boardPosts = data.posts || data.board || data || [];
        renderBoardPosts();
    } catch (e) {
        list.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:1rem;">게시판을 불러올 수 없습니다.</p>';
    }
}

function renderBoardPosts() {
    var list = document.getElementById('board-list');

    var filtered = boardPosts;
    if (boardCurrentCat) {
        filtered = boardPosts.filter(function(p) {
            return (p.category || '') === boardCurrentCat;
        });
    }

    if (!filtered.length) {
        list.innerHTML = '<div class="board-empty"><p>아직 작성된 글이 없습니다.</p><p>첫 번째 글을 작성해보세요!</p></div>';
        return;
    }

    var html = '';
    filtered.forEach(function(post) {
        html += '<div class="board-post-item" onclick="showBoardDetail(' + (post.id || 0) + ')">';
        html += '<div class="board-post-title">';
        if (post.category) html += '<span class="board-post-category-badge">' + esc(post.category) + '</span>';
        html += esc(post.title || '') + '</div>';
        html += '<div class="board-post-meta">';
        html += '<span>' + esc(post.author || post.nickname || '') + '</span>';
        html += '<span>' + formatDate(post.created_at) + '</span>';
        html += '</div>';
        var content = post.content || '';
        if (content.length > 100) content = content.substring(0, 100) + '...';
        html += '<div class="board-post-preview">' + esc(content) + '</div>';
        html += '</div>';
    });

    list.innerHTML = html;
}

async function showBoardDetail(id) {
    var post = boardPosts.find(function(p) { return p.id === id; });
    if (!post) {
        showToast('게시글을 찾을 수 없습니다.', 'error');
        return;
    }

    var detail = document.getElementById('board-detail');
    var list = document.getElementById('board-list');
    var form = document.getElementById('board-form');
    var writeBtn = document.getElementById('board-write-btn');
    var catTabs = document.getElementById('board-category-tabs');

    list.style.display = 'none';
    form.style.display = 'none';
    if (writeBtn) writeBtn.style.display = 'none';
    if (catTabs) catTabs.style.display = 'none';
    detail.style.display = 'block';

    var html = '<button class="board-back-btn" onclick="showBoardList()">&#x2190; 목록으로</button>';
    html += '<div class="board-detail-content">';
    html += '<div class="board-detail-title">';
    if (post.category) html += '<span class="board-post-category-badge">' + esc(post.category) + '</span>';
    html += esc(post.title || '') + '</div>';
    html += '<div class="board-detail-meta">';
    html += '<span>' + esc(post.author || post.nickname || '') + '</span>';
    html += '<span>' + formatDate(post.created_at) + '</span>';
    html += '</div>';
    html += '<div class="board-detail-body">' + esc(post.content || '') + '</div>';
    html += '<div class="board-detail-actions">';
    html += '<button class="board-delete-btn" onclick="deleteBoardPost(' + (post.id || 0) + ')">삭제</button>';
    html += '</div>';
    html += '</div>';

    detail.innerHTML = html;
}

function showBoardList() {
    var detail = document.getElementById('board-detail');
    var list = document.getElementById('board-list');
    var form = document.getElementById('board-form');
    var writeBtn = document.getElementById('board-write-btn');
    var catTabs = document.getElementById('board-category-tabs');

    detail.style.display = 'none';
    form.style.display = 'none';
    list.style.display = 'flex';
    if (writeBtn) writeBtn.style.display = 'inline-block';
    if (catTabs) catTabs.style.display = 'flex';

    loadBoardPosts();
}

function showBoardForm() {
    var detail = document.getElementById('board-detail');
    var list = document.getElementById('board-list');
    var form = document.getElementById('board-form');
    var writeBtn = document.getElementById('board-write-btn');
    var catTabs = document.getElementById('board-category-tabs');

    detail.style.display = 'none';
    list.style.display = 'none';
    if (writeBtn) writeBtn.style.display = 'none';
    if (catTabs) catTabs.style.display = 'none';
    form.style.display = 'block';

    // Clear form
    document.getElementById('board-author').value = '';
    document.getElementById('board-title-input').value = '';
    document.getElementById('board-content').value = '';
    document.getElementById('board-category').value = '잡담';
}

async function submitBoardPost() {
    var author = document.getElementById('board-author').value.trim();
    var title = document.getElementById('board-title-input').value.trim();
    var content = document.getElementById('board-content').value.trim();
    var category = document.getElementById('board-category').value;

    if (!author) { showToast('닉네임을 입력해주세요.', 'error'); return; }
    if (!title) { showToast('제목을 입력해주세요.', 'error'); return; }
    if (!content) { showToast('내용을 입력해주세요.', 'error'); return; }

    try {
        var resp = await fetch('/api/board', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                author: author,
                nickname: author,
                title: title,
                content: content,
                category: category
            })
        });

        if (!resp.ok) throw new Error('Failed to post');

        showToast('글이 등록되었습니다!', 'success');
        showBoardList();
    } catch (err) {
        showToast('글 등록에 실패했습니다.', 'error');
    }
}

async function deleteBoardPost(id) {
    if (!confirm('이 게시글을 삭제하시겠습니까?')) return;

    try {
        var resp = await fetch('/api/board/' + id, { method: 'DELETE' });
        if (!resp.ok) throw new Error('Failed to delete');
        showToast('게시글이 삭제되었습니다.', 'success');
        showBoardList();
    } catch (e) {
        try {
            var resp2 = await fetch('/api/board?id=' + id, { method: 'DELETE' });
            if (!resp2.ok) throw new Error('Failed to delete');
            showToast('게시글이 삭제되었습니다.', 'success');
            showBoardList();
        } catch (e2) {
            showToast('삭제에 실패했습니다.', 'error');
        }
    }
}
