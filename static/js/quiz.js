/**
 * quiz.js — Handles all quiz attempt interactions:
 *  - Countdown timer with auto-submit
 *  - Question navigation (prev/next/nav dots)
 *  - Answer selection and state tracking
 *  - AJAX quiz submission to backend
 */

let questions = [];
let sessionId = '';
let timeLimit = 0;
let currentIndex = 0;
let answers = {};       // { question_id: 'A' | 'B' | 'C' | 'D' | null }
let timerInterval = null;
let secondsLeft = 0;
let startTime = null;


function initQuiz(qs, sid, limit) {
  questions = qs;
  sessionId = sid;
  timeLimit = limit;
  secondsLeft = limit;
  startTime = Date.now();

  // Init answers map
  questions.forEach(q => { answers[q.id] = null; });

  renderNavDots();
  renderQuestion(0);
  startTimer();
}


/* ── Timer ───────────────────────────────────────────────── */
function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    secondsLeft--;
    updateTimerDisplay();
    if (secondsLeft <= 0) {
      clearInterval(timerInterval);
      autoSubmit();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const display = document.getElementById('timerDisplay');
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  const pct = secondsLeft / timeLimit;
  display.classList.remove('warning', 'danger');
  if (pct <= 0.1) {
    display.classList.add('danger');
  } else if (pct <= 0.25) {
    display.classList.add('warning');
  }
}

function autoSubmit() {
  submitQuiz(true);
}


/* ── Navigation ──────────────────────────────────────────── */
function renderNavDots() {
  const nav = document.getElementById('questionNav');
  nav.innerHTML = '';
  questions.forEach((q, i) => {
    const btn = document.createElement('button');
    btn.className = 'q-nav-btn' + (i === currentIndex ? ' current' : '') + (answers[q.id] ? ' answered' : '');
    btn.textContent = i + 1;
    btn.onclick = () => goToQuestion(i);
    nav.appendChild(btn);
  });
}

function goToQuestion(index) {
  currentIndex = index;
  renderQuestion(index);
  renderNavDots();
  updateControls();
  updateProgress();
}

function prevQuestion() {
  if (currentIndex > 0) goToQuestion(currentIndex - 1);
}

function nextQuestion() {
  if (currentIndex < questions.length - 1) {
    goToQuestion(currentIndex + 1);
  }
}

function updateControls() {
  const prev = document.getElementById('prevBtn');
  const next = document.getElementById('nextBtn');
  const submit = document.getElementById('submitBtn');

  prev.disabled = currentIndex === 0;

  if (currentIndex === questions.length - 1) {
    next.style.display = 'none';
    submit.style.display = 'inline-flex';
  } else {
    next.style.display = 'inline-flex';
    submit.style.display = 'none';
  }
}

function updateProgress() {
  const answered = Object.values(answers).filter(v => v !== null).length;
  const pct = (answered / questions.length) * 100;
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('progressLabel').textContent = `${currentIndex + 1} / ${questions.length}`;
}


/* ── Rendering ───────────────────────────────────────────── */
function renderQuestion(index) {
  const q = questions[index];
  const area = document.getElementById('questionArea');
  const selected = answers[q.id];

  const opts = [
    { key: 'A', text: q.option_a },
    { key: 'B', text: q.option_b },
    { key: 'C', text: q.option_c },
    { key: 'D', text: q.option_d },
  ];

  area.innerHTML = `
    <div class="q-label">Question ${index + 1} of ${questions.length}</div>
    <div class="q-text">${escapeHtml(q.question_text)}</div>
    <div class="options-grid" id="optionsGrid">
      ${opts.map(o => `
        <button class="option-btn ${selected === o.key ? 'selected' : ''}"
                onclick="selectOption('${q.id}', '${o.key}')"
                data-key="${o.key}">
          <div class="opt-letter">${o.key}</div>
          <div class="opt-text-label">${escapeHtml(o.text)}</div>
        </button>
      `).join('')}
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}


/* ── Answer Selection ────────────────────────────────────── */
function selectOption(questionId, optionKey) {
  answers[questionId] = optionKey;

  // Update UI for this question
  document.querySelectorAll('.option-btn').forEach(btn => {
    btn.classList.remove('selected');
    btn.querySelector('.opt-letter').style.background = '';
    btn.querySelector('.opt-letter').style.color = '';
  });
  const selected = document.querySelector(`.option-btn[data-key="${optionKey}"]`);
  if (selected) selected.classList.add('selected');

  renderNavDots();
  updateProgress();
}


/* ── Submit ──────────────────────────────────────────────── */
function confirmSubmit() {
  const answered = Object.values(answers).filter(v => v !== null).length;
  document.getElementById('answeredCount').textContent = answered;
  document.getElementById('confirmModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('confirmModal').classList.add('hidden');
}

async function submitQuiz(isAutoSubmit = false) {
  clearInterval(timerInterval);
  document.getElementById('confirmModal').classList.add('hidden');

  const timeTaken = Math.round((Date.now() - startTime) / 1000);
  const answersPayload = questions.map(q => ({
    question_id: q.id,
    selected_option: answers[q.id] || null,
  }));

  try {
    const res = await fetch(`/quiz/${sessionId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        answers: answersPayload,
        time_taken_seconds: timeTaken,
      }),
    });
    const data = await res.json();
    if (data.redirect) {
      window.location.href = data.redirect;
    } else if (data.error) {
      alert('Submission error: ' + data.error);
    }
  } catch (err) {
    alert('Network error. Please try again.');
  }
}
