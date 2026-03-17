/* === Keroro Archive - Quiz === */

var quizScore = 0;
var quizAnswered = false;

function initQuiz() {
    var startBtn = document.getElementById('quiz-start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', loadQuizQuestion);
    }

    var nextBtn = document.getElementById('quiz-next-btn');
    if (nextBtn) {
        nextBtn.addEventListener('click', loadQuizQuestion);
    }
}

async function loadQuizQuestion() {
    var startScreen = document.getElementById('quiz-start-screen');
    var questionScreen = document.getElementById('quiz-question-screen');
    var questionText = document.getElementById('quiz-question-text');
    var optionsDiv = document.getElementById('quiz-options');
    var resultMsg = document.getElementById('quiz-result-msg');
    var nextBtn = document.getElementById('quiz-next-btn');

    // Show loading state
    startScreen.style.display = 'none';
    questionScreen.style.display = 'block';
    questionText.textContent = '문제를 불러오는 중...';
    optionsDiv.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    resultMsg.style.display = 'none';
    nextBtn.style.display = 'none';
    quizAnswered = false;

    try {
        var data = await api('/api/quiz/random');
        var question = data.question || data;

        questionText.textContent = question.question || question.text || '';

        var options = question.options || question.choices || [];
        var correctIdx = question.correct_index;
        var correctAnswer = question.correct_answer || '';

        var html = '';
        options.forEach(function(opt, idx) {
            html += '<button class="quiz-option" data-idx="' + idx + '" onclick="selectQuizAnswer(' + idx + ', ' + correctIdx + ', \'' + escapeAttr(correctAnswer) + '\')">';
            html += '<span class="quiz-option-marker">' + String.fromCharCode(65 + idx) + '</span>';
            html += '<span class="quiz-option-text">' + esc(opt) + '</span>';
            html += '</button>';
        });

        optionsDiv.innerHTML = html;
    } catch (e) {
        questionText.textContent = '문제를 불러올 수 없습니다.';
        optionsDiv.innerHTML = '<p style="color:var(--danger);">' + esc(e.message) + '</p>';
        nextBtn.style.display = 'inline-block';
        nextBtn.textContent = '다시 시도';
    }
}

function selectQuizAnswer(selectedIdx, correctIdx, correctAnswer) {
    if (quizAnswered) return;
    quizAnswered = true;

    var options = document.querySelectorAll('#quiz-options .quiz-option');
    var resultMsg = document.getElementById('quiz-result-msg');
    var nextBtn = document.getElementById('quiz-next-btn');
    var scoreValue = document.getElementById('quiz-score-value');

    var isCorrect = selectedIdx === correctIdx;

    options.forEach(function(opt, idx) {
        opt.disabled = true;
        opt.classList.add('quiz-option-disabled');
        if (idx === correctIdx) {
            opt.classList.add('quiz-correct');
        }
        if (idx === selectedIdx && !isCorrect) {
            opt.classList.add('quiz-wrong');
        }
    });

    if (isCorrect) {
        quizScore++;
        resultMsg.innerHTML = '<span class="quiz-result-correct">정답입니다!</span>';
        resultMsg.className = 'quiz-result-msg quiz-result-msg-correct';
        // Add shake animation to card
        var card = document.getElementById('quiz-card');
        card.classList.add('quiz-correct-anim');
        setTimeout(function() { card.classList.remove('quiz-correct-anim'); }, 600);
    } else {
        quizScore = 0;
        var answerText = correctAnswer || '';
        resultMsg.innerHTML = '<span class="quiz-result-wrong">오답!</span>';
        resultMsg.className = 'quiz-result-msg quiz-result-msg-wrong';
        // Add shake animation
        var card = document.getElementById('quiz-card');
        card.classList.add('quiz-wrong-anim');
        setTimeout(function() { card.classList.remove('quiz-wrong-anim'); }, 600);
    }

    resultMsg.style.display = 'block';
    nextBtn.style.display = 'inline-block';
    nextBtn.textContent = '다음 문제';
    if (scoreValue) scoreValue.textContent = quizScore;
}
